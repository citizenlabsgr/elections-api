import sys
from datetime import datetime

import log
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.utils import timezone

from elections import models


class Command(BaseCommand):
    help = "Generate data for local development and review"

    def handle(self, verbosity: int, **_kwargs):  # type: ignore
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
        url = "https://michiganelections.io/api/ballots/?active_election=null"
        log.info(f"Fetching latest election from {url}")
        response = requests.get(url, timeout=10)
        data = response.json()
        ballot = data["results"][0]
        election = ballot["election"]

        election, created = models.Election.objects.get_or_create(
            name=election["name"],
            date=datetime.strptime(election["date"], "%Y-%m-%d").date(),
            defaults=dict(
                active=election["active"],
                mvic_id=ballot["mvic_url"].strip("/").split("/")[-1],
            ),
        )
        if created:
            log.info(f"Added election: {election}")

    def fetch_districts(self):
        voter = models.Voter(
            first_name="Rosalynn",
            last_name="Bliss",
            birth_date=timezone.make_aware(datetime(1975, 8, 3)),
            zip_code="49503",
        )
        voter.fetch_registration_status()
