# pylint: disable=no-self-use

import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

import log
import pendulum

from elections import models


class Command(BaseCommand):
    help = "Generate data for local development and review"

    def handle(self, verbosity: int, **_kwargs):
        log.reset()
        log.init(verbosity=verbosity if '-v' in sys.argv[-1] else 2)

        self.get_or_create_superuser()
        self.add_elections()
        self.fetch_districts()

    def get_or_create_superuser(self, username="admin", password="password"):
        try:
            user = User.objects.create_superuser(
                username=username,
                email=f"{username}@{settings.BASE_DOMAIN}",
                password=password,
            )
            log.info(f"Created new superuser: {user}")
        except IntegrityError:
            user = User.objects.get(username=username)
            log.debug(f"Found existing superuser: {user}")

        return user

    def add_elections(self):
        election, created = models.Election.objects.get_or_create(
            name="May Consolidated",
            date=pendulum.parse("2020-05-05", tz='America/Detroit'),
            defaults=dict(active=False, mi_sos_id=681),
        )
        if created:
            log.info(f"Added election: {election}")

    def fetch_districts(self):
        voter = models.Voter(
            first_name="Rosalynn",
            last_name="Bliss",
            birth_date=pendulum.parse("1975-08-03"),
            zip_code="49503",
        )
        voter.fetch_registration_status(track_missing_data=False)
