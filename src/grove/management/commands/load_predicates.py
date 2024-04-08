from csv import reader
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
                csv_reader = reader(csv_file)
                next(csv_reader)

                try:
                    for predicate, object_type in csv_reader:
                        logger.debug(f'Predicate: {predicate}, {object_type}')
                        uri = from_n3(predicate, nsm=namespace_manager)
                        Predicate.objects.get_or_create(uri=uri, object_type=object_type)
                except ValueError as e:
                    raise CommandError(f"Invalid CSV: {str(e)}") from e

        except IOError as e:
            raise CommandError(f"Invalid file: {str(e)}") from e
