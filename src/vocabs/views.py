from http import HTTPStatus
from os.path import basename
from typing import Any

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import CreateView, DetailView, ListView, UpdateView, TemplateView
from plastron.namespaces import namespace_manager, rdf
from rdflib.util import from_n3

from vocabs.forms import PropertyForm, NewVocabularyForm, VocabularyForm
from vocabs.models import Predicate, Property, Term, Vocabulary, VOCAB_FORMAT_LABELS


class PrefixList(TemplateView):
    template_name = 'vocabs/prefix_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prefixes = {prefix: uri for prefix, uri in namespace_manager.namespaces()}
        context.update({'prefixes': dict(sorted(prefixes.items()))})
        return context


class IndexView(ListView):
    model = Vocabulary
    context_object_name = 'vocabularies'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({
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


class VocabularyView(UpdateView):
    model = Vocabulary
    fields = ['uri', 'label', 'description', 'preferred_prefix']
    context_object_name = 'vocabulary'
    template_name_suffix = '_detail'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({
            'predicates': Predicate.objects.all,
            'form': VocabularyForm(instance=self.get_object()),
            'formats': VOCAB_FORMAT_LABELS,
        })
        return context

    def get_success_url(self):
        return reverse('show_vocabulary', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        for key, value in form.cleaned_data.items():
            setattr(self.object, key, value)
        return super().form_valid(form)


class TermsView(View):
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


class GraphView(DetailView):
    model = Vocabulary

    def requested_content_type(self, default: str = 'json-ld') -> tuple[str, str]:
        format_param = self.request.GET.get('format', default)
        match format_param:
            case 'json-ld' | 'jsonld' | 'json':
                return 'application/ld+json', 'utf-8'
            case 'rdfxml' | 'rdf/xml' | 'rdf' | 'xml':
                return 'application/rdf+xml', 'utf-8'
            case 'ttl' | 'turtle':
                return 'text/turtle', 'utf-8'
            case 'nt' | 'ntriples' | 'n-triples':
                return 'application/n-triples', 'us-ascii'
            case _:
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


class TermView(DetailView):
    model = Term
    context_object_name = 'term'

    @method_decorator(ensure_csrf_cookie)
    def delete(self, *_args, **_kwargs):
        self.get_object().delete()
        return HttpResponse(status=HTTPStatus.OK)


class PropertyView(DetailView):
    model = Property
    context_object_name = 'property'

    @method_decorator(ensure_csrf_cookie)
    def delete(self, *_args, **_kwargs):
        self.get_object().delete()
        return HttpResponse(status=HTTPStatus.OK)


class NewPropertyView(CreateView):
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


class PropertyEditView(UpdateView):
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


class PredicatesView(ListView):
    model = Predicate

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
