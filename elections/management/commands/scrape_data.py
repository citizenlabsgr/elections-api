# pylint: disable=broad-except

import os
import sys

import bugsnag
import log
from django.core.management.base import BaseCommand

from elections.commands import scrape_ballots, update_elections


class Command(BaseCommand):
    help = "Crawl the Michigan SOS website to discover ballots"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-election",
            metavar="MVIC_ID",
            type=int,
            default=None,
            help="Initial Michigan SOS election ID to start from.",
        )
        parser.add_argument(
            "--start-precinct",
            metavar="MVIC_ID",
            type=int,
            default=1,
            help="Initial Michigan SOS precinct ID to start from.",
        )
        parser.add_argument(
            "--ballot-limit",
            metavar="COUNT",
            type=int,
            help="Maximum number of fetches to perform before stopping.",
        )

    def handle(  # type: ignore
        self,
        verbosity: int,
        start_election: int | None,
        start_precinct: int,
        ballot_limit: int | None,
        **_kwargs,
    ):
        log.reset()
        log.silence("datafiles")
        log.init(verbosity=verbosity if "-v" in sys.argv[-1] else 2)

        try:
            update_elections()
            scrape_ballots(
                starting_election_id=start_election,
                starting_precinct_id=start_precinct,
                ballot_limit=ballot_limit,
            )
        except Exception as e:
            if "HEROKU_APP_NAME" in os.environ:
                log.error("Unable to finish scraping data", exc_info=e)
                bugsnag.notify(e)
                sys.exit(1)
            else:
                raise e from None
