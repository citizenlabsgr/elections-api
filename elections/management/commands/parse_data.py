# pylint: disable=broad-except

import os
import sys

import bugsnag
import log
from django.core.management.base import BaseCommand

from elections.commands import parse_ballots


class Command(BaseCommand):
    help = "Convert fetched ballot data into database records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--election",
            metavar="MVIC_ID",
            type=int,
            default=None,
            help="Michigan SOS election ID to parse ballots for.",
        )
        parser.add_argument(
            "--start-precinct",
            metavar="MVIC_ID",
            type=int,
            default=1,
            help="Initial Michigan SOS precinct ID to start from.",
        )

    def handle(self, verbosity: int, election: int | None, start_precinct: int, **_kwargs):  # type: ignore
        log.reset()
        log.silence("datafiles")
        log.init(reset=True, verbosity=verbosity if "-v" in sys.argv[-1] else 2)

        try:
            parse_ballots(election_id=election, starting_precinct_id=start_precinct)
        except Exception as e:
            if "HEROKU_APP_NAME" in os.environ:
                log.error("Unable to finish parsing data", exc_info=e)
                bugsnag.notify(e)
                sys.exit(1)
            else:
                raise e from None
