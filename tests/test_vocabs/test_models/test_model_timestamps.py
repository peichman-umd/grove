import datetime
from freezegun import freeze_time
import pytest
from plastron.namespaces import rdfs

from vocabs.models import Vocabulary, Term, Predicate, Property

created_timestamp = '2024-04-20T12:34:56Z'
modified_timestamp = '2024-05-01T23:00:00Z'
deleted_timestamp = '2024-06-15T16:24:52Z'


@pytest.fixture
@freeze_time(created_timestamp)
def vocab():
    vocab = Vocabulary(uri='http://example.com/foo#')
    vocab.save()
    return vocab


@pytest.fixture
@freeze_time(created_timestamp)
def term(vocab):
    term = Term(name='bar', vocabulary=vocab)
    term.save()
    return term


@pytest.fixture
def predicate():
    predicate, _ = Predicate.objects.get_or_create(uri=rdfs.label, object_type=Predicate.ObjectType.LITERAL)
    return predicate


@pytest.fixture
@freeze_time(created_timestamp)
def prop(term, predicate):
    prop = Property(term=term, predicate=predicate, value='Bar')
    prop.save()
    return prop


@pytest.mark.django_db
def test_vocabulary_initial_timestamps(vocab):
    assert vocab.created == datetime.datetime.fromisoformat(created_timestamp)
    assert vocab.modified == datetime.datetime.fromisoformat(created_timestamp)


@pytest.mark.django_db
def test_vocabalary_modified_timestamp_changed_when_vocabulary_is_changed(vocab):
    with freeze_time(modified_timestamp):
        vocab.description = "Test description"
        vocab.save()

        assert vocab.created == datetime.datetime.fromisoformat(created_timestamp)
        assert vocab.modified == datetime.datetime.fromisoformat(modified_timestamp)


@pytest.mark.django_db
def test_term_initial_timestamps(term):
    assert term.created == datetime.datetime.fromisoformat(created_timestamp)
    assert term.modified == datetime.datetime.fromisoformat(created_timestamp)
    assert term.deleted is None


@pytest.mark.django_db
def test_term_modified_timestamp_changed_when_term_is_changed(term):
    with freeze_time(modified_timestamp):
        term.description = "Test description"
        term.save()

        assert term.created == datetime.datetime.fromisoformat(created_timestamp)
        assert term.modified == datetime.datetime.fromisoformat(modified_timestamp)
        assert term.deleted is None


@pytest.mark.django_db
def test_term_deleted_timestamp_set_when_term_is_deleted(term):
    with freeze_time(deleted_timestamp):
        term.delete()
        assert term.modified == datetime.datetime.fromisoformat(deleted_timestamp)
        assert term.deleted == datetime.datetime.fromisoformat(deleted_timestamp)


@pytest.mark.django_db
def test_property_initial_timestamps(prop):
    assert prop.created == datetime.datetime.fromisoformat(created_timestamp)
    assert prop.modified == datetime.datetime.fromisoformat(created_timestamp)
    assert prop.deleted is None


@pytest.mark.django_db
def test_property_modified_timestamp_changed_when_property_is_changed(prop):
    with freeze_time(modified_timestamp):
        prop.value = "baz"
        prop.save()

        assert prop.created == datetime.datetime.fromisoformat(created_timestamp)
        assert prop.modified == datetime.datetime.fromisoformat(modified_timestamp)
        assert prop.deleted is None


@pytest.mark.django_db
def test_property_deleted_timestamp_set_when_property_is_deleted(prop):
    with freeze_time(deleted_timestamp):
        prop.delete()
        assert prop.modified == datetime.datetime.fromisoformat(deleted_timestamp)
        assert prop.deleted == datetime.datetime.fromisoformat(deleted_timestamp)


@pytest.mark.django_db
def test_vocabulary_delete_hard_deletes_dependent_term_and_property(vocab, prop):
    assert 1 == len(Vocabulary.objects.all())
    assert 1 == len(Term.objects.all())
    assert 1 == len(Property.objects.all())

    vocab.delete()

    # Verify hard delete
    assert 0 == len(Vocabulary.objects.all())
    assert 0 == len(Term.objects.all())
    assert 0 == len(Term.objects.all_with_deleted())
    assert 0 == len(Property.objects.all())
    assert 0 == len(Property.objects.all_with_deleted())

    # Predicate model _not_ deleted
    assert 1 == len(Predicate.objects.all())


@pytest.mark.django_db
def test_term_soft_delete_also_soft_deletes_dependent_property(term, prop):
    assert 1 == len(Term.objects.all())
    assert 1 == len(Property.objects.all())

    term.delete()

    # Verify soft delete
    assert 0 == len(Term.objects.all())
    assert 1 == len(Term.objects.all_with_deleted())
    assert 0 == len(Property.objects.all())
    assert 1 == len(Property.objects.all_with_deleted())

    # Predicate model _not_ deleted
    assert 1 == len(Predicate.objects.all())
