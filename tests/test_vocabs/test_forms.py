import pytest
from plastron.namespaces import rdf, rdfs

from vocabs.forms import VocabularyForm, PropertyForm
from vocabs.models import Vocabulary, Term, Predicate


@pytest.mark.parametrize(
    ('data', 'expected_validity'),
    [
        ({}, False),
        ({'uri': 'http://example.com/foo#'}, False),
        ({'label': 'Foo'}, False),
        # uri and label are both required
        ({'uri': 'http://example.com/foo#', 'label': 'Foo'}, True),
    ]
)
def test_vocabulary_form(data, expected_validity):
    form = VocabularyForm(data)
    assert form.is_valid() is expected_validity


@pytest.mark.django_db
def test_property_form():
    vocab = Vocabulary(uri='http://example.com/foo#')
    vocab.save()
    predicate, _ = Predicate.objects.get_or_create(uri=rdf.type, object_type=Predicate.ObjectType.URI_REF)
    term = Term(name='bar', vocabulary=vocab)
    term.save()
    form = PropertyForm({'term': term, 'predicate': predicate, 'value': 'rdfs:Class'})
    form.full_clean()
    assert form.cleaned_data['value'] == str(rdfs.Class)
    form = PropertyForm({'term': term, 'predicate': predicate, 'value': str(rdfs.Class)})
    form.full_clean()
    assert form.cleaned_data['value'] == str(rdfs.Class)
