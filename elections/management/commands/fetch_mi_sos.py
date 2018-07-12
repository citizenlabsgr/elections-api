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
            for poll in query:

                if not poll.mi_sos_id:
                    log.warn(f"No MI SOS ID for poll: {poll}")
                    continue

                ballot, created = models.Ballot.objects.get_or_create(
                    election=election, poll=poll
                )
                if created:
                    self.stdout.write(f"Create ballot: {ballot}")

                if ballot.update_mi_sos_html():
                    self.stdout.write(f"Updated ballot: {ballot}")
                    ballot.save()

                count = models.Ballot.objects.count()
                if max_ballots_count and count >= max_ballots_count:
                    self.stdout.write(f"Stopping at {count} ballot(s)")
                    return
