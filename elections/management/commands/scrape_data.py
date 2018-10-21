# pylint: disable=no-self-use,attribute-defined-outside-init

import itertools
import re
from typing import Tuple

from django.conf import settings
from django.core.management.base import BaseCommand

import bugsnag
import log

from elections.models import (
    Ballot,
    BallotWebsite,
    District,
    DistrictCategory,
    Election,
    Precinct,
)


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

    def handle(self, start: int, limit: int, verbosity: int, **_kwargs):
        log.init(reset=True, debug=verbosity >= 2)

        self.ballot_fetches = 0
        self.max_ballot_fetches = limit

        self.ballot_misses = 0
        self.max_ballot_misses = 10

        election = self.get_current_election()

        self.stdout.write('')
        for mi_sos_precinct_id in itertools.count(start=start):

            if self.should_stop():
                break

            try:
                if self.scrape_ballot_website(election, mi_sos_precinct_id):
                    self.stdout.write('')
            except Exception as e:
                if settings.DEBUG:
                    log.exception(e)
                else:
                    bugsnag.notify(e)
                raise e from None

    def get_current_election(self) -> Election:
        election = (
            Election.objects.filter(active=True)
            .exclude(mi_sos_id=None)
            .first()
        )
        self.stdout.write(f'Crawling precincts for election: {election}')
        # TODO: Ensure election date is in the future
        return election

    def should_stop(self) -> bool:
        if self.ballot_misses >= self.max_ballot_misses:
            self.stdout.write(
                f'Stopping at {self.ballot_misses} ballot misses (limit: {self.max_ballot_misses})'
            )
            return True

        if (
            self.max_ballot_fetches
            and self.ballot_fetches >= self.max_ballot_fetches
        ):
            self.stdout.write(
                f'Stopping at {self.ballot_fetches} ballot fetches (limit: {self.max_ballot_fetches})'
            )
            return True

        return False

    def scrape_ballot_website(
        self, election: Election, mi_sos_precinct_id: int
    ) -> bool:
        fetched_or_parsed = False

        website, created = BallotWebsite.objects.get_or_create(
            mi_sos_election_id=election.mi_sos_id,
            mi_sos_precinct_id=mi_sos_precinct_id,
        )
        if created:
            self.stdout.write(f'Added website: {website}')

        if website.stale:
            website.fetch()
            self.ballot_fetches += 1
            fetched_or_parsed = True

            if website.valid:
                precinct = self.ensure_precinct(mi_sos_precinct_id, website)
                ballot = self.ensure_ballot(election, precinct)
                website.ballot = ballot
                website.save()

                if website.source:
                    website.parse()

        if website.valid:
            self.ballot_misses = 0

            if website.source and not website.parsed:
                precinct = self.ensure_precinct(mi_sos_precinct_id, website)
                ballot = self.ensure_ballot(election, precinct)
                website.ballot = ballot
                website.parse()
                fetched_or_parsed = True

        else:
            self.ballot_misses += 1

        return fetched_or_parsed

    def ensure_precinct(
        self, mi_sos_precinct_id: int, website: BallotWebsite
    ) -> Precinct:
        county_category, jurisdiction_category = self.get_district_categories()

        # Parse county
        match = re.search(
            r'(?P<county_name>[^>]+) County, Michigan', website.mi_sos_html
        )
        assert match, f'Could not find county name: {website.mi_sos_url}'
        county_name = match.group('county_name')

        # Parse jurisdiction, ward, and number
        jurisdiction_name, ward, number = self.parse_jurisdiction(
            website.mi_sos_html, website.mi_sos_url
        )

        # Add county
        county, created = District.objects.get_or_create(
            category=county_category, name=county_name
        )
        if created:
            self.stdout.write(f'Added county: {county}')
        else:
            self.stdout.write(f'Matched county: {county}')

        # Add jurisdiction
        jurisdiction, created = District.objects.get_or_create(
            category=jurisdiction_category, name=jurisdiction_name
        )
        if created:
            self.stdout.write(f'Added jurisdiction: {jurisdiction}')
        else:
            self.stdout.write(f'Matched jurisdiction: {jurisdiction}')

        # Add precinct
        precinct, created = Precinct.objects.get_or_create(
            county=county,
            jurisdiction=jurisdiction,
            ward=ward,
            number=number,
            defaults=dict(mi_sos_id=mi_sos_precinct_id),
        )
        if created:
            self.stdout.write(f'Added precinct: {precinct}')
        elif precinct.mi_sos_id:
            self.stdout.write(f'Matched precinct: {precinct}')
        else:
            self.stdout.write(f'Updated precinct: {precinct}')
            precinct.mi_sos_id = mi_sos_precinct_id
            precinct.save()

        return precinct

    def ensure_ballot(self, election: Election, precinct: Precinct) -> Ballot:
        ballot, created = Ballot.objects.update_or_create(
            election=election, precinct=precinct
        )
        if created:
            self.stdout.write(f'Added ballot: {ballot}')

        return ballot

    def get_district_categories(
        self
    ) -> Tuple[DistrictCategory, DistrictCategory]:
        return (
            DistrictCategory.objects.get(name="County"),
            DistrictCategory.objects.get(name="Jurisdiction"),
        )

    def parse_jurisdiction(self, html: str, url: str) -> Tuple[str, str, str]:
        match = None
        for pattern in [
            r'(?P<jurisdiction_name>[^>]+), Ward (?P<ward>\d+) Precinct (?P<precinct>\d+)<',
            r'(?P<jurisdiction_name>[^>]+),  Precinct (?P<precinct>\d+[A-Z]?)<',
            r'(?P<jurisdiction_name>[^>]+), Ward (?P<ward>\d+) <',
        ]:
            match = re.search(pattern, html)
            if match:
                break
        assert match, f'Unable to find precinct information: {url}'

        jurisdiction_name = match.group('jurisdiction_name')

        try:
            ward = match.group('ward')
        except IndexError:
            ward = ''

        try:
            precinct = match.group('precinct')
        except IndexError:
            precinct = ''

        return (jurisdiction_name, ward, precinct)
