from django.core.management.base import BaseCommand

import log

from elections import models


class Command(BaseCommand):
    help = "Migrate data between existing models"

    def handle(self, *_args, **_kwargs):
        log.init(reset=True)

        for ballot in models.Ballot.objects.all():
            webpage, created = models.BallotWebpage.objects.update_or_create(
                mi_sos_election_id=ballot.election.mi_sos_id,
                mi_sos_precinct_id=ballot.precinct.mi_sos_id,
                defaults=dict(mi_sos_html=ballot.mi_sos_html, valid=True),
            )
            if created:
                self.stdout.write(f'Created webpage: {webpage}')
            else:
                self.stdout.write(f'Updated webpage: {webpage}')
