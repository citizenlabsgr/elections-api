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

    def handle(self, verbosity: int, election: Optional[int], **_kwargs):
        log.reset()
        log.init(reset=True, verbosity=verbosity if '-v' in sys.argv[-1] else 2)

        try:
            parse_ballots(election_id=election)
        except Exception as e:
            if 'HEROKU_APP_NAME' in os.environ:
                log.error("Unable to finish parsing data", exc_info=e)
                bugsnag.notify(e)
                sys.exit(1)
            else:
                raise e from None
