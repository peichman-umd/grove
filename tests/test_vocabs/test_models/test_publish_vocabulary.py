from pathlib import Path
from typing import Iterator, Callable

import pytest

import vocabs
from vocabs.models import Vocabulary, Term


def published_files(vocabulary: Vocabulary, vocab_output_dir: Path) -> Iterator[Path]:
    for fmt in Vocabulary.OUTPUT_FORMATS:
        yield vocab_output_dir / (vocabulary.basename + '.' + fmt.extension)


@pytest.fixture
def create_vocab(monkeypatch, datadir) -> Callable[..., Vocabulary]:
    monkeypatch.setattr(vocabs.models, 'VOCAB_OUTPUT_DIR', datadir)

    def _create_vocab(published: bool = False):
        vocab = Vocabulary(uri='http://example.com/foo#')
        vocab.save()
        term = Term(name='bar', vocabulary=vocab)
        term.save()
        if published:
            vocab.publish()
        return vocab

    return _create_vocab


@pytest.mark.django_db
def test_vocabulary_starts_unpublished(datadir, create_vocab):
    vocabulary = create_vocab(published=False)
    assert not vocabulary.is_published
    # no files should be present
    for file in published_files(vocabulary=vocabulary, vocab_output_dir=datadir):
        assert not file.exists()


@pytest.mark.django_db
def test_publish_vocabulary_creates_files(datadir, create_vocab):
    vocabulary = create_vocab(published=False)
    vocabulary.publish()
    assert vocabulary.is_published

    # publish should create all the files
    for file in published_files(vocabulary=vocabulary, vocab_output_dir=datadir):
        assert file.exists()


@pytest.mark.django_db
def test_unpublish_vocabulary_removes_files(datadir, create_vocab):
    vocabulary = create_vocab(published=True)
    vocabulary.unpublish()
    assert not vocabulary.is_published

    # unpublish should remove all the files
    for file in published_files(vocabulary=vocabulary, vocab_output_dir=datadir):
        assert not file.exists()


@pytest.mark.django_db
def test_unpublished_vocab_has_no_publication_date(create_vocab):
    assert create_vocab(published=False).publication_date is None


@pytest.mark.django_db
def test_published_vocab_has_publication_date(create_vocab):
    assert create_vocab(published=True).publication_date is not None
