from __future__ import annotations

import random
from typing import Any, Dict, List

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone

import bugsnag
import log
import pendulum
from model_utils.models import TimeStampedModel

from . import helpers, scraper


class DistrictCategory(TimeStampedModel):
    """Types of regions bound to ballot items."""

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "District Categories"
        ordering = ['name']

    def __str__(self) -> str:
        if self.name in {"County", "Jurisdiction", "City", "Township"}:
            return self.name
        return f'{self.name} District'


class District(TimeStampedModel):
    """Districts bound to ballot items."""

    category = models.ForeignKey(DistrictCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    population = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        unique_together = ['category', 'name']
        ordering = ['-population']

    def __repr__(self) -> str:
        return f'<District: {self.name} ({self.category})>'

    def __str__(self) -> str:
        return self.name


class Election(TimeStampedModel):
    """Point in time where voters can cast opinions on ballot items."""

    name = models.CharField(max_length=100)
    date = models.DateField()

    active = models.BooleanField(default=True)
    reference_url = models.URLField(blank=True, null=True)

    mi_sos_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ['date', 'name']
        ordering = ['date']

    def __str__(self) -> str:
        return ' | '.join(self.mi_sos_name)

    @property
    def mi_sos_name(self) -> List[str]:
        return [
            self.name,
            pendulum.parse(self.date.isoformat()).format("dddd, MMMM D, YYYY"),
        ]


# https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/polling_location.html
# TODO: PollingLocation(TimestampedModel): ...


class Precinct(TimeStampedModel):
    """Specific region where all voters share a ballot."""

    county = models.ForeignKey(
        District, related_name='counties', on_delete=models.CASCADE
    )
    jurisdiction = models.ForeignKey(
        District, related_name='jurisdictions', on_delete=models.CASCADE
    )
    ward = models.CharField(max_length=2, blank=True)
    number = models.CharField(max_length=3, blank=True)

    # TODO: Remove this field to normalize data
    mi_sos_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ['county', 'jurisdiction', 'ward', 'number']
        ordering = ['mi_sos_id']

    def __str__(self) -> str:
        return ' | '.join(self.mi_sos_name)

    @property
    def mi_sos_name(self) -> List[str]:
        if self.ward and self.number:
            ward_precinct = f"Ward {self.ward} Precinct {self.number}"
        elif self.ward:
            # Extra space is intentional to match the MI SOS website format
            ward_precinct = f"Ward {self.ward} "
        else:
            assert self.number, f"Ward and precinct are missing: pk={self.id}"
            # Extra space is intentional to match the MI SOS website format
            ward_precinct = f" Precinct {self.number}"
        return [
            f"{self.county} County, Michigan",
            f"{self.jurisdiction}, {ward_precinct}",
        ]

    def save(self, *args, **kwargs):
        self.ward = self.ward if self.ward.strip('0') else ''
        self.number = self.number if self.number.strip('0') else ''
        assert self.mi_sos_name
        super().save(*args, **kwargs)


class RegistrationStatus(models.Model):
    """Status of a particular voter's registration."""

    registered = models.BooleanField()
    precinct = models.ForeignKey(Precinct, null=True, on_delete=models.SET_NULL)
    # We can't use 'ManytoManyField' because this model is never saved
    districts: List[District] = []

    def save(self, *args, **kwargs):
        raise NotImplementedError


class Voter(models.Model):
    """Data needed to look up Michigan voter registration status."""

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField()
    zip_code = models.CharField(max_length=10)

    def __repr__(self) -> str:
        birth = pendulum.parse(str(self.birth_date)).format("YYYY-MM-DD")
        return f"<voter: {self}, birth={birth}, zip={self.zip_code}>"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def birth_month(self) -> int:
        return self.birth_date.month

    @property
    def birth_year(self) -> int:
        return self.birth_date.year

    def fetch_registration_status(self) -> RegistrationStatus:
        data = helpers.fetch_registration_status_data(self)

        if not data['registered']:
            return RegistrationStatus(registered=False)

        districts: List[District] = []
        county = jurisdiction = None

        for category_name, district_name in sorted(data['districts'].items()):
            if not district_name:
                log.debug(f'Skipped blank district: {category_name}')
                continue

            if category_name in ["Ward", "Precinct"]:
                log.debug(f"Skipped category: {category_name}")
                continue

            category, created = DistrictCategory.objects.get_or_create(
                name=category_name
            )
            if created:
                log.info(f"New category: {category}")

            if category.name == "County":
                district_name = district_name.replace(" County", "")
            district, created = District.objects.get_or_create(
                category=category, name=district_name
            )
            if created:
                log.info(f"New district: {district}")

            districts.append(district)

            if district.category.name == "County":
                county = district
            if district.category.name == "Jurisdiction":
                jurisdiction = district

        precinct, created = Precinct.objects.get_or_create(
            county=county,
            jurisdiction=jurisdiction,
            ward=data['districts']['Ward'],
            number=data['districts']['Precinct'],
            defaults=dict(mi_sos_id=0),
        )
        if created:
            log.info(f"New precinct: {precinct}")
        if not precinct.mi_sos_id:
            bugsnag.notify(ValueError(f'Precinct missing MI SOS ID: {precinct}'))

        status = RegistrationStatus(registered=data['registered'], precinct=precinct)
        status.districts = districts

        return status

    def save(self, *args, **kwargs):
        raise NotImplementedError


# https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/party.html
class Party(TimeStampedModel):
    """Affiliation for a particular candidate."""

    name = models.CharField(max_length=50, unique=True, editable=False)
    color = models.CharField(max_length=7, blank=True, editable=False)

    class Meta:
        verbose_name_plural = "Parties"
        ordering = ['name']

    def __str__(self):
        return self.name


class BallotWebsite(models.Model):
    """Raw HTML of potential ballot from the MI SOS website."""

    mi_sos_election_id = models.PositiveIntegerField()
    mi_sos_precinct_id = models.PositiveIntegerField()

    mi_sos_html = models.TextField(blank=True, editable=False)

    fetched = models.BooleanField(default=False, editable=False)
    valid = models.NullBooleanField(editable=False)
    parsed = models.BooleanField(default=False, editable=False)

    data = JSONField(null=True, editable=False)
    data_count = models.IntegerField(default=-1, editable=False)
    refetch_weight = models.FloatField(default=1.0, editable=False)

    last_fetch = models.DateTimeField(null=True, editable=False)
    last_fetch_with_precinct = models.DateTimeField(null=True, editable=False)
    last_fetch_with_ballot = models.DateTimeField(null=True, editable=False)
    last_parse = models.DateTimeField(null=True, editable=False)

    class Meta:
        unique_together = ['mi_sos_election_id', 'mi_sos_precinct_id']

    def __str__(self) -> str:
        return self.mi_sos_url

    @property
    def mi_sos_url(self) -> str:
        return helpers.build_mi_sos_url(
            election_id=self.mi_sos_election_id, precinct_id=self.mi_sos_precinct_id
        )

    @property
    def stale(self) -> bool:
        return self.refetch_weight > random.random()

    def fetch(self) -> bool:
        """Fetch ballot HTML from the URL."""
        self.mi_sos_html = scraper.fetch(self.mi_sos_url)

        self.fetched = True
        self.last_fetch = timezone.now()

        if (
            "not available at this time" in self.mi_sos_html
            or " County" not in self.mi_sos_html
        ):
            log.warn('Ballot URL does not contain precinct information')
            self.valid = False
        else:
            assert "Sample Ballot" in self.mi_sos_html
            log.info('Ballot URL contains precinct information')
            self.valid = True
            self.last_fetch_with_precinct = timezone.now()

        self.save()

        return self.valid

    def parse(self) -> int:
        """Parse ballot data from the HTML."""
        assert self.valid, 'Ballot has not been fetched'
        data: Dict[str, Any] = {}

        data['election'] = scraper.parse_election(self.mi_sos_html)
        data['precinct'] = scraper.parse_precinct(self.mi_sos_html, self.mi_sos_url)
        data['ballot'] = {}

        data_count = scraper.parse_ballot(self.mi_sos_html, data['ballot'])
        log.info(f'Ballot URL contains {data_count} parsed item(s)')
        if data_count:
            self.last_fetch_with_ballot = timezone.now()
            self.data = data

        if data_count == self.data_count:
            min_weight = 1 / 14 if self.valid else 1 / 28
            self.refetch_weight = max(min_weight, self.refetch_weight / 2)
        elif self.data_count == -1:
            self.refetch_weight = 0.5
        else:
            if self.parsed and data_count:
                self.parsed = False
            self.refetch_weight = (self.refetch_weight + 1.0) / 2

        self.data_count = data_count
        self.refetch_weight = round(self.refetch_weight, 3)
        self.save()

        return self.data_count

    def convert(self) -> int:
        """Convert parsed ballot data into models."""
        log.info(f'Exctracting models for ballot: {self}')
        assert self.data, 'Ballot has not been parsed'

        count = 0

        election = self._get_election()
        precinct = self._get_precinct()
        self._get_ballot(election, precinct)

        # self.parsed = True
        # self.last_parse = timezone.now()
        # self.balot = ???
        # self.save()

        return count

    def _get_election(self) -> Election:
        election_name, election_date = self.data['election']

        election, created = Election.objects.get_or_create(
            mi_sos_id=self.mi_sos_election_id,
            defaults={'name': election_name, 'date': pendulum.date(*election_date)},
        )
        if created:
            log.info(f'Created election: {election}')

        assert (
            election.name == election_name
        ), f'Election {election.mi_sos_id} name changed: {election_name}'

        return election

    def _get_precinct(self) -> Precinct:
        county_name, jurisdiction_name, ward, number = self.data['precinct']

        county, created = District.objects.get_or_create(
            category=DistrictCategory.objects.get(name="County"), name=county_name
        )
        if created:
            log.info(f'Created district: {county}')

        jurisdiction, created = District.objects.get_or_create(
            category=DistrictCategory.objects.get(name="Jurisdiction"),
            name=jurisdiction_name,
        )
        if jurisdiction:
            log.info(f'Created district: {jurisdiction}')

        assert self.mi_sos_precinct_id
        precinct, created = Precinct.objects.get_or_create(
            county=county,
            jurisdiction=jurisdiction,
            ward=ward,
            number=number,
            defaults={'mi_sos_id': self.mi_sos_precinct_id},
        )
        if created:
            log.info(f'Created precinct: {precinct}')
        elif precinct.mi_sos_id != self.mi_sos_election_id:
            log.warning(
                f'Precinct ID changed from {precinct.mi_sos_id} to {self.mi_sos_precinct_id}'
            )
            precinct.mi_sos_id = self.mi_sos_election_id
            precinct.save()

        return precinct

    @staticmethod
    def _get_ballot(election: Election, precinct: Precinct) -> Ballot:
        ballot, created = Ballot.objects.get_or_create(
            election=election, precinct=precinct
        )
        if created:
            log.info(f'Created ballot: {ballot}')
        return ballot


class Ballot(TimeStampedModel):
    """Full ballot bound to a particular polling location."""

    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    precinct = models.ForeignKey(Precinct, on_delete=models.CASCADE)

    website = models.OneToOneField(
        BallotWebsite, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        unique_together = ['election', 'precinct']
        ordering = ['election__date']

    def __str__(self) -> str:
        return ' | '.join(self.mi_sos_name)

    @property
    def mi_sos_name(self) -> List[str]:
        return self.election.mi_sos_name + self.precinct.mi_sos_name

    @property
    def mi_sos_url(self) -> str:
        return helpers.build_mi_sos_url(
            election_id=self.election.mi_sos_id, precinct_id=self.precinct.mi_sos_id
        )


class BallotItem(TimeStampedModel):

    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.CASCADE, null=True)
    precincts = models.ManyToManyField(Precinct)

    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    reference_url = models.URLField(blank=True, null=True)

    class Meta:
        abstract = True


class Proposal(BallotItem):
    """Ballot item with a boolean outcome."""

    class Meta:
        unique_together = ['election', 'district', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name


class Position(BallotItem):
    """Ballot item selecting one ore more candidates."""

    term = models.CharField(max_length=200)
    seats = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ['election', 'district', 'name', 'term', 'seats']
        ordering = ['name', 'seats']

    def __str__(self):
        if self.term:
            return f'{self.name} ({self.term})'
        return self.name


# https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/candidate.html
class Candidate(TimeStampedModel):
    """Individual running for a particular position."""

    position = models.ForeignKey(
        Position, null=True, on_delete=models.CASCADE, related_name='candidates'
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    reference_url = models.URLField(blank=True, null=True)
    party = models.ForeignKey(Party, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ['position', 'name']
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} for {self.position}'
