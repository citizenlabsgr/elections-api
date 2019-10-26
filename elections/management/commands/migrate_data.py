# pylint: disable=no-self-use

import sys
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

import log

from elections import defaults
from elections.models import Election


class Command(BaseCommand):
    help = "Initialize contants and migrate data between existing models"

    def handle(self, verbosity: int, **_kwargs):
        log.init(verbosity=verbosity if '-v' in sys.argv else 2)

        defaults.initialize_parties()
        defaults.initialize_districts()

        self.update_elections()

    def update_elections(self):
        for election in Election.objects.filter(active=True):
            age = timezone.now() - timedelta(weeks=3)
            if election.date < age.date():
                log.info(f'Deactivating election: {election}')
                election.active = False
                election.save()
