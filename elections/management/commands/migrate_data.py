# pylint: disable=no-self-use

import sys
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

import log

from elections import defaults
from elections.helpers import normalize_jurisdiction
from elections.models import District, DistrictCategory, Election


class Command(BaseCommand):
    help = "Initialize contants and migrate data between existing models"

    def handle(self, verbosity: int, **_kwargs):
        log.init(verbosity=verbosity if '-v' in sys.argv else 2)

        defaults.initialize_parties()
        defaults.initialize_districts()

        self.update_elections()
        self.update_jurisdictions()

    def update_elections(self):
        for election in Election.objects.filter(active=True):
            age = timezone.now() - timedelta(weeks=3)
            if election.date < age.date():
                log.info(f'Deactivating election: {election}')
                election.active = False
                election.save()

    def update_jurisdictions(self):
        jurisdiction = DistrictCategory.objects.get(name="Jurisdiction")
        for district in District.objects.filter(category=jurisdiction):

            old = district.name
            new = normalize_jurisdiction(district.name)

            if new != old:

                if District.objects.filter(category=jurisdiction, name=new):
                    log.warning(f'Deleting district {old!r} in favor of {new!r}')
                    district.delete()
                else:
                    log.info(f'Renaming district {old!r} to {new!r}')
                    district.name = new
                    district.save()
