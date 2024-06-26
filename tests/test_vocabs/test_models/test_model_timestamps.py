import datetime
import vocabs
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
    assert vocab.updated == datetime.datetime.fromisoformat(created_timestamp)
    assert vocab.published is None


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


@pytest.mark.django_db
def test_vocabulary_updated_timestamp(predicate):
    with freeze_time(created_timestamp) as frozen_datetime:
        # New vocabulary
        vocab_added_time = frozen_datetime().replace(tzinfo=datetime.UTC)
        vocab = Vocabulary(uri='http://example.com/foo#')
        vocab.save()

        assert vocab.created == vocab_added_time
        assert vocab.modified == vocab_added_time
        assert vocab.updated == vocab_added_time

        # New Term
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        term_added_time = frozen_datetime().replace(tzinfo=datetime.UTC)
        term = Term(name='bar', vocabulary=vocab)
        term.save()

        assert vocab.created == vocab_added_time
        assert vocab.modified == vocab_added_time
        assert vocab.updated == term_added_time

        # New Property
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        prop_added_time = frozen_datetime().replace(tzinfo=datetime.UTC)
        prop = Property(term=term, predicate=predicate, value='Bar')
        prop.save()

        assert vocab.created == vocab_added_time
        assert vocab.modified == vocab_added_time
        assert vocab.updated == prop_added_time

        # Vocabulary modification
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        vocab_modified_time = frozen_datetime().replace(tzinfo=datetime.UTC)
        vocab.description = "update vocab"
        vocab.save()

        assert vocab.created == vocab_added_time
        assert vocab.modified == vocab_modified_time
        assert vocab.updated == vocab_modified_time

        # Term modification
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        term_modified_time = frozen_datetime().replace(tzinfo=datetime.UTC)
        term.description = "update term"
        term.save()

        assert vocab.modified == vocab_modified_time
        assert term.modified == term_modified_time
        assert vocab.updated == term_modified_time

        # Property modification
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        prop_modified_time = frozen_datetime().replace(tzinfo=datetime.UTC)

        prop.value = "update prop"
        prop.save()

        assert vocab.modified == vocab_modified_time
        assert term.modified == term_modified_time
        assert prop.modified == prop_modified_time
        assert vocab.updated == prop_modified_time

        # Property deletion
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        prop_deleted_time = frozen_datetime().replace(tzinfo=datetime.UTC)

        prop.delete()

        assert vocab.updated == prop_deleted_time

        # Term deletion
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        term_deleted_time = frozen_datetime().replace(tzinfo=datetime.UTC)

        term.delete()

        assert vocab.updated == term_deleted_time


@pytest.mark.django_db
def test_vocabulary_published_timestamp(vocab, monkeypatch, datadir):
    monkeypatch.setattr(vocabs.models, 'VOCAB_OUTPUT_DIR', datadir)
    assert vocab.published is None
    assert vocab.is_published is False

    current_timestamp = '2024-07-15T18:45:22Z'
    with freeze_time(current_timestamp) as frozen_datetime:
        vocab_publish_time = frozen_datetime().replace(tzinfo=datetime.UTC)
        vocab.publish()
        vocab.refresh_from_db()
        assert vocab.published == vocab_publish_time
        assert vocab.is_published is True

        vocab.unpublish()
        vocab.refresh_from_db()
        assert vocab.published is None
        assert vocab.is_published is False


@pytest.mark.django_db
def test_vocabulary_modified_and_published_timestamps_set_to_same_time_on_publish(vocab, monkeypatch, datadir):
    monkeypatch.setattr(vocabs.models, 'VOCAB_OUTPUT_DIR', datadir)
    # This test verifies that the "published" and "modified" timestamps are set
    # to the same timestamp when a vocabulary is published. This test is needed
    # because when changing the "published" timestamp for publication, the
    # the "modified" timestamp would normally be set to the moment when the
    # vocabulary is saved, which would be _after_ the "published" timestamp,
    # resulting in the "has_updated" flag returning an incorrect result.

    # This test should _not_ freeze time

    vocab.publish()
    assert vocab.published is not None
    assert vocab.modified == vocab.published


@pytest.mark.django_db
def test_vocabulary_has_updated(vocab, predicate, monkeypatch, datadir):
    monkeypatch.setattr(vocabs.models, 'VOCAB_OUTPUT_DIR', datadir)
    with freeze_time(created_timestamp) as frozen_datetime:
        vocab_added_time = frozen_datetime().replace(tzinfo=datetime.UTC)
        current_time = frozen_datetime().replace(tzinfo=datetime.UTC)

        # New vocabulary
        assert vocab.created == vocab_added_time
        assert vocab.updated == vocab_added_time
        assert vocab.has_updated is True
        assert vocab.published is None

        vocab.publish()

        assert vocab.has_updated is False
        assert vocab.published == current_time

        # New Term
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        current_time = frozen_datetime().replace(tzinfo=datetime.UTC)

        term = Term(name='bar', vocabulary=vocab)
        term.save()

        assert vocab.has_updated is True

        vocab.publish()

        assert vocab.has_updated is False
        assert vocab.published == current_time

        # New Property
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        current_time = frozen_datetime().replace(tzinfo=datetime.UTC)

        prop = Property(term=term, predicate=predicate, value='Bar')
        prop.save()

        assert vocab.has_updated is True

        vocab.publish()

        assert vocab.has_updated is False
        assert vocab.published == current_time

        # Vocabulary modification
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        current_time = frozen_datetime().replace(tzinfo=datetime.UTC)

        vocab.description = "update vocab"
        vocab.save()

        assert vocab.has_updated is True

        vocab.publish()

        assert vocab.has_updated is False
        assert vocab.published == current_time

        # Term modification
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        current_time = frozen_datetime().replace(tzinfo=datetime.UTC)

        term.description = "update term"
        term.save()

        assert vocab.has_updated is True

        vocab.publish()

        assert vocab.has_updated is False
        assert vocab.published == current_time

        # Property modification
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        current_time = frozen_datetime().replace(tzinfo=datetime.UTC)

        prop.value = "update prop"
        prop.save()

        assert vocab.has_updated is True

        vocab.publish()

        assert vocab.has_updated is False
        assert vocab.published == current_time

        # Property deletion
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        current_time = frozen_datetime().replace(tzinfo=datetime.UTC)

        prop.delete()

        assert vocab.has_updated is True

        vocab.publish()

        assert vocab.has_updated is False
        assert vocab.published == current_time

        # Term deletion
        frozen_datetime.tick(delta=datetime.timedelta(days=32))
        current_time = frozen_datetime().replace(tzinfo=datetime.UTC)

        term.delete()

        assert vocab.has_updated is True

        vocab.publish()

        assert vocab.has_updated is False
        assert vocab.published == current_time
