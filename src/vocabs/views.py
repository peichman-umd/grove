import logging
from http import HTTPStatus
from os.path import basename
from typing import Any, Counter

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import pluralize
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import CreateView, DetailView, ListView, UpdateView, TemplateView, FormView
from plastron.namespaces import namespace_manager, rdf
from rdflib.util import from_n3

from vocabs.forms import PropertyForm, NewVocabularyForm, VocabularyForm, ImportForm
from vocabs.models import Predicate, Property, Term, Vocabulary, VOCAB_FORMAT_LABELS, import_vocabulary

logger = logging.getLogger(__name__)


class RootView(TemplateView):
    template_name = 'vocabs/login_required.html'

    def get(self, request, *args, **kwargs):
        """If the user is already logged in, send them to the vocab list page.
        Otherwise, display the "Login Required" page."""

        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('list_vocabularies'))
        else:
            return super().get(request, *args, **kwargs)


class PrefixList(LoginRequiredMixin, TemplateView):
    template_name = 'vocabs/prefix_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prefixes = {prefix: uri for prefix, uri in namespace_manager.namespaces()}
        context.update({
            'title': 'Prefixes',
            'prefixes': dict(sorted(prefixes.items())),
        })
        return context


class IndexView(LoginRequiredMixin, ListView):
    model = Vocabulary
    context_object_name = 'vocabularies'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Vocabularies',
            'vocab_form': NewVocabularyForm(),
            'formats': VOCAB_FORMAT_LABELS,
        })
        return context

    def post(self, _request, *_args, **_kwargs):
        uri = self.request.POST.get('uri', '').strip()
        if uri != '':
            label = basename(uri.rstrip('#/')).title()
            vocab, is_new = Vocabulary.objects.get_or_create(uri=uri, label=label)
            return HttpResponseRedirect(reverse('show_vocabulary', args=(vocab.id,)))

        return HttpResponseRedirect(reverse('list_vocabularies'))


class VocabularyView(LoginRequiredMixin, UpdateView):
    model = Vocabulary
    form_class = VocabularyForm
    context_object_name = 'vocabulary'
    template_name_suffix = '_detail'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'Vocabulary: {self.object.label}',
            'predicates': Predicate.objects.all,
            'formats': VOCAB_FORMAT_LABELS,
            'terms': self.object.terms.all().order_by('name'),
        })
        return context

    def get_success_url(self):
        return reverse('show_vocabulary', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        messages.success(self.request, message='Vocabulary updated')
        for key, value in form.cleaned_data.items():
            setattr(self.object, key, value)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, message='Vocabulary cannot be updated due to validation errors')
        return super().form_invalid(form)

    @method_decorator(ensure_csrf_cookie)
    def delete(self, *_args, **_kwargs):
        self.get_object().delete()
        return HttpResponse(status=HTTPStatus.OK)


class TermsView(LoginRequiredMixin, View):
    model = Vocabulary
    context_object_name = 'vocabulary'

    def post(self, request, pk, *_args, **_kwargs):
        """Create a new term."""
        vocabulary = get_object_or_404(self.model, id=pk)
        name = request.POST.get('term_name', '').strip()
        rdf_type = request.POST.get('rdf_type', '').strip()
        if name != '':
            term, is_new = Term.objects.get_or_create(
                vocabulary=vocabulary,
                name=name,
            )
            if rdf_type != '':
                predicate, _ = Predicate.objects.get_or_create(
                    uri=str(rdf.type),
                    object_type=Predicate.ObjectType.URI_REF,
                )
                Property.objects.get_or_create(
                    term=term,
                    predicate=predicate,
                    value=from_n3(rdf_type),
                )

            if self.request.headers.get('HX-Request', 'false') == 'true':
                return render(self.request, 'vocabs/term.html', {'term': term, 'predicates': Predicate.objects.all})

        return HttpResponseRedirect(reverse('show_vocabulary', args=(pk,)))


class GraphView(LoginRequiredMixin, DetailView):
    model = Vocabulary

    def requested_content_type(self, default: str = 'json-ld') -> tuple[str, str]:
        format_param = self.request.GET.get('format', default)
        for fmt in Vocabulary.OUTPUT_FORMATS:
            if format_param in fmt.parameter_names:
                return fmt.media_type, 'utf-8'

        raise ValueError(f'Unknown format: {format_param}')

    def get(self, request, *args, **kwargs):
        graph, context = self.get_object().graph()
        try:
            media_type, charset = self.requested_content_type()
        except ValueError as e:
            return HttpResponse(str(e), status=HTTPStatus.NOT_ACCEPTABLE)

        return HttpResponse(
            graph.serialize(format=media_type, context=context),
            headers={'Content-Type': f'{media_type}; charset={charset}'},
        )


