import re
from contextlib import suppress

from django.conf import settings
from django.core.management.base import BaseCommand

import log
import requests

from elections import helpers, models


class Command(BaseCommand):
    help = "Crawl the Michigan SOS website to discover polls"

    def handle(self, *_args, **_kwargs):
        log.init(reset=True)
        helpers.enable_requests_cache(settings.REQUESTS_CACHE_EXPIRE_AFTER)
        helpers.requests_cache.core.remove_expired_responses()
        self.discover_polls()

    def discover_polls(self):
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

        poll_id = 0
        misses = 0
        while misses < 3:
            poll_id += 1

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
            match = re.search(
                r'(?P<jurisdiction_name>[^>]+), Ward (?P<ward_number>\d+) Precinct (?P<precinct_number>\d+)',
                html,
            )
            if match:
                ward_number = int(match.group('ward_number'))
            else:
                ward_number = 0
                match = re.search(
                    r'(?P<jurisdiction_name>[^>]+),  Precinct (?P<precinct_number>\d+)',
                    html,
                )
                assert match, f"Unable to find precinct information: {url}"

            jurisdiction_name = match.group('jurisdiction_name')
            precinct_number = int(match.group('precinct_number'))

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
