# pylint: disable=no-self-use,attribute-defined-outside-init

import itertools
import re

from django.conf import settings
from django.core.management.base import BaseCommand

import bugsnag
import log

from elections import helpers
from elections.models import (
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

    def handle(self, start, limit, *_args, **_kwargs):
        log.init(reset=True)

        helpers.enable_requests_cache(settings.REQUESTS_CACHE_EXPIRE_AFTER)
        helpers.requests_cache.core.remove_expired_responses()

        self.ballot_fetches = 0
        self.max_ballot_fetches = limit

        self.ballot_misses = 0
        self.max_ballot_misses = 10

        try:
            self.run(start)
        except Exception as e:
            bugsnag.notify(e)
            raise e

    def run(self, start: int):
        election = self.get_current_election()
        for mi_sos_precinct_id in itertools.count(start=start):
            if self.should_stop():
                break
            self.fetch_ballot_website(election, mi_sos_precinct_id)

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

    def fetch_ballot_website(
        self, election: Election, mi_sos_precinct_id: int
    ):
        website, created = BallotWebsite.objects.get_or_create(
            mi_sos_election_id=election.mi_sos_id,
            mi_sos_precinct_id=mi_sos_precinct_id,
        )
        if created:
            self.stdout.write(f'Added website: {website}')

        if website.stale:
            website.fetch()
            if website.valid:
                self.add_precent(mi_sos_precinct_id, website)
                website.parse()
            self.ballot_fetches += 1

        if website.valid:
            self.ballot_misses = 0
        else:
            self.ballot_misses += 1

    def add_precent(self, mi_sos_precinct_id: int, website: BallotWebsite):
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
            website.source = True
            website.save()
        elif precinct.mi_sos_id == mi_sos_precinct_id:
            self.stdout.write(f'Matched precinct: {precinct}')
        elif not precinct.mi_sos_id:
            self.stdout.write(f'Updated precinct: {precinct}')
            precinct.mi_sos_id = mi_sos_precinct_id
            precinct.save()
            website.source = True
            website.save()
        else:
            log.warn(f'Duplicate precinct: {website}')
            precinct.delete()
            website.source = False
            website.save()

    def get_district_categories(self):
        return (
            DistrictCategory.objects.get(name="County"),
            DistrictCategory.objects.get(name="Jurisdiction"),
        )

    def parse_jurisdiction(self, html, url):
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
