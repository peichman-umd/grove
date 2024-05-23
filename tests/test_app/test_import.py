from http import HTTPStatus

import pytest


@pytest.mark.django_db
def test_import_vocabulary(datadir, post, vocab_uri):
    with (datadir / 'foo.ttl').open() as fh:
        response = post('/import', data={'uri': vocab_uri, 'rdf_format': 'text/turtle', 'file': fh})
    assert response.status_code == HTTPStatus.OK
