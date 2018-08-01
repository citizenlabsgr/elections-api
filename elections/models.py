from __future__ import annotations

import random
import string
from datetime import timedelta
from typing import List, Optional, Union

from django.db import models
from django.utils import timezone

import log
import pendulum
import requests
from bs4 import BeautifulSoup, element
from model_utils.models import TimeStampedModel

from . import helpers


class DistrictCategory(TimeStampedModel):
    """Types of regions bound to ballot items."""

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "District Categories"

    def __str__(self) -> str:
        return self.name


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

    active = models.BooleanField(default=False)
    reference_url = models.URLField(blank=True, null=True)

    mi_sos_id = models.PositiveIntegerField(blank=True, null=True)

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

    mi_sos_id = models.PositiveIntegerField(blank=True, null=True)

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
            assert (
                self.number
            ), f"Ward and precinct are missing: id={self.id} mi_sos_id={self.mi_sos_id}"  # pylint: disable=no-member
            # Extra space is intentional to match the MI SOS website format
            ward_precinct = f" Precinct {self.number}"
        return [
            f"{self.county} County, Michigan",
            f"{self.jurisdiction}, {ward_precinct}",
        ]


class RegistrationStatus(models.Model):
    """Status of a particular voter's registration."""

    registered = models.BooleanField()
    precinct = models.ForeignKey(
        Precinct, null=True, on_delete=models.SET_NULL
    )
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
    def birth_month(self) -> str:
        return pendulum.parse(str(self.birth_date)).format("MMMM")

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
            if not (category_name and district_name):
                log.warn("Skipped blank MI SOS district")
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
        )
        if created:
            log.info(f"New precinct: {precinct}")

        status = RegistrationStatus(
            registered=data['registered'], precinct=precinct
        )
        status.districts = districts

        return status

    def save(self, *args, **kwargs):
        raise NotImplementedError


