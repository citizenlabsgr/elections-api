import string
from contextlib import suppress

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

import arrow
import factory
from factory import fuzzy

from elections import models


class DistrictCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DistrictCategory

    name = fuzzy.FuzzyText(
        length=1, prefix="District Category ", chars=string.ascii_uppercase
    )


class DistrictFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.District

    category = fuzzy.FuzzyChoice(models.DistrictCategory.objects.all())
    name = fuzzy.FuzzyText(
        length=1, prefix="District ", chars=string.ascii_uppercase
    )
    population = fuzzy.FuzzyInteger(low=1_000, high=100_000)


class ElectionFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Election

    date = fuzzy.FuzzyDate(
        start_date=arrow.utcnow().shift(years=+1),
        end_date=arrow.utcnow().shift(years=+4),
    )
    name = fuzzy.FuzzyChoice(["General", "Midterm", "Special"])


class Command(BaseCommand):
    help = "Generate data for automated testing and manual review"

    def handle(self, *_args, **_kwargs):
        self.get_or_create_superuser()
        self.add_known_data()
        self.generate_random_data()

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
            date=arrow.get("2018-08-07").datetime,
            defaults=dict(mi_sos_id=675),
        )
        self.stdout.write(f"Added election: {election}")

        county, _ = models.DistrictCategory.objects.get_or_create(
            name="County"
        )
        self.stdout.write(f"Added category: {county}")

        jurisdiction, _ = models.DistrictCategory.objects.get_or_create(
            name="Jurisdiction"
        )
        self.stdout.write(f"Added category: {jurisdiction}")

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
            ward_number=1,
            precinct_number=9,
            mi_sos_id=1828,
        )
        self.stdout.write(f"Added precinct: {precinct}")

    def generate_random_data(self):
        with suppress(IntegrityError):
            for obj in DistrictCategoryFactory.create_batch(5):
                self.stdout.write(f"Generated category: {obj}")

        with suppress(IntegrityError):
            for obj in DistrictFactory.create_batch(20):
                self.stdout.write(f"Generated district: {obj}")

        with suppress(IntegrityError):
            for obj in ElectionFactory.create_batch(3):
                self.stdout.write(f"Generated election: {obj}")
