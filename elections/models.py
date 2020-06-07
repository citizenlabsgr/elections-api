from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone

import bugsnag
import log
import pendulum
from model_utils.models import TimeStampedModel

from . import constants, exceptions, helpers


class DistrictCategory(TimeStampedModel):
    """Types of regions bound to ballot items."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    rank = models.IntegerField(default=0, help_text="Controls ballot item ordering")

    class Meta:
        verbose_name_plural = "District Categories"
        ordering = ['name']

    def __str__(self) -> str:
        if self.name in {
            "State",
            "County",
            "Jurisdiction",
            "City",
            "Township",
            "Village",
            "Ward",
            "Precinct",
        }:
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
    description = models.TextField(blank=True)

    active = models.BooleanField(default=True)
    reference_url = models.URLField(blank=True, null=True)

    mi_sos_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ['date', 'name']
        ordering = ['-date']

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

    class Meta:
        unique_together = ['county', 'jurisdiction', 'ward', 'number']

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

    def get_county_district_label(self, district: str) -> str:
        return f"{self.county.name} County, {district}"

    def get_ward_label(self, district: str) -> str:
        return f"{self.jurisdiction}, {district}"

    def get_precinct_label(self) -> str:
        if self.ward and self.number:
            ward_precinct = f"Ward {self.ward}, Precinct {self.number}"
        elif self.ward:
            ward_precinct = f"Ward {self.ward}"
        else:
            ward_precinct = f"Precinct {self.number}"
        return f"{self.jurisdiction}, {ward_precinct}"

    def save(self, *args, **kwargs):
        self.ward = self.ward if self.ward.strip('0') else ''
        self.number = self.number if self.number.strip('0') else ''
        assert self.mi_sos_name
        super().save(*args, **kwargs)


class RegistrationStatus(models.Model):
    """Status of a particular voter's registration."""

    registered = models.BooleanField()
    absentee = models.BooleanField(default=False)
    polling_location = JSONField(blank=True, null=True)
    recently_moved = models.BooleanField(default=False)
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

    def fetch_registration_status(
        self, *, track_missing_data: bool = True
    ) -> RegistrationStatus:
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

            category = DistrictCategory.objects.get(name=category_name)

            if category.name == "County":
                district_name = district_name.replace(" County", "")
            district, created = District.objects.get_or_create(
                category=category, name=district_name
            )
            if created:
                message = f"Created district: {district}"
                log.info(message)

            districts.append(district)

            if district.category.name == "County":
                county = district
            if district.category.name == "Jurisdiction":
                jurisdiction = district

        if data['districts']['Ward']:
            precinct, created = Precinct.objects.get_or_create(
                county=county,
                jurisdiction=jurisdiction,
                ward=data['districts']['Ward'],
                number=data['districts']['Precinct'],
            )
        else:
            precinct, created = Precinct.objects.get_or_create(
                county=county,
                jurisdiction=jurisdiction,
                number=data['districts']['Precinct'],
            )
        if created:
            message = f"Created precinct: {precinct}"
            log.info(message)
            if track_missing_data:
                bugsnag.notify(
                    exceptions.MissingData(message),
                    meta_data={
                        'voter': {
                            'first_name': self.first_name,
                            'last_name': self.last_name,
                            'birth_data': self.birth_date,
                            'zip_code': self.zip_code,
                        }
                    },
                )

        status = RegistrationStatus(
            registered=data['registered'],
            absentee=data['absentee'],
            polling_location=list(data['polling_location'].values()),
            recently_moved=data['recently_moved'],
            precinct=precinct,
        )
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

    last_fetch = models.DateTimeField(null=True, editable=False)
    last_validate = models.DateTimeField(null=True, editable=False)
    last_scrape = models.DateTimeField(null=True, editable=False)
    last_convert = models.DateTimeField(null=True, editable=False)
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
        if not self.last_fetch:
            log.debug(f'Ballot has never been scraped: {self}')
            return True

        age = timezone.now() - self.last_fetch
        if age < timezone.timedelta(minutes=61):
            log.debug(f'Ballot was scraped in the last hour: {self}')
            return False

        if self.last_fetch < constants.SCRAPER_LAST_UPDATED:
            log.info(f'Scraping logic is newer than last scrape: {self}')
            return True

        age_in_days = age.total_seconds() / 3600 / 24
        weight = age_in_days / 14  # fetch once per week on average
        log.debug(f'Ballot was scraped {round(age_in_days, 1)} days ago: {self}')

        return weight > random.random()

    def fetch(self) -> None:
        """Fetch ballot HTML from the URL."""
        self.mi_sos_html = helpers.fetch_ballot(self.mi_sos_url)

        self.fetched = True
        self.last_fetch = timezone.now()

        self.save()

    def validate(self) -> bool:
        """Determine if fetched HTML contains ballot information."""
        log.info(f'Validating ballot HTML: {self}')
        assert self.mi_sos_html, f'Ballot has not been fetched: {self}'

        if (
            "not available at this time" in self.mi_sos_html
            or "currently no items for this ballot" in self.mi_sos_html
            or " County" not in self.mi_sos_html
        ):
            log.info('Ballot URL does not contain precinct information')
            self.valid = False
        else:
            assert "Sample Ballot" in self.mi_sos_html
            log.info('Ballot URL contains precinct information')
            self.valid = True
            self.last_validate = timezone.now()

        self.save()

        return self.valid

    def scrape(self) -> int:
        """Scrape ballot data from the HTML."""
        log.info(f'Scraping data from ballot: {self}')
        assert self.valid, f'Ballot has not been validated: {self}'
        data: Dict[str, Any] = {}

        data['election'] = helpers.parse_election(self.mi_sos_html)
        data['precinct'] = helpers.parse_precinct(self.mi_sos_html, self.mi_sos_url)
        data['ballot'] = {}

        data_count = helpers.parse_ballot(self.mi_sos_html, data['ballot'])
        log.info(f'Ballot URL contains {data_count} parsed item(s)')
        if data_count > 0:
            self.data = data
            if data_count != self.data_count:
                self.parsed = False

        self.data_count = data_count
        self.last_scrape = timezone.now()
        self.save()

        return self.data_count

    def convert(self) -> Ballot:
        """Convert parsed ballot data into a ballot."""
        log.info(f'Converting to a ballot: {self}')
        assert self.data, f'Ballot has not been scrapted: {self}'

        election = self._get_election()
        precinct = self._get_precinct()
        ballot = self._get_ballot(election, precinct)
        self.last_convert = timezone.now()

        self.save()

        return ballot

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
        if created:
            log.info(f'Created district: {jurisdiction}')

        assert self.mi_sos_precinct_id
        precinct, created = Precinct.objects.get_or_create(
            county=county, jurisdiction=jurisdiction, ward=ward, number=number
        )
        if created:
            log.info(f'Created precinct: {precinct}')

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
        BallotWebsite,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='ballot',
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
    def mi_sos_url(self) -> Optional[str]:
        if self.website:
            return self.website.mi_sos_url
        return None

    @property
    def stale(self) -> bool:
        if not self.website.last_parse:
            log.debug('Ballot has never been parsed')
            return True

        if self.website.last_parse < constants.PARSER_LAST_UPDATED:
            log.info(f'Parsing logic is newer than last scrape: {self.website}')
            return True

        age = timezone.now() - self.website.last_parse
        if age < timezone.timedelta(hours=23):
            log.debug('Ballot was parsed in the last day')
            return False

        return True

    def parse(self) -> int:
        log.info(f'Parsing ballot: {self}')
        assert (
            self.website and self.website.data
        ), 'Ballot website has not been converted: {self}'

        count = 0
        for section_name, section_data in self.website.data['ballot'].items():
            section_parser = getattr(self, '_parse_' + section_name.replace(' ', '_'))
            for item in section_parser(section_data):
                if isinstance(item, (Candidate, Proposal)):
                    count += 1

        self.website.parsed = True
        self.website.last_parse = timezone.now()
        self.website.save()

        return count

    def _parse_primary_section(self, data):
        for section_name, section_data in data.items():
            yield from self._parse_partisan_section(section_data, section_name)

    def _parse_partisan_section(self, data, section=''):
        for category_name, positions_data in data.items():
            for position_data in positions_data:

                category = district = None

                if category_name in {'Presidential', 'State', 'State Board'}:
                    district = District.objects.get(name='Michigan')
                elif category_name in {'City', 'Township'}:
                    district = self.precinct.jurisdiction
                elif category_name in {
                    'Congressional',
                    'Legislative',
                    'County',
                    'Delegate',
                }:
                    pass  # district parsed based on position name
                else:
                    raise exceptions.UnhandledData(
                        f'Unhandled category {category_name!r} on {self.website.mi_sos_url}'
                    )

                position_name = position_data['name']

                if district is None:
                    if position_name in {'United States Senator'}:
                        district = District.objects.get(name='Michigan')
                    elif position_name in {'Representative in Congress'}:
                        category = DistrictCategory.objects.get(name='US Congress')
                        district, created = District.objects.get_or_create(
                            category=category, name=position_data['district']
                        )
                        if created:
                            log.info(f'Created district: {district}')
                    elif position_name in {'State Senator'}:
                        category = DistrictCategory.objects.get(name='State Senate')
                        district, created = District.objects.get_or_create(
                            category=category, name=position_data['district']
                        )
                        if created:
                            log.info(f'Created district: {district}')
                    elif position_name in {'Representative in State Legislature'}:
                        category = DistrictCategory.objects.get(name='State House')
                        district, created = District.objects.get_or_create(
                            category=category, name=position_data['district']
                        )
                        if created:
                            log.info(f'Created district: {district}')

                    elif position_name in {'County Commissioner'}:
                        category = DistrictCategory.objects.get(name=position_name)
                        district, created = District.objects.get_or_create(
                            category=category,
                            name=self.precinct.get_county_district_label(
                                position_data['district']
                            ),
                        )
                        if created:
                            log.info(f'Created district: {district}')
                    elif position_name in {'Delegate to County Convention'}:
                        category = DistrictCategory.objects.get(name='Precinct')
                        district, created = District.objects.get_or_create(
                            category=category, name=self.precinct.get_precinct_label(),
                        )
                        if created:
                            log.info(f'Created district: {district}')
                    elif category_name in {'County'}:
                        district = self.precinct.county
                    else:
                        raise exceptions.UnhandledData(
                            f'Unhandled position {position_name!r} on {self.website.mi_sos_url}'
                        )

                position, created = Position.objects.get_or_create(
                    election=self.election,
                    district=district,
                    name=position_data['name'],
                    term=position_data['term'] or "",
                    seats=position_data['seats'],
                    section=section,
                )
                if created:
                    log.info(f'Created position: {position}')
                if not section:
                    # TODO: default to general section
                    # position.section = "General"
                    log.warn(f"Position missing section: {position}")
                position.precincts.add(self.precinct)
                position.save()
                yield position

                for candidate_data in position_data['candidates']:
                    candidate_name = candidate_data['name']

                    if candidate_name in {"Uncommitted"}:
                        log.debug(f'Skipped placeholder candidate: {candidate_name}')
                        continue

                    if candidate_data['party'] is None:
                        raise exceptions.UnhandledData(
                            f'Expected party for {candidate_name!r} on {self.website.mi_sos_url}'
                        )

                    party = Party.objects.get(name=candidate_data['party'])
                    candidate, created = Candidate.objects.update_or_create(
                        position=position,
                        name=candidate_name,
                        defaults={
                            'party': party,
                            'reference_url': candidate_data['finance_link'],
                        },
                    )
                    if created:
                        log.info(f'Created candidate: {candidate}')
                    yield candidate

    def _parse_nonpartisan_section(self, data):
        for category_name, positions_data in data.items():
            for position_data in positions_data:

                category = district = None

                if category_name in {
                    'City',
                    'Township',
                    'Village',
                    'Authority',
                    'Metropolitan',
                }:
                    district = self.precinct.jurisdiction
                elif category_name in {
                    'Community College',
                    'Local School',
                    'Intermediate School',
                    'Library',
                }:
                    category = DistrictCategory.objects.get(name=category_name)
                elif category_name in {'Judicial'}:
                    pass  # district parsed based on position name
                else:
                    raise exceptions.UnhandledData(
                        f'Unhandled category {category_name!r} on {self.website.mi_sos_url}'
                    )

                position_name = position_data['name']

                if district is None:
                    if category is None:
                        if position_name in {'Justice of Supreme Court'}:
                            district = District.objects.get(name='Michigan')
                        elif position_name in {'Judge of Court of Appeals'}:
                            category = DistrictCategory.objects.get(
                                name='Court of Appeals'
                            )
                        elif position_name in {'Judge of Municipal Court'}:
                            category = DistrictCategory.objects.get(
                                name='Municipal Court'
                            )
                        elif position_name in {'Judge of Probate Court'}:
                            category = DistrictCategory.objects.get(
                                name='Probate Court'
                            )
                        elif position_name in {'Judge of Circuit Court'}:
                            category = DistrictCategory.objects.get(
                                name='Circuit Court'
                            )
                        elif position_name in {'Judge of District Court'}:
                            category = DistrictCategory.objects.get(
                                name='District Court'
                            )
                        else:
                            raise exceptions.UnhandledData(
                                f'Unhandled position {position_name!r} on {self.website.mi_sos_url}'
                            )

                    if position_data['district']:
                        district, created = District.objects.get_or_create(
                            category=category, name=position_data['district']
                        )
                        if created:
                            log.info(f'Created district: {district}')
                    else:
                        log.warning(
                            f'Ballot {self.website.mi_sos_url} missing district: {position_data}'
                        )
                        district = self.precinct.jurisdiction

                elif position_name in {'Commissioner by Ward'}:
                    category = DistrictCategory.objects.get(name='Ward')
                    district, created = District.objects.get_or_create(
                        category=category,
                        name=self.precinct.get_ward_label(position_data['district']),
                    )
                    if created:
                        log.info(f'Created district: {district}')

                position, created = Position.objects.get_or_create(
                    election=self.election,
                    district=district,
                    name=position_data['name'],
                    term=position_data['term'] or "",
                    seats=position_data['seats'] or 0,
                )
                if created:
                    log.info(f'Created position: {position}')
                position.section = "Nonpartisan"
                position.precincts.add(self.precinct)
                position.save()
                yield position

                for candidate_data in position_data['candidates']:
                    assert candidate_data['party'] is None
                    party = Party.objects.get(name="Nonpartisan")
                    candidate, created = Candidate.objects.update_or_create(
                        position=position,
                        name=candidate_data['name'],
                        defaults={'party': party},
                    )
                    if created:
                        log.info(f'Created candidate: {candidate}')
                    yield candidate

    def _parse_proposal_section(self, data):
        for category_name, proposals_data in data.items():

            category = district = None

            if category_name in {'State'}:
                district = District.objects.get(name='Michigan')
            elif category_name in {'County'}:
                district = self.precinct.county
            elif category_name in {
                'City',
                'Township',
                'Village',
                'Authority',
                'Local School',
                'Metropolitan',
            }:
                # TODO: Verify this is the correct mapping for 'Local School'
                district = self.precinct.jurisdiction
            elif category_name in {
                'Community College',
                'Intermediate School',
                'District Library',
            }:
                category = DistrictCategory.objects.get(name=category_name)
            else:
                raise exceptions.UnhandledData(
                    f'Unhandled category {category_name!r} on {self.website.mi_sos_url}'
                )

            for proposal_data in proposals_data:

                if district is None:
                    assert category, f'Expected category: {proposals_data}'

                    possible_category_names = [category.name]
                    if category.name == 'District Library':
                        possible_category_names.extend(
                            ['Public Library', 'Community Library', 'Library District']
                        )
                    elif category.name == 'Community College':
                        possible_category_names.extend(['College'])
                    elif category.name == 'Intermediate School':
                        possible_category_names.extend(
                            [
                                'Regional Education Service Agency',
                                'Regional Educational Service Agency',
                                'Regional Education Service',
                                'Area Educational Service Agency',
                            ]
                        )

                    original_exception = None
                    for category_name in possible_category_names:
                        try:
                            district_name = helpers.parse_district_from_proposal(
                                category_name,
                                proposal_data['text'],
                                self.website.mi_sos_url,
                            )
                        except ValueError as e:
                            if original_exception is None:
                                original_exception = e
                        else:
                            break
                    else:
                        raise original_exception  # type: ignore

                    district, created = District.objects.get_or_create(
                        category=category, name=district_name
                    )
                    if created:
                        log.info(f'Created district: {district}')

                proposal, created = Proposal.objects.update_or_create(
                    election=self.election,
                    district=district,
                    name=proposal_data['title'],
                    defaults={'description': proposal_data['text']},
                )
                if created:
                    log.info(f'Created proposal: {proposal}')
                proposal.precincts.add(self.precinct)
                proposal.save()
                yield proposal


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

    term = models.CharField(max_length=200, blank=True)
    seats = models.PositiveIntegerField(default=1, blank=True)
    section = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = [
            'election',
            'section',
            'district',
            'name',
            'term',
            'seats',
        ]
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
