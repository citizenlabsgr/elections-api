# pylint: disable=no-self-use

import sys
import warnings

from django.core.management.base import BaseCommand

import log

from elections.commands import parse_ballots


class Command(BaseCommand):
    help = "Convert fetched ballot data into database records"

    def add_arguments(self, parser):
        parser.add_argument(
            '--refetch',
            action='store_true',
            help='Fetch, validate, and scrape ballots again if parsing fails.',
        )

    def handle(self, verbosity: int, refetch: bool, **_kwargs):
        log.init(verbosity=verbosity if '-v' in sys.argv else 2)

        # https://github.com/citizenlabsgr/elections-api/issues/81
        warnings.simplefilter('once')

        parse_ballots(refetch=refetch)
