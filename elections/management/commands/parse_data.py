# pylint: disable=no-self-use,broad-except

import os
import sys
from typing import Optional

from django.core.management.base import BaseCommand

import bugsnag
import log

from elections.commands import parse_ballots


class Command(BaseCommand):
    help = "Convert fetched ballot data into database records"

    def add_arguments(self, parser):
        parser.add_argument(
            '--election',
            metavar='MI_SOS_ID',
            type=int,
            default=None,
            help='Michigan SOS election ID to parse ballots for.',
        )
        parser.add_argument(
            '--refetch',
            action='store_true',
            help='Fetch, validate, and scrape ballots again if parsing fails.',
        )

    def handle(self, verbosity: int, election: Optional[int], refetch: bool, **_kwargs):
        log.init(verbosity=verbosity if '-v' in sys.argv else 2)

        try:
            parse_ballots(election_id=election, refetch=refetch)
        except Exception as e:
            if 'HEROKU_APP_NAME' in os.environ:
                log.error("Unable to finish parsing data", exc_info=e)
                bugsnag.notify(e)
            else:
                raise e from None