class TermView(LoginRequiredMixin, DetailView):
    model = Term
    context_object_name = 'term'

    @method_decorator(ensure_csrf_cookie)
    def delete(self, *_args, **_kwargs):
        self.get_object().delete()
        return HttpResponse(status=HTTPStatus.OK)


class PropertyView(LoginRequiredMixin, DetailView):
    model = Property
    context_object_name = 'property'

    @method_decorator(ensure_csrf_cookie)
    def delete(self, *_args, **_kwargs):
        self.get_object().delete()
        return HttpResponse(status=HTTPStatus.OK)


class NewPropertyView(LoginRequiredMixin, CreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'vocabs/new_property.html'

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()
        if self.request.method == 'GET':
            curie = self.request.GET['predicate']
            term = Term.objects.get(id=self.request.GET['term_id'])
            initial.update({
                'term': term,
                'predicate': Predicate.from_curie(curie)
            })
        return initial

    def get_success_url(self) -> str:
        return reverse('show_property', args=(self.object.id,))


class PropertyEditView(LoginRequiredMixin, UpdateView):
    model = Property
    form_class = PropertyForm

    def get_initial(self):
        return {
            'term': self.object.term,
            'predicate': self.object.predicate,
            'value': self.object.value_for_editing,
        }

    def get_success_url(self) -> str:
        return reverse('show_property', args=(self.object.id,))


class PredicatesView(LoginRequiredMixin, ListView):
    model = Predicate

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context.update({'title': 'Predicates'})
        return context

    # create new Predicate
    def post(self, _request, *_args, **_kwargs):
        uri = self.request.POST.get('new_predicate', '').strip()
        if uri != '':
            if not uri.startswith('http:') or uri.startswith('https:'):
                uri = from_n3(uri, nsm=namespace_manager)
            Predicate.objects.get_or_create(
                uri=uri,
                object_type=self.request.POST.get('object_type', '')
            )

        return HttpResponseRedirect(reverse('list_predicates'))


def quantity(count: Counter, term: str) -> str:
    if '|' not in term:
        base = term
        suffixes = 's'
    else:
        base, suffixes = term.split('|', 1)
    # counter keys are in the plural form
    key = base.replace(' ', '_') + pluralize(2, suffixes)
    number = count[key]
    return f'{number} {base}{pluralize(number, suffixes)}'


class ImportFormView(LoginRequiredMixin, FormView):
    form_class = ImportForm
    template_name = 'vocabs/import_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'title': 'Import Vocabulary'})
        return context

    def form_valid(self, form):
        try:
            vocab, is_new, count = import_vocabulary(
                file=form.files['file'],
                rdf_format=form.cleaned_data['rdf_format'],
                uri=form.cleaned_data['uri'],
            )
        except ValueError:
            messages.error(self.request, message='Unable to import vocabulary')
            return super().form_invalid(form)

        if is_new or count['new_terms'] > 0 or count['new_properties'] > 0:
            messages.success(
                self.request, message=f'Import successful: Vocabulary {"created" if is_new else "updated"}'
            )
            if count['new_terms'] > 0:
                messages.info(self.request, message=f'Created {quantity(count, "new term")}.')
            if count['new_properties'] > 0:
                messages.info(self.request, message=f'Created {quantity(count, "new propert|y,ies")}.')
        else:
            messages.info(self.request, message='No changes to vocabulary')

        return HttpResponseRedirect(reverse('show_vocabulary', kwargs={'pk': vocab.id}))

    def form_invalid(self, form):
        messages.error(self.request, message='Unable to import vocabulary')
        return super().form_invalid(form)


class PublishedVocabularyView(LoginRequiredMixin, DetailView):
    model = Vocabulary

    def get(self, request, *args, **kwargs):
        vocab: Vocabulary = self.get_object()
        if vocab.is_published:
            return JsonResponse({'published': vocab.is_published, 'date': vocab.publication_date.isoformat()})
        else:
            return JsonResponse({'published': vocab.is_published})

    def post(self, _request, *_args, **_kwargs):
        publish = self.request.POST['publish'] == 'true'
        if publish:
            self.get_object().publish()
        else:
            self.get_object().unpublish()

        return HttpResponseRedirect(reverse('show_vocabulary', kwargs={'pk': self.get_object().id}))