# https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/party.html
class Party(TimeStampedModel):
    """Affiliation for a particular candidate."""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class BallotWebsite(TimeStampedModel):
    """Raw HTML of potential ballot from the MI SOS website."""

    mi_sos_election_id = models.PositiveIntegerField()
    mi_sos_precinct_id = models.PositiveIntegerField()

    mi_sos_html = models.TextField(blank=True)
    fetched = models.DateTimeField(null=True)

    valid = models.NullBooleanField()
    source = models.NullBooleanField()

    class Meta:
        unique_together = ['mi_sos_election_id', 'mi_sos_precinct_id']

    def __str__(self) -> str:
        return self.mi_sos_url

    @property
    def mi_sos_url(self) -> str:
        return self.build_mi_sos_url(
            election_id=self.mi_sos_election_id,
            precinct_id=self.mi_sos_precinct_id,
        )

    def stale(self, fuzz=0.0):
        if not self.fetched:
            log.debug(f'Age of fetch: <infinity>')
            return True

        age = timezone.now() - self.fetched
        log.debug(f'Age of fetch: {age}')

        if self.valid:
            days = 1.0
            days += days * random.uniform(-fuzz, +fuzz)
            stale_age = timedelta(days=days)
        else:
            weeks = 1.0
            weeks += weeks * random.uniform(-fuzz, +fuzz)
            stale_age = timedelta(weeks=weeks)
        log.debug(f'Fetch becomes stale: {stale_age}')

        return age > stale_age

    def fetch(self) -> bool:
        url = self.mi_sos_url

        log.info(f'Fetching {url}')
        response = requests.get(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Geck o/20100101 Firefox/40.1'
            },
        )
        response.raise_for_status()

        self.fetched = timezone.now()

        html = response.text
        log.debug(f"Ballot HTML: {self.valid}")
        if "not available at this time" in html:
            log.warn(f'Invalid ballot URL: {url}')
            self.valid = False
        elif "General Information" in html:
            log.info(f'Valid ballot URL: {url}')
            self.valid = True

        updated = self.mi_sos_html != html
        self.mi_sos_html = html

        return updated

    def parse(self):
        soup = BeautifulSoup(self.mi_sos_html, 'html.parser')

        county = Precinct.objects.get(mi_sos_id=self.mi_sos_precinct_id).county
        election = Election.objects.get(mi_sos_id=self.mi_sos_election_id)
        party = None
        results = []
        for index, table in enumerate(soup.find_all('table')):
            result = self._handle(table, county, election, party)

            if isinstance(result, (Party, Position, Proposal)):
                results.append(result)
            if isinstance(result, Party):
                party = result

            if result:
                continue

            html = table.prettify()
            msg = f'Unexpected table ({index}) on {self.mi_sos_url}:\n\n{html}'
            raise ValueError(msg)

        return results

    def _handle(
        self,
        table: element.Tag,
        county: District,
        election: Election,
        party: Optional[Party],
    ) -> Union[None, Party, Position, Proposal]:
        for handler in [
            self._handle_primary_header,
            self._handle_party_section,
            self._handle_position,
            self._handle_proposal_header,
            self._handle_proposal,
        ]:
            try:
                result = handler(  # type: ignore
                    table, county=county, election=election, party=party
                )
            except:
                print(table.prettify())
                raise

            if result:
                return result

        return None

    @staticmethod
    def _handle_primary_header(table: element.Tag, **_) -> bool:
        td = table.find('td', class_='primarySection')
        if td:
            header = td.text.strip()
            log.debug(f'Found header: {header!r}')
            if "partisan section" in header.lower():
                return True
        return False

    @staticmethod
    def _handle_party_section(table: element.Tag, **_) -> Optional[Party]:
        if table.get('class') != ['primaryTable']:
            return None

        td = table.find('td', class_='partyHeading')
        section = td.text.strip()
        log.debug(f'Found section: {section!r}')
        name = section.split(' ')[0].title()
        return Party.objects.get(name=name)

    @staticmethod
    def _handle_position(
        table: element.Tag,
        county: District,
        election: Election,
        party: Optional[Party],
    ) -> Optional['Position']:
        assert party, 'Party must be parsed before positions'
        if table.get('class') != ['tblOffice']:
            return None

        # Parse category

        category = None
        td = table.find(class_='division')
        if td:
            category_name = string.capwords(td.text)
            if category_name not in {
                "Congressional",
                "Legislative",
                "Delegate",
            }:
                log.debug(f'Parsing category from division: {td.text!r}')
                category = DistrictCategory.objects.get(name=category_name)

        if not category:
            td = table.find(class_='office')
            if td:
                office = string.capwords(td.text)

                if office == "United States Senator":
                    log.debug(f'Parsing category from office: {td.text!r}')
                    category = DistrictCategory.objects.get(name="State")

                elif office == "Representative In Congress":
                    log.debug(f'Parsing category from office: {td.text!r}')
                    category = DistrictCategory.objects.get(
                        name="US Congress District"
                    )
                elif office == "State Senator":
                    log.debug(f'Parsing category from office: {td.text!r}')
                    category = DistrictCategory.objects.get(
                        name="State Senate District"
                    )
                elif office == "Representative In State Legislature":
                    log.debug(f'Parsing category from office: {td.text!r}')
                    category = DistrictCategory.objects.get(
                        name="State House District"
                    )

                elif office == "Delegate To County Convention":
                    log.debug(f'Parsing category from office: {td.text!r}')
                    category = DistrictCategory.objects.get(name="County")

        if not category:
            class_ = 'mobileOnly'
            td = table.find(class_=class_)
            if td:
                category_name = string.capwords(td.text)
                log.debug(f'Parsing category from {class_!r}: {td.text!r}')
                category = DistrictCategory.objects.get(name=category_name)

        log.info(f'Parsed {category!r}')
        assert category

        # Parse district

        district = None
        td = table.find(class_='office')
        if td:
            office = string.capwords(td.text)

            if office == "Governor":
                log.debug(f'Parsing district from office: {td.text!r}')
                district = District.objects.get(
                    category=category, name="Michigan"
                )
            elif office == "United States Senator":
                log.debug(f'Parsing district from office: {td.text!r}')
                district = District.objects.get(
                    category=category, name="Michigan"
                )

            elif category.name == "County":
                log.debug(f'Parsing district from office: {td.text!r}')
                district = county

            else:
                td = table.find(class_='term')
                log.debug(f'Parsing district from term: {td.text!r}')
                district_name = string.capwords(td.text)
                district = District.objects.get(
                    category=category, name=district_name
                )

        log.info(f'Parsed {district!r}')
        assert district

        # Parse position

        office = table.find(class_='office').text
        seats = table.find_all(class_='term')[-1].text
        log.debug(f'Parsing position from: {office!r} when {seats!r}')
        position_name = string.capwords(office)
        if 'DELEGATE' in office:
            position_name = f'{position_name} ({party})'
        position, _ = Position.objects.get_or_create(
            election=election,
            district=district,
            name=position_name,
            seats=int(seats.strip().split()[-1]),
        )
        log.info(f'Parsed {position!r}')

        # Parse candidates

        for td in table.find_all(class_='candidate'):
            log.debug(f'Parsing candidate: {td.text!r}')
            candidate_name = td.text.strip()

            if candidate_name == "No candidates on ballot":
                log.warn(f'No {party} candidates for {position}')
                break

            candidate, _ = Candidate.objects.get_or_create(
                name=candidate_name, party=party, position=position
            )
            log.info(f'Parsed {candidate!r}')

        return position

    @staticmethod
    def _handle_proposal_header(table: element.Tag, **_) -> bool:
        if table.get('class') == None:
            td = table.find('td', class_='section')
            if td:
                header = td.text.strip()
                log.debug(f'Found header: {header!r}')
                return True
        return False

    @staticmethod
    def _handle_proposal(
        table: element.Tag, election: Election, **_
    ) -> Optional['Proposal']:
        if table.get('class') != ['proposal']:
            return None

        td = table.find(class_='division')
        log.debug(f'Parsing category from division: {td.text!r}')
        category = DistrictCategory.objects.get(
            name=string.capwords(td.text.split("PROPOSALS")[0])
        )
        log.info(f'Parsed {category!r}')

        td = table.find(class_='proposalTitle')
        log.debug(f'Parsing district from title: {td.text!r}')
        district = District.objects.get(
            category=category,
            name=string.capwords(td.text).split(category.name)[0].strip(),
        )
        log.info(f'Parsed {district}')

        td2 = table.find(class_='proposalText')
        log.debug(f'Parsing proposal from text: {td2.text!r}')
        proposal, _ = Proposal.objects.get_or_create(
            election=election,
            district=district,
            name=string.capwords(td.text),
            description=td2.text.strip(),
        )
        log.info(f'Parsed {proposal!r}')

        return proposal

    @staticmethod
    def build_mi_sos_url(election_id: int, precinct_id: int) -> str:
        assert election_id, "MI SOS election ID is missing"
        assert precinct_id, "MI SOS precinct ID is missing"
        base = 'https://webapps.sos.state.mi.us/MVIC/SampleBallot.aspx'
        params = f'd={precinct_id}&ed={election_id}'
        return f'{base}?{params}'


