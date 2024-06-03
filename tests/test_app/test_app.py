from contextlib import contextmanager
from http import HTTPStatus

import pytest
from vocabs.models import Vocabulary


@contextmanager
def vocab_with_uri(uri: str):
    yield Vocabulary.objects.get(uri=uri)


def test_site_root_unauthenticated(client):
    response = client.get('/')
    assert 'Login Required' in response.content.decode()


def test_site_root_authenticated(admin_client):
    response = admin_client.get('/')
    assert response.status_code == 302
    assert response.headers['Location'] == '/vocabs/'


@pytest.mark.django_db
def test_list_vocabularies(admin_client):
    response = admin_client.get('/vocabs', follow=True)
    assert 'Vocabularies' in response.content.decode()


def test_list_prefixes(admin_client):
    response = admin_client.get('/prefixes', follow=True)
    assert 'Prefixes' in response.content.decode()


@pytest.mark.django_db
def test_create_vocabulary(post, vocab_uri):
    response = post('/vocabs/', data={'uri': vocab_uri})
    assert 'Vocabulary: Foo' in response.content.decode()
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
def test_create_and_delete_vocabulary(post, vocab_uri, admin_client):
    vocab_path = post('/vocabs/', data={'uri': vocab_uri}).wsgi_request.path
    with Vocabulary.with_uri(vocab_uri) as vocab:
        assert vocab.uri == vocab_uri
        assert vocab.label == 'Foo'
        assert vocab.description == ''
        assert vocab.preferred_prefix == ''
    admin_client.delete(vocab_path)
    with pytest.raises(Vocabulary.DoesNotExist):
        Vocabulary.objects.get(uri=vocab_uri)


@pytest.mark.parametrize(
    ('format_param', 'expected_content_type'),
    [
        ('json-ld', 'application/ld+json; charset=utf-8'),
        ('json-ld', 'application/ld+json; charset=utf-8'),
        ('json-ld', 'application/ld+json; charset=utf-8'),
        ('rdfxml', 'application/rdf+xml; charset=utf-8'),
        ('rdf/xml', 'application/rdf+xml; charset=utf-8'),
        ('rdf', 'application/rdf+xml; charset=utf-8'),
        ('xml', 'application/rdf+xml; charset=utf-8'),
        ('ttl', 'text/turtle; charset=utf-8'),
        ('turtle', 'text/turtle; charset=utf-8'),
        ('nt', 'application/n-triples; charset=utf-8'),
        ('ntriples', 'application/n-triples; charset=utf-8'),
        ('n-triples', 'application/n-triples; charset=utf-8'),
    ]
)
@pytest.mark.django_db
def test_graph(admin_client, post, vocab_uri, format_param, expected_content_type):
    vocab_path = post('/vocabs/', data={'uri': vocab_uri}).wsgi_request.path
    response = admin_client.get(vocab_path + '/graph', data={'format': format_param})
    assert response.headers['Content-Type'] == expected_content_type


@pytest.mark.django_db
def test_graph_not_acceptable(admin_client, post, vocab_uri):
    vocab_path = post('/vocabs/', data={'uri': vocab_uri}).wsgi_request.path
    response = admin_client.get(vocab_path + '/graph', data={'format': 'NOT_A_VALID_FORMAT'})
    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
