# pylint: disable=no-self-use

import sys

import log
import pendulum
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from elections import models


class Command(BaseCommand):
    help = "Generate data for local development and review"

    def handle(self, verbosity: int, **_kwargs):
        log.reset()
        log.silence("datafiles")
        log.init(verbosity=verbosity if "-v" in sys.argv[-1] else 2)

        self.get_or_create_superuser()
        self.add_elections()
        self.fetch_districts()

    def get_or_create_superuser(self, username="admin", password="password"):
        User = get_user_model()
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
            name="November Consolidated",
            date=pendulum.parse("2021-11-02", tz="America/Detroit"),
            defaults=dict(active=True, mvic_id=687),
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