class Ballot(TimeStampedModel):
    """Full ballot bound to a particular polling location."""

    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    precinct = models.ForeignKey(Precinct, on_delete=models.CASCADE)

    website = models.ForeignKey(
        BallotWebsite, null=True, on_delete=models.SET_NULL
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
        return BallotWebsite.build_mi_sos_url(
            election_id=self.election.mi_sos_id,
            precinct_id=self.precinct.mi_sos_id,
        )


class BallotItem(TimeStampedModel):

    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    precinct = models.ForeignKey(
        Precinct, on_delete=models.CASCADE, null=True
    )  # TODO: remove null
    # TODO: Delete this
    district = models.ForeignKey(District, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    reference_url = models.URLField(blank=True, null=True)

    class Meta:
        abstract = True
        unique_together = ['election', 'district', 'name']

    def __str__(self):
        return self.name


# https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/ballot_measure_contest.html
# https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/ballot_measure_selection.html
# TODO: Considering adding selection options
class Proposal(BallotItem):
    """Ballot item with a boolean outcome."""


# https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/candidate_contest.html
# https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/candidate_selection.html
# TODO: Consider splitting this up to match VIP
class Position(BallotItem):
    """Ballot item selecting one ore more candidates."""

    seats = models.PositiveIntegerField(default=1)


# https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/candidate.html
class Candidate(TimeStampedModel):
    """Individual running for a particular position."""

    position = models.ForeignKey(Position, null=True, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    reference_url = models.URLField(blank=True, null=True)
    party = models.ForeignKey(
        Party, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        unique_together = ['position', 'name']

    def __str__(self) -> str:
        return f'{self.name} for {self.position}'
