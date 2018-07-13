import re
from contextlib import suppress

from django.conf import settings
from django.core.management.base import BaseCommand

import log

from elections import helpers, models


class Command(BaseCommand):
    help = "Crawl the Michigan SOS website to discover precincts"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            metavar='ID',
            type=int,
            dest='starting_precinct_id',
            default=1,
            help='Initial MI SOS precinct ID to start the crawl.',
        )
        parser.add_argument(
            '--limit',
            metavar='COUNT',
            type=int,
            dest='max_precincts_count',
            help='Number of precincts to crawl before stopping. ',
        )

    def handle(
        self, starting_precinct_id, max_precincts_count, *_args, **_kwargs
    ):
        log.init(reset=True)
        helpers.enable_requests_cache(settings.REQUESTS_CACHE_EXPIRE_AFTER)
        helpers.requests_cache.core.remove_expired_responses()
        self.discover_precincts(starting_precinct_id, max_precincts_count)

    def discover_precincts(self, starting_precinct_id, max_precincts_count):
        election = (
            models.Election.objects.filter(active=True)
            .exclude(mi_sos_id=None)
            .first()
        )
        self.stdout.write(f"Crawling precincts for election: {election}")

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

        precinct_id = starting_precinct_id - 1
        misses = 0
        while misses < 10:
            precinct_id += 1

            count = models.Precinct.objects.count()
            if max_precincts_count and count >= max_precincts_count:
                self.stdout.write(f"Stopping at {count} precinct(s)")
                return

            with suppress(models.BallotWebsite.DoesNotExist):
                website = models.BallotWebsite.objects.get(
                    mi_sos_election_id=election.mi_sos_id,
                    mi_sos_precinct_id=precinct_id,
                )
                misses = 0
                if not website.stale:
                    log.debug(f'Ballot already scraped: {website}')
                    continue

            # Fetch ballot
            website = models.BallotWebsite.objects.create(
                mi_sos_election_id=election.mi_sos_id,
                mi_sos_precinct_id=precinct_id,
            )
            if website.fetch():
                website.save()
            if website.valid:
                misses = 0
            else:
                log.warn(f"Invalid ballot website: {website}")
                misses += 1
                continue

            # Find county
            match = re.search(
                r'(?P<county_name>[^>]+) County, Michigan', website.mi_sos_html
            )
            assert match, f"Could not find county name: {website.mi_sos_url}"
            county_name = match.group('county_name')

            # Find jurisdiction, ward, and precinct
            jurisdiction_name, ward, precinct = self.parse_jurisdiction(
                website.mi_sos_html, website.mi_sos_url
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
                self.stdout.write(f"Matched jurisdiction: {jurisdiction}")

            # Update precinct
            precinct, created = models.Precinct.objects.get_or_create(
                county=county,
                jurisdiction=jurisdiction,
                ward=ward,
                precinct=precinct,
            )
            if created:
                self.stdout.write(f"Added precinct: {precinct}")
                precinct.mi_sos_id = precinct_id
                precinct.save()
            else:
                self.stdout.write(f"Matched precinct: {precinct}")
                if precinct.mi_sos_id != precinct_id:
                    log.warn(f"Duplicate html: {website}")
                    website.valid = False
                    website.save()
                    continue

            # Update ballot
            ballot, created = models.Ballot.objects.update_or_create(
                election=election,
                precinct=precinct,
                defaults=dict(website=website),
            )
            if created:
                self.stdout.write(f"Added ballot: {ballot}")
            else:
                self.stdout.write(f"Updated ballot: {ballot}")

    @staticmethod
    def parse_jurisdiction(html, url):
        match = None
        for pattern in [
            r'(?P<jurisdiction_name>[^>]+), Ward (?P<ward>\d+) Precinct (?P<precinct>\d+)<',
            r'(?P<jurisdiction_name>[^>]+),  Precinct (?P<precinct>\d+[A-Z]?)<',
            r'(?P<jurisdiction_name>[^>]+), Ward (?P<ward>\d+) <',
        ]:
            match = re.search(pattern, html)
            if match:
                break
        assert match, f"Unable to find precinct information: {url}"

        jurisdiction_name = match.group('jurisdiction_name')

        try:
            ward = int(match.group('ward'))
        except IndexError:
            ward = 0

        try:
            precinct = match.group('precinct')
        except IndexError:
            precinct = ''

        return (jurisdiction_name, ward, precinct)
