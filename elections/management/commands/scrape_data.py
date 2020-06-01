# pylint: disable=no-self-use,broad-except

import os
import sys
from typing import Optional

from django.core.management.base import BaseCommand

import bugsnag
import log

from elections.commands import scrape_ballots


class Command(BaseCommand):
    help = "Crawl the Michigan SOS website to discover ballots"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-election',
            metavar='MI_SOS_ID',
            type=int,
            default=None,
            help='Initial Michigan SOS election ID to start from.',
        )
        parser.add_argument(
            '--start-precinct',
            metavar='MI_SOS_ID',
            type=int,
            default=1,
            help='Initial Michigan SOS precinct ID to start from.',
        )
        parser.add_argument(
            '--ballot-limit',
            metavar='COUNT',
            type=int,
            help='Maximum number of fetches to perform before stopping.',
        )

    def handle(
        self,
        verbosity: int,
        start_election: Optional[int],
        start_precinct: int,
        ballot_limit: Optional[int],
        **_kwargs,
    ):
        log.reset()
        log.init(verbosity=verbosity if '-v' in sys.argv[-1] else 2)

        try:
            scrape_ballots(
                starting_election_id=start_election,
                starting_precinct_id=start_precinct,
                ballot_limit=ballot_limit,
            )
        except Exception as e:
            if 'HEROKU_APP_NAME' in os.environ:
                log.error("Unable to finish scraping data", exc_info=e)
                bugsnag.notify(e)
                sys.exit(1)
            else:
                raise e from None
