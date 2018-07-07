from django.core.management.base import BaseCommand

import log

from elections import models


class Command(BaseCommand):
    help = "Fetch ballot information from the Michigan SOS website"

    def handle(self, *_args, **_kwargs):
        log.init(reset=True)
        self.fetch_ballots_html()

    def fetch_ballots_html(self):
        for election in models.Election.objects.filter(active=True):

            if not election.mi_sos_id:
                log.warn(f"No MI SOS ID for election: {election}")
                continue

            for poll in models.Poll.objects.all():

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
