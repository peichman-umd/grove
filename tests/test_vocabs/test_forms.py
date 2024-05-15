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


@pytest.fixture
def vocab():
    vocab, _ = Vocabulary.objects.get_or_create(uri='http://example.com/foo#')
    return vocab


@pytest.fixture
def rdf_type_predicate():
    predicate, _ = Predicate.objects.get_or_create(uri=rdf.type, object_type=Predicate.ObjectType.URI_REF)
    return predicate


@pytest.fixture
def rdfs_label_predicate():
    predicate, _ = Predicate.objects.get_or_create(uri=rdfs.label, object_type=Predicate.ObjectType.LITERAL)
    return predicate


@pytest.fixture
def term(vocab):
    term, _ = Term.objects.get_or_create(name='bar', vocabulary=vocab)
    return term


@pytest.mark.django_db
def test_property_form(vocab, rdf_type_predicate, term):
    form = PropertyForm({'term': term, 'predicate': rdf_type_predicate, 'value': 'rdfs:Class'})
    form.full_clean()
    assert form.cleaned_data['value'] == str(rdfs.Class)
    form = PropertyForm({'term': term, 'predicate': rdf_type_predicate, 'value': str(rdfs.Class)})
    form.full_clean()
    assert form.cleaned_data['value'] == str(rdfs.Class)
    _invalid_uri_chars = '<>" {}|\\^`'


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('value', 'expected_validity'),
    [
        ('', False),
        ('string with space', False),
        ('<angle_bracketed>', False),
        ('pipe|string', False),
        ('{curly_brackets}', False),
        ('\\escaped\\', False),
        ('caret^string', False),
        ('`backtick_string`', False),
        ('rdfs:Class', True),
        ('http://example.com/doc.html?q=foo#section', True),
        ('urn:uuid:b2bce418-eb2f-4aa8-9678-b89438814449', True),
        ('mailto:jdoe@example.com', True),
    ]
)
def test_property_form_uriref_validation(vocab, rdf_type_predicate, term, value, expected_validity):
    form = PropertyForm({'term': term, 'predicate': rdf_type_predicate, 'value': value})
    assert form.is_valid() == expected_validity
