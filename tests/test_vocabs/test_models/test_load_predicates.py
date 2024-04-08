import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from vocabs.models import Predicate


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('filename', 'uri', 'object_type', 'curie'),
    [
        ('test1.csv', 'http://www.w3.org/2000/01/rdf-schema#label', 'Literal', 'rdfs:label'),
        ('test2.csv', 'http://www.w3.org/2002/07/owl#sameAs', 'URIRef', 'owl:sameAs'),
    ]
)
def test_load_predicates(datadir, filename, uri, object_type, curie):
    "Tests importing valid CSV files into the database"

    args = []
    opts = {"file": datadir / filename}
    call_command('load_predicates', *args, **opts)

    predicate = Predicate.objects.first()
    assert predicate.uri == uri
    assert predicate.object_type == object_type
    assert predicate.curie == curie


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('filename', 'message'),
    [
        ('test3.csv', 'Invalid CSV'),
        ('test4.csv', 'Invalid CSV'),
        ('invalid_file_path', 'Invalid file')
    ]
)
def test_bad_csvs(datadir, filename, message):
    "Tests importing invalid CSV files into the database"

    args = []
    opts = {"file": datadir / filename}
    with pytest.raises(CommandError, match=message):
        call_command('load_predicates', *args, **opts)
