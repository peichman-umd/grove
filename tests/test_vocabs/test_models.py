import pytest
from plastron.namespaces import rdfs, dc, rdf
from rdflib import URIRef, Literal

from vocabs.models import Vocabulary, Term, vann, Predicate, Property


@pytest.mark.django_db
def test_vocabulary():
    vocab = Vocabulary(uri='http://example.com/foo#')
    vocab.save()
    assert vocab.uri == 'http://example.com/foo#'
    assert str(vocab) == 'http://example.com/foo#'
    assert vocab.term_count == 0
    term = Term(name='bar', vocabulary=vocab)
    term.save()
    assert term.uri == 'http://example.com/foo#bar'
    assert str(term) == 'http://example.com/foo#bar'
    assert vocab.term_count == 1


@pytest.mark.django_db
def test_graph():
    params = {
        'uri': 'http://example.com/foo#',
        'label': 'Test Vocabulary',
        'description': 'Just a test vocab',
        'preferred_prefix': 'foo',
    }
    vocab = Vocabulary(**params)
    vocab.save()
    term = Term(name='bar', vocabulary=vocab)
    term.save()
    rdf_type, _ = Predicate.objects.get_or_create(uri=rdf.type, object_type=Predicate.ObjectType.URI_REF)
    rdfs_label, _ = Predicate.objects.get_or_create(uri=rdfs.label, object_type=Predicate.ObjectType.LITERAL)
    Property(term=term, predicate=rdf_type, value=rdfs.Class).save()
    Property(term=term, predicate=rdfs_label, value='Bar').save()
    graph, context = vocab.graph()
    assert (URIRef(params['uri']), rdfs.label, Literal(params['label'])) in graph
    assert (URIRef(params['uri']), dc.description, Literal(params['description'])) in graph
    assert (URIRef(params['uri']), vann.preferredNamespacePrefix, Literal(params['preferred_prefix'])) in graph
    assert (URIRef(params['uri'] + 'bar'), dc.identifier, Literal('bar')) in graph
    assert (URIRef(params['uri'] + 'bar'), rdf.type, rdfs.Class) in graph
    assert (URIRef(params['uri'] + 'bar'), rdfs.label, Literal('Bar')) in graph


@pytest.mark.django_db
def test_predicate():
    predicate = Predicate(uri=rdf.type, object_type=Predicate.ObjectType.URI_REF)
    predicate.save()
    assert predicate.curie == 'rdf:type'
    assert Predicate.from_curie('rdf:type') == predicate
    assert str(predicate) == 'rdf:type'
