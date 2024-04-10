from csv import DictReader
from logging import getLogger

from django.core.management.base import BaseCommand, CommandError
from plastron.namespaces import namespace_manager
from rdflib.util import from_n3
from vocabs.models import Predicate

logger = getLogger(__name__)


class Command(BaseCommand):
    help = """
           A small management utility that reads a simple, 2-column CSV file (predicate, object_type),
           and does a get_or_create for each predicate listed.
           """

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--file",
            help="The 2-column CSV file (predicate, object_type)",
            action="store",
            type=str,
            required=True,
        )

    def handle(self, *args, **options):
        try:
            with open(options["file"], "r", newline="") as csv_file:
                csv_reader = DictReader(csv_file)

                for row in csv_reader:
                    if None in row:
                        raise CommandError(f'Invalid row, extra column found: {row[None]}')

                    predicate = row['predicate']
                    object_type = row['object_type']

                    if predicate is None or object_type is None:
                        raise CommandError(f'Invalid row: {predicate}, {object_type}')

                    logger.debug(f'Row: {predicate}, {object_type}')

                    uri = from_n3(predicate.strip(), nsm=namespace_manager)
                    Predicate.objects.get_or_create(uri=uri, object_type=object_type.strip())

        except IOError as e:
            raise CommandError(f"Invalid file: {str(e)}") from e
