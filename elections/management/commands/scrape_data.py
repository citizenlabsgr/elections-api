# pylint: disable=no-self-use

import itertools
import warnings
from typing import Optional

from django.core.management.base import BaseCommand

import log

from elections.models import BallotWebsite, Election


class Command(BaseCommand):
    help = "Crawl the Michigan SOS website to parse ballots"

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
        log.init(verbosity=verbosity)
        warnings.simplefilter('once')

        last_election = Election.objects.exclude(active=True).last()

        error_count = 0

        for election_id in itertools.count(last_election.mi_sos_id + 1):
            ballot_count = self.scrape_ballots(election_id, start, limit)

            if ballot_count:
                error_count = 0
            else:
                error_count += 1

            if error_count >= 3:
                log.info(f'No more ballots to scrape')
                break

            if limit and ballot_count >= limit:
                log.info(f'Stopping after fetching {ballot_count} ballot(s)')
                break

    def scrape_ballots(
        self, election_id: int, starting_precinct_id: int, limit: Optional[int]
    ) -> int:
        log.info(f'Scrapping ballots for election {election_id}')
        log.info(f'Starting from precinct {starting_precinct_id}')
        if limit:
            log.info(f'Stopping after {limit} ballots')

        ballot_count = 0
        error_count = 0

        for precinct_id in itertools.count(starting_precinct_id):
            website, created = BallotWebsite.objects.get_or_create(
                mi_sos_election_id=election_id, mi_sos_precinct_id=precinct_id
            )
            if created:
                log.info(f'Discovered new website: {website}')
            if website.stale or limit:
                website.fetch()
                if website.valid:
                    website.parse()
                if website.data:
                    website.convert()
            if website.valid:
                ballot_count += 1
                error_count = 0
            else:
                error_count += 1

            if limit and ballot_count >= limit:
                break

            if error_count >= 10:
                log.info(f'No more ballots to scrape for election {election_id}')
                break

        return ballot_count
