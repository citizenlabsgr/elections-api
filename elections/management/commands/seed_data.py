# pylint: disable=no-self-use

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
        log.init(verbosity=verbosity)

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
            self.stdout.write(f"Created new superuser: {user}")
        except IntegrityError:
            user = User.objects.get(username=username)
            self.stdout.write(f"Found existing superuser: {user}")

        return user

    def add_elections(self):
        election, _ = models.Election.objects.get_or_create(
            name="November Consolidated",
            date=pendulum.parse("2019-11-05", tz='America/Detroit'),
            defaults=dict(active=True, mi_sos_id=679),
        )
        self.stdout.write(f"Added election: {election}")

    def fetch_districts(self):
        voter = models.Voter(
            first_name="Rosalynn",
            last_name="Bliss",
            birth_date=pendulum.parse("1975-08-03"),
            zip_code="49503",
        )
        voter.fetch_registration_status()
