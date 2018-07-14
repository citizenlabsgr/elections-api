# pylint: disable=unused-import

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

import log

from elections import models


class Command(BaseCommand):
    help = "Migrate data between existing models"

    def handle(self, *_args, **_kwargs):
        log.init(reset=True)