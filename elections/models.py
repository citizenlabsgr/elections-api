from django.db import models

import arrow

from . import helpers


class Voter(models.Model):
    """Data needed to look up Michigan voter registration status."""

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField()
    zip_code = models.CharField(max_length=10)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def birth_month(self):
        locale = arrow.locales.get_locale("en")
        return locale.month_name(self.birth_date.month)

    @property
    def birth_year(self):
        return self.birth_date.year

    def fetch_registration_status(self):
        data = helpers.fetch_registration_status_data(self)
        print(data)
        return RegistrationStatus(registered=data["registered"])


class RegistrationStatus(models.Model):
    """Status of a particular voter's registration."""

    registered = models.BooleanField()
    # regions = models.ManyToManyField(Region)


class RegionType(models.Model):
    """Types of regions that ballot items are tied to."""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name
