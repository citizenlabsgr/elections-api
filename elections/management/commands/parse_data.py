# pylint: disable=no-self-use

import sys
import warnings

from django.core.management.base import BaseCommand

import log

from elections.commands import parse_ballots


class Command(BaseCommand):
    help = "Convert fetched ballot data into database records"

    def handle(self, verbosity: int, **_kwargs):
        log.init(verbosity=verbosity if '-v' in sys.argv else 2)

        # https://github.com/citizenlabsgr/elections-api/issues/81
        warnings.simplefilter('once')

        parse_ballots()
