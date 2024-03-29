import pytest

from vocabs.models import import_vocabulary, VocabularyImportError


@pytest.mark.django_db
def test_import_empty_vocabulary(datadir):
    vocab, is_new, count = import_vocabulary(
        file=datadir / 'empty.json',
        uri='http://example.com/vocab/empty#',
        rdf_format='json-ld',
    )
    assert is_new
    assert vocab.label == 'Empty'
    assert vocab.term_count == 0
    assert count['subjects'] == 0
    assert count['new_terms'] == 0
    assert count['new_properties'] == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('filename', 'rdf_format'),
    [
        ('simple.ttl', 'text/turtle'),
        ('simple.json', 'application/ld+json'),
        ('simple.nt', 'application/n-triples'),
        ('simple.xml', 'application/rdf+xml'),
    ],
)
def test_import_simple_vocabulary(datadir, filename, rdf_format):
    vocab, is_new, count = import_vocabulary(
        file=datadir / filename,
        uri='http://example.com/vocab/simple#',
        rdf_format=rdf_format,
    )
    assert is_new
    assert vocab.label == 'Simple'
    assert vocab.term_count == 1
    assert count['subjects'] == 1
    assert count['new_terms'] == 1
    assert count['new_properties'] == 1

    term = vocab.terms.first()
    assert term.name == 'Thing'
    assert term.uri == 'http://example.com/vocab/simple#Thing'


@pytest.mark.django_db
def test_import_same_vocabulary_twice(datadir):
    vocab, is_new, count = import_vocabulary(
        file=datadir / 'simple.ttl',
        uri='http://example.com/vocab/simple#',
        rdf_format='turtle',
    )
    assert is_new
    assert vocab.label == 'Simple'
    assert vocab.term_count == 1
    assert count['subjects'] == 1
    assert count['new_terms'] == 1
    assert count['new_properties'] == 1

    # import the same vocabulary a second time, there should be no changes
    vocab, is_new, count = import_vocabulary(
        file=datadir / 'simple.ttl',
        uri='http://example.com/vocab/simple#',
        rdf_format='turtle',
    )
    assert not is_new
    assert vocab.label == 'Simple'
    assert vocab.term_count == 1
    assert count['subjects'] == 1
    assert count['new_terms'] == 0
    assert count['new_properties'] == 0


@pytest.mark.django_db
def test_import_vocabulary_from_two_files(datadir):
    vocab, is_new, count = import_vocabulary(
        file=datadir / 'simple.ttl',
        uri='http://example.com/vocab/simple#',
        rdf_format='turtle',
    )
    assert is_new
    assert vocab.label == 'Simple'
    assert vocab.term_count == 1
    assert count['subjects'] == 1
    assert count['new_terms'] == 1
    assert count['new_properties'] == 1

    vocab, is_new, count = import_vocabulary(
        file=datadir / 'extra.ttl',
        uri='http://example.com/vocab/simple#',
        rdf_format='turtle',
    )
    assert not is_new
    assert vocab.label == 'Simple'
    assert vocab.term_count == 2
    assert count['subjects'] == 1
    assert count['new_terms'] == 1
    assert count['new_properties'] == 2


@pytest.mark.django_db
def test_import_only_terms_with_base_uri(datadir):
    vocab, is_new, count = import_vocabulary(
        file=datadir / 'superfluous.ttl',
        uri='http://example.com/vocab/simple#',
        rdf_format='turtle',
    )
    assert is_new
    assert vocab.label == 'Simple'
    assert vocab.term_count == 1
    assert count['subjects'] == 1
    assert count['new_terms'] == 1
    assert count['new_properties'] == 1


@pytest.mark.django_db
def test_import_skip_dc_identifier_matching_name(datadir):
    vocab, is_new, count = import_vocabulary(
        file=datadir / 'identifier.ttl',
        uri='http://example.com/vocab/simple#',
        rdf_format='turtle',
    )
    assert is_new
    assert vocab.label == 'Simple'
    assert vocab.term_count == 1
    assert count['subjects'] == 1
    assert count['new_terms'] == 1
    assert count['new_properties'] == 1


@pytest.mark.parametrize(
    ('filename', 'rdf_format'),
    [
        # mismatched format
        ('simple.ttl', 'xml'),
        # malformed file
        ('malformed.json', 'json-ld'),
        # unknown format
        ('simple.ttl', 'UNKNOWN_FORMAT'),
        # missing file
        ('MISSING.xml', 'xml'),
    ]
)
def test_bad_import_throws_error(datadir, filename, rdf_format):
    with pytest.raises(VocabularyImportError):
        import_vocabulary(
            file=datadir / filename,
            uri='http://example.com/vocab/simple#',
            rdf_format=rdf_format,
        )
