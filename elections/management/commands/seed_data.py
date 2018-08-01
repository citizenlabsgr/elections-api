# pylint: disable=no-self-use

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

import pendulum

from elections import models


class Command(BaseCommand):
    help = "Generate data for local development and review"

    def handle(self, *_args, **_kwargs):
        self.get_or_create_superuser()
        self.add_known_data()
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

    def add_known_data(self):
        election, _ = models.Election.objects.get_or_create(
            name="State Primary",
            date=pendulum.parse("2018-08-07", tz='America/Detroit'),
            defaults=dict(active=True, mi_sos_id=675),
        )
        self.stdout.write(f"Added election: {election}")

        election, _ = models.Election.objects.get_or_create(
            name="State General",
            date=pendulum.parse("2018-11-06", tz='America/Detroit'),
            defaults=dict(active=True, mi_sos_id=676),
        )
        self.stdout.write(f"Added election: {election}")

        state, _ = models.DistrictCategory.objects.get_or_create(name="State")
        self.stdout.write(f'Added category: {state}')

        county, _ = models.DistrictCategory.objects.get_or_create(
            name="County"
        )
        self.stdout.write(f"Added category: {county}")

        jurisdiction, _ = models.DistrictCategory.objects.get_or_create(
            name="Jurisdiction"
        )
        self.stdout.write(f"Added category: {jurisdiction}")

        michigan, _ = models.District.objects.get_or_create(
            category=state, name="Michigan"
        )
        self.stdout.write(f'Added district: {michigan}')

        kent, _ = models.District.objects.get_or_create(
            category=county, name="Kent"
        )
        self.stdout.write(f"Added district: {kent}")

        grand_rapids, _ = models.District.objects.get_or_create(
            category=jurisdiction, name="City of Grand Rapids"
        )
        self.stdout.write(f"Added district: {grand_rapids}")

        precinct, _ = models.Precinct.objects.get_or_create(
            county=kent,
            jurisdiction=grand_rapids,
            ward='1',
            number='9',
            mi_sos_id=1828,
        )
        self.stdout.write(f"Added precinct: {precinct}")

        for party_name in [
            'Democratic',
            'Green',
            'Libertarian',
            'Republican',
            'Nonpartisan',
        ]:
            party, _ = models.Party.objects.get_or_create(name=party_name)
            self.stdout.write(f'Added party: {party}')

    def fetch_districts(self):
        voter = models.Voter(
            first_name="Jace",
            last_name="Browning",
            birth_date=pendulum.parse("1987-06-02"),
            zip_code="49503",
        )
        voter.fetch_registration_status()
