from django.db import models

import arrow

from . import helpers


class Voter(models.Model):
    """Data needed to look up Michigan voter registration status."""

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField()
    zip_code = models.CharField(max_length=10)

    def __repr__(self) -> str:
        birth = arrow.get(self.birth_date).format("YYYY-MM-DD")
        return f"<voter: {self}, birth={birth}, zip={self.zip_code}>"

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


class RegionKind(models.Model):
    """Types of regions bound to ballot items."""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class Region(models.Model):
    """Regions bound to ballot items."""

    kind = models.ForeignKey(RegionKind, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ["kind", "name"]
