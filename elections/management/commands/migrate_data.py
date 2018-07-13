from django.core.management.base import BaseCommand

import log

from elections import models


class Command(BaseCommand):
    help = "Migrate data between existing models"

    def handle(self, *_args, **_kwargs):
        log.init(reset=True)
        for precinct in models.Precinct.objects.filter(ward='0'):
            precinct.ward = ''
            precinct.save()
        for precinct in models.Precinct.objects.filter(number='0'):
            precinct.number = ''
            precinct.save()
