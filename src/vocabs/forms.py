from django.core.exceptions import ValidationError
from django.forms import CharField, Form, HiddenInput, ModelForm, TextInput, Textarea, FileField, ChoiceField
from plastron.namespaces import namespace_manager
from rdflib.util import from_n3

from vocabs.models import Predicate, Property, Vocabulary, VocabularyURIValidator, VOCAB_FORMAT_LABELS, Term


class NewVocabularyForm(Form):
    uri = CharField(
        widget=TextInput(attrs={'size': 40, 'placeholder': 'URI'}),
        validators=[VocabularyURIValidator()],
    )


class VocabularyForm(ModelForm):
    template_name = 'vocabs/dl_form.html'

    class Meta:
        model = Vocabulary
        fields = ['uri', 'label', 'description', 'preferred_prefix']
        labels = {
            'uri': 'URI',
        }
        widgets = {
            'uri': TextInput(attrs={'size': 40}),
            'label': TextInput(attrs={'size': 40}),
            'description': Textarea(attrs={'rows': 4, 'cols': 45}),
            'preferred_prefix': TextInput(attrs={'size': 20}),
        }
        validators = {
            'uri': [VocabularyURIValidator()],
        }


# copied from rdflib.term._is_valid_uri, since that function is not
# part of the public interface to rdflib, and may be subject to changes
def _is_valid_uri(uri: str) -> bool:
    # _invalid_uri_chars = '<>" {}|\\^`'
    for c in '<>" {}|\\^`':
        if c in uri:
            return False
    return True


class TermForm(ModelForm):
    class Meta:
        model = Term
        fields = ['vocabulary', 'name']
        widgets = {
            'vocabulary': HiddenInput(),
            'name': TextInput(attrs={'placeholder': 'Name'})
        }

    rdf_type = ChoiceField(
        choices={'': 'Basic term', 'rdfs:Class': 'Class', 'rdfs:Datatype': 'Datatype'},
        # must set required=False to allow the choice of "" for the Basic term option
        required=False,
    )


class PropertyForm(ModelForm):
    class Meta:
        model = Property
        fields = ['term', 'predicate', 'value']
        widgets = {
            'term': HiddenInput(),
            'value': TextInput(attrs={'autofocus': True, 'size': 40}),
        }

    def clean_value(self):
        """If the predicate takes URIRef values, and the value comes in as a CURIE,
        use the namespace manager to expand it to a full URI."""

        predicate = self.cleaned_data['predicate']
        value = self.cleaned_data['value']
        if predicate.object_type == Predicate.ObjectType.URI_REF:
            # ensure only valid URI characters in the value
            if not _is_valid_uri(value):
                raise ValidationError(f'{predicate} expects a URI or CURIE')
            try:
                return str(from_n3(value, nsm=namespace_manager))
            except KeyError:
                # something looked like a CURIE, but we don't have a namespace for it
                # (e.g., "http://example.com" or "urn:foo" or "mailto:jdoe@example.org"),
                # so just return the full value
                return value

        return value


class ImportForm(Form):
    uri = CharField(
        label='URI',
        widget=TextInput(attrs={'size': 40}),
        validators=[VocabularyURIValidator()],
    )
    file = FileField()
    rdf_format = ChoiceField(choices=VOCAB_FORMAT_LABELS, label='RDF Format')
    template_name = 'vocabs/dl_form.html'
