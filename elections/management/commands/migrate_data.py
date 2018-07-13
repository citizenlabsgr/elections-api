from django.core.management.base import BaseCommand

import log


class Command(BaseCommand):
    help = "Migrate data between existing models"

    def handle(self, *_args, **_kwargs):
        log.init(reset=True)
