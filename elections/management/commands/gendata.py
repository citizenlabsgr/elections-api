from contextlib import suppress

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

import factory

from elections import models


class RegionTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.RegionType

    name = factory.Sequence(lambda n: f"Type {n}")


class Command(BaseCommand):
    help = "Generate data for automated testing and manual review"

    def handle(self, *_args, **_kwargs):
        self.get_or_create_superuser()
        self.generate_review_data()

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

    def generate_review_data(self):
        with suppress(IntegrityError):
            for obj in RegionTypeFactory.create_batch(5):
                self.stdout.write(f"Generated region type: {obj}")

    # @staticmethod
    # def fake_election():
    #     date = fake.future_date(end_date="+2y")
    #     kind = random.choice(["General", "Midterm", "Special"])
    #     return f"{date.year} {kind} Election", date
