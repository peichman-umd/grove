from contextlib import contextmanager

import pytest

from vocabs.models import Vocabulary


@contextmanager
def vocab_with_uri(uri: str):
    yield Vocabulary.objects.get(uri=uri)


@pytest.fixture
def vocab_uri() -> str:
    return 'http://example.com/foo#'


@pytest.fixture
def post(client):
    def _post(url: str, **kwargs):
        return client.post(url, follow=True, **kwargs)
    return _post


@pytest.mark.django_db
def test_list_vocabularies(client):
    response = client.get('/vocabs', follow=True)
    assert 'Vocabularies' in response.content.decode()


def test_list_prefixes(client):
    response = client.get('/vocabs/prefixes', follow=True)
    assert 'Prefixes' in response.content.decode()


@pytest.mark.django_db
def test_create_vocabulary(post, vocab_uri):
    response = post('/vocabs/', data={'uri': vocab_uri})
    assert f'Vocabulary: {vocab_uri}' in response.content.decode()
    assert len(Vocabulary.objects.all()) == 1


@pytest.mark.django_db
def test_create_and_update_vocabulary(post, vocab_uri):
    vocab_path = post('/vocabs/', data={'uri': vocab_uri}).wsgi_request.path
    with Vocabulary.with_uri(vocab_uri) as vocab:
        assert vocab.uri == vocab_uri
        assert vocab.label == 'Foo'
        assert vocab.description == ''
        assert vocab.preferred_prefix == ''
    post(vocab_path, data={'uri': vocab_uri, 'label': 'bar', 'description': 'Vocab foo bar', 'preferred_prefix': 'foo'})
    with Vocabulary.with_uri(vocab_uri) as vocab:
        assert vocab.uri == vocab_uri
        assert vocab.label == 'bar'
        assert vocab.description == 'Vocab foo bar'
        assert vocab.preferred_prefix == 'foo'


@pytest.mark.django_db
def test_graph(client, post, vocab_uri):
    vocab_path = post('/vocabs/', data={'uri': vocab_uri}).wsgi_request.path
    response = client.get(vocab_path + '/graph')
    assert response.headers['Content-Type'].startswith('application/ld+json')
