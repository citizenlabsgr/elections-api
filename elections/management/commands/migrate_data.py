from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

import log

from elections import models  # pylint: unused-import


class Command(BaseCommand):
    help = "Migrate data between existing models"

    def handle(self, *_args, **_kwargs):
        log.init(reset=True)
        for precinct in models.Precinct.objects.filter(ward='0'):
            log.warn(f'Fixing precinct: {precinct}')
            precinct.ward = ''
            try:
                precinct.save()
            except IntegrityError:
                precinct.delete()
        for precinct in models.Precinct.objects.filter(number='0'):
            log.warn(f'Fixing precinct: {precinct}')
            precinct.number = ''
            try:
                precinct.save()
            except IntegrityError:
                precinct.delete()
