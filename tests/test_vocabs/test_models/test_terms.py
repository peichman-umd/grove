import pytest
from django.db import IntegrityError

from vocabs.models import Vocabulary, Term


@pytest.mark.django_db
def test_terms_must_be_unique_within_vocab():
    # create term "Bar" in first vocab is fine
    vocab = Vocabulary.objects.create(uri='http://example.org/foo#', label='foo')
    Term.objects.create(vocabulary=vocab, name='Bar')

    # create term "Bar" in second vocab is fine
    vocab2 = Vocabulary.objects.create(uri='http://www.example.com/ns/bar#', label='bar')
    Term.objects.create(vocabulary=vocab2, name='Bar')

    # trying to add the term "Bar" to the first vocabulary again should raise an exception
    with pytest.raises(IntegrityError):
        Term.objects.create(vocabulary=vocab, name='Bar')
