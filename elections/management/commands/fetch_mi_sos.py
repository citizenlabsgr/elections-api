from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

import log

from elections import models


class Command(BaseCommand):
    help = "Fetch ballot information from the Michigan SOS website"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            metavar='COUNT',
            type=int,
            dest='max_ballots_count',
            help='Number of ballots to fetch before stopping.',
        )

    def handle(self, max_ballots_count, *_args, **_kwargs):
        log.init(reset=True)
        self.fetch_ballots_html(max_ballots_count)

    def fetch_ballots_html(self, max_ballots_count):
        for election in models.Election.objects.filter(active=True):

            if not election.mi_sos_id:
                log.warn(f"No MI SOS ID for election: {election}")
                continue

            if max_ballots_count:
                query = models.Precinct.objects.all()
            else:
                query = models.Precinct.objects.filter(
                    modified__lt=timezone.now() - timedelta(hours=24)
                )
            for precinct in query:

                if not precinct.mi_sos_id:
                    log.warn(f"No MI SOS ID for precinct: {precinct}")
                    continue

                # Update ballot
                ballot, created = models.Ballot.objects.get_or_create(
                    election=election, precinct=precinct
                )
                if created:
                    self.stdout.write(f"Created ballot: {ballot}")
                else:
                    self.stdout.write(f"Matched ballot: {ballot}")

                # Update website
                if not ballot.website:
                    website, created = models.BallotWebsite.objects.get_or_create(
                        mi_sos_election_id=ballot.election.id,
                        mi_sos_precinct_id=ballot.precinct.id,
                    )
                    if created:
                        self.stdout.write(f"Created website: {website}")
                        website.fetch()
                        website.save()
                    ballot.website = website
                    ballot.save()

                if ballot.website.stale and ballot.website.fetch():
                    self.stdout.write(f"Updated website: {ballot.website}")
                    ballot.website.save()

                count = models.Ballot.objects.count()
                if max_ballots_count and count >= max_ballots_count:
                    self.stdout.write(f"Stopping at {count} ballot(s)")
                    return
