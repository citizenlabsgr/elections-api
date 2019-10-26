# pylint: disable=no-self-use


import sys
import warnings
from typing import Optional

from django.core.management.base import BaseCommand

import log

from elections.commands import scrape_ballots


class Command(BaseCommand):
    help = "Crawl the Michigan SOS website to discover ballots"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            metavar='MI_SOS_ID',
            type=int,
            default=1,
            help='Initial Michigan SOS precinct ID to start from.',
        )
        parser.add_argument(
            '--limit',
            metavar='COUNT',
            type=int,
            help='Maximum number of fetches to perform before stopping.',
        )

    def handle(self, verbosity: int, start: int, limit: Optional[int], **_kwargs):
        log.init(verbosity=verbosity if '-v' in sys.argv else 2)

        # https://github.com/citizenlabsgr/elections-api/issues/81
        warnings.simplefilter('once')

        scrape_ballots(start=start, limit=limit)
