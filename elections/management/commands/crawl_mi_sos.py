import re
from contextlib import suppress

from django.conf import settings
from django.core.management.base import BaseCommand

import log
import requests

from elections import helpers, models


class Command(BaseCommand):
    help = "Crawl the Michigan SOS website to discover polls"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            metavar='ID',
            type=int,
            dest='starting_poll_id',
            default=1,
            help='Initial MI SOS poll ID to start the crawl.',
        )
        parser.add_argument(
            '--limit',
            metavar='COUNT',
            type=int,
            dest='max_polls_count',
            help='Number of polls to crawl before stopping. ',
        )

    def handle(self, starting_poll_id, max_polls_count, *_args, **_kwargs):
        log.init(reset=True)
        helpers.enable_requests_cache(settings.REQUESTS_CACHE_EXPIRE_AFTER)
        helpers.requests_cache.core.remove_expired_responses()
        self.discover_polls(starting_poll_id, max_polls_count)

    def discover_polls(self, starting_poll_id, max_polls_count):
        election = models.Election.objects.exclude(mi_sos_id=None).first()
        self.stdout.write(f"Crawling polls for election: {election}")

        county_cateogry, created = models.DistrictCategory.objects.get_or_create(
            name="County"
        )
        if created:
            log.warn(f"Created category: {county_cateogry}")

        jurisdiction_category, created = models.DistrictCategory.objects.get_or_create(
            name="Jurisdiction"
        )
        if created:
            log.warn(f"Created category: {jurisdiction_category}")

        poll_id = starting_poll_id - 1
        misses = 0
        while misses < 3:
            poll_id += 1

            count = models.Poll.objects.count()
            if max_polls_count and count >= max_polls_count:
                self.stdout.write(f"Stopping at {count} poll(s)")
                return

            with suppress(models.Poll.DoesNotExist):
                poll = models.Poll.objects.get(mi_sos_id=poll_id)
                log.debug(f"Poll already added: {poll}")
                continue

            # Fetch ballot
            url = models.Ballot.build_mi_sos_url(
                election_id=election.mi_sos_id, poll_id=poll_id
            )
            self.stdout.write(f"Fetching: {url}")
            response = requests.get(url)
            response.raise_for_status()
            html = response.text

            # Find county
            match = re.search(r'(?P<county_name>[^>]+) County, Michigan', html)
            if match:
                misses = 0
            else:
                misses += 1
                self.stdout.write(f"No ballot detected (misses={misses})")
                assert "not available at this time" in html
                continue
            county_name = match.group('county_name')

            # Find jurisdiction, ward, and precinct
            jurisdiction_name, ward_number, precinct_number, precinct_letter = self.parse_jurisdiction(
                html, url
            )

            # Update county
            county, created = models.District.objects.get_or_create(
                category=county_cateogry, name=county_name
            )
            if created:
                self.stdout.write(f"Added county: {county}")
            else:
                self.stdout.write(f"Matched county: {county}")

            # Update jurisdiction
            jurisdiction, created = models.District.objects.get_or_create(
                category=jurisdiction_category, name=jurisdiction_name
            )
            if created:
                self.stdout.write(f"Added jurisdiction: {jurisdiction}")
            else:
                self.stdout.write(f"Matched: jurisdiction: {jurisdiction}")

            # Update poll
            poll, created = models.Poll.objects.update_or_create(
                county=county,
                jurisdiction=jurisdiction,
                ward_number=ward_number,
                precinct_number=precinct_number,
                precinct_letter=precinct_letter,
                defaults=dict(mi_sos_id=poll_id),
            )
            if created:
                self.stdout.write(f"Added poll: {poll}")
            else:
                self.stdout.write(f"Matched: poll: {poll}")

            # Update ballot
            ballot, created = models.Ballot.objects.get_or_create(
                election=election, poll=poll
            )
            if created:
                self.stdout.write(f"Added ballot: {ballot}")
            else:
                self.stdout.write(f"Matched ballot: {ballot}")
            ballot.mi_sos_html = html
            ballot.save()

    @staticmethod
    def parse_jurisdiction(html, url):
        match = None
        for pattern in [
            r'(?P<jurisdiction_name>[^>]+), Ward (?P<ward_number>\d+) Precinct (?P<precinct_number>\d+)<',
            r'(?P<jurisdiction_name>[^>]+),  Precinct (?P<precinct_number>\d+)(?P<precinct_letter>[A-Z]?)<',
            r'(?P<jurisdiction_name>[^>]+), Ward (?P<ward_number>\d+) <',
        ]:
            match = re.search(pattern, html)
            if match:
                break
        assert match, f"Unable to find precinct information: {url}"

        jurisdiction_name = match.group('jurisdiction_name')

        try:
            ward_number = int(match.group('ward_number'))
        except IndexError:
            ward_number = 0

        try:
            precinct_number = int(match.group('precinct_number'))
        except IndexError:
            precinct_number = 0

        try:
            precinct_letter = match.group('precinct_letter')
        except IndexError:
            precinct_letter = ''

        return (
            jurisdiction_name,
            ward_number,
            precinct_number,
            precinct_letter,
        )
