from __future__ import annotations

import random
from datetime import timedelta
from typing import Any

import log
import pendulum
from django.conf import settings
from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel

from . import constants, exceptions, helpers


class DistrictCategory(TimeStampedModel):
    """Types of regions bound to ballot items."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    rank = models.IntegerField(
        default=0, help_text="Controls ballot item ordering", db_index=True
    )

    described = models.BooleanField(default=False, editable=False)

    class Meta:
        verbose_name_plural = "District Categories"
        ordering = ["name"]

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
        return f"{self.name} District"

    def update_described(self):
        self.described = bool(self.description)

    def save(self, *args, **kwargs):
        self.update_described()
        super().save(*args, **kwargs)


class District(TimeStampedModel):
    """Districts bound to ballot items."""

    category = models.ForeignKey(
        DistrictCategory, on_delete=models.CASCADE, db_index=True
    )
    name = models.CharField(max_length=100, db_index=True)
    population = models.PositiveIntegerField(blank=True, null=True, db_index=True)

    class Meta:
        unique_together = ["category", "name"]
        ordering = ["-population"]

    def __repr__(self) -> str:
        return f"<District: {self.name} ({self.category})>"

    def __str__(self) -> str:
        return self.name


class Election(TimeStampedModel):
    """Point in time where voters can cast opinions on ballot items."""

    name = models.CharField(max_length=100)
    date = models.DateField(db_index=True)

    active = models.BooleanField(default=True, db_index=True)
    reference_url = models.URLField(blank=True, null=True, verbose_name="Reference URL")

    mvic_id = models.PositiveIntegerField(verbose_name="MVIC ID", db_index=True)

    class Meta:
        unique_together = ["date", "name"]
        ordering = ["-date"]

    def __str__(self) -> str:
        return " | ".join(self.mvic_name)

    @property
    def mvic_name(self) -> list[str]:
        dt = pendulum.parse(self.date.isoformat())
        assert isinstance(dt, pendulum.DateTime)
        return [
            self.name,
            dt.format("dddd, MMMM D, YYYY"),
        ]

    @property
    def message(self) -> str:
        if self.date < timezone.now().date():
            return "next election"
        return f"{self.name} election on {self.date:%Y-%m-%d}"


class Precinct(TimeStampedModel):
    """Specific region where all voters share a ballot."""

    county = models.ForeignKey(
        District, related_name="counties", on_delete=models.CASCADE, db_index=True
    )
    jurisdiction = models.ForeignKey(
        District, related_name="jurisdictions", on_delete=models.CASCADE, db_index=True
    )
    ward = models.CharField(max_length=2, blank=True, db_index=True)
    number = models.CharField(max_length=3, blank=True, db_index=True)

    class Meta:
        unique_together = ["county", "jurisdiction", "ward", "number"]

    def __str__(self) -> str:
        return " | ".join(self.mvic_name)

    @property
    def mvic_name(self) -> list[str]:
        if self.ward and self.number:
            ward_precinct = f"Ward {self.ward} Precinct {self.number}"
        elif self.ward:
            # Extra space is intentional to match the MVIC website format
            ward_precinct = f"Ward {self.ward} "
        else:
            assert self.number, f"Ward and precinct are missing: pk={self.id}"
            # Extra space is intentional to match the MVIC website format
            ward_precinct = f" Precinct {self.number}"
        return [
            f"{self.county} County, Michigan",
            f"{self.jurisdiction}, {ward_precinct}",
        ]

    def get_county_district_label(self, district: str) -> str:
        return f"{self.county.name} County, {district}"

    def get_ward_label(self, ballot_item: dict) -> str:
        if self.ward:
            return f"{self.jurisdiction}, Ward {self.ward}"
        if district := ballot_item.get("district"):
            log.warn(f"Inferring ward from ballot item: {ballot_item}")
            assert "Ward" in district
            return f"{self.jurisdiction}, {district}"
        log.warn("Assuming jurisdiction does not have wards")
        assert self.number
        return f"{self.jurisdiction}, Precinct {self.number}"

    def get_precinct_label(self) -> str:
        if self.ward and self.number:
            ward_precinct = f"Ward {self.ward}, Precinct {self.number}"
        elif self.ward:
            ward_precinct = f"Ward {self.ward}"
        else:
            ward_precinct = f"Precinct {self.number}"
        return f"{self.jurisdiction}, {ward_precinct}"

    def save(self, *args, **kwargs):
        self.ward = self.ward if self.ward.strip("0") else ""
        self.number = self.number if self.number.strip("0") else ""
        assert self.mvic_name
        super().save(*args, **kwargs)


class RegistrationStatus(models.Model):
    """Status of a particular voter's registration."""

    registered = models.BooleanField()
    ballot = models.BooleanField(null=True, blank=True)
    ballot_url = models.URLField(null=True, blank=True)
    ballots: list[Ballot] = []  # not M2M because model is never saved

    absentee = models.BooleanField(null=True, blank=True)
    absentee_application_received = models.DateField(null=True)
    absentee_ballot_sent = models.DateField(null=True)
    absentee_ballot_received = models.DateField(null=True)

    polling_location = models.JSONField(null=True, blank=True)
    dropbox_locations = models.JSONField(null=True, blank=True)
    recently_moved = models.BooleanField(null=True, blank=True)

    precinct = models.ForeignKey(Precinct, null=True, on_delete=models.SET_NULL)

    districts: list[District] = []  # not M2M because model is never saved

    def __init__(self, *args, districts=None, **kwargs):
        super().__init__(*args, **kwargs)

        if self.ballot_url:
            *_, precinct_id, election_id = self.ballot_url.strip("/").split("/")
            self.ballots = Ballot.objects.filter(
                website__mvic_election_id=election_id,
                website__mvic_precinct_id=precinct_id,
            )

        self.districts = districts or []

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        if self.registered:
            text = "registered to vote"
            if self.absentee_application_received:
                text += " absentee"
            elif self.absentee:
                text += " and applied for an absentee ballot"
            if self.absentee_ballot_received:
                text += f" and your ballot was received on {self.absentee_ballot_received:%Y-%m-%d}"
            elif self.absentee_ballot_sent:
                text += f" and your ballot was mailed to you on {self.absentee_ballot_sent:%Y-%m-%d}"
            elif self.absentee_application_received:
                text += f" (application received on {self.absentee_application_received:%Y-%m-%d})"
        else:
            text = "not registered to vote"
        return text

    def save(self, *args, **kwargs):
        raise NotImplementedError


class Voter(models.Model):
    """Data needed to look up Michigan voter registration status."""

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField()
    zip_code = models.CharField(max_length=10)

    def __repr__(self) -> str:
        dt = pendulum.parse(str(self.birth_date))
        assert isinstance(dt, pendulum.Date)
        birth = dt.format("YYYY-MM-DD")
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

        if not data["registered"]:
            return RegistrationStatus(registered=False)

        districts: list[District] = []
        county = jurisdiction = None

        for category_name, district_name in sorted(data["districts"].items()):
            if not district_name:
                log.debug(f"Skipped blank district: {category_name}")
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

        precinct, _created = Precinct.objects.get_or_create(
            county=county,
            jurisdiction=jurisdiction,
            ward=data["districts"]["Ward"],
            number=data["districts"]["Precinct"],
        )

        status = RegistrationStatus(  # type: ignore[misc]
            registered=data["registered"],
            ballot=data["ballot"],
            ballot_url=data["ballot_url"],
            absentee=data["absentee"],
            absentee_application_received=data["absentee_dates"][
                "Application Received"
            ],
            absentee_ballot_sent=data["absentee_dates"]["Ballot Sent"],
            absentee_ballot_received=data["absentee_dates"]["Ballot Received"],
            polling_location=list(data["polling_location"].values()),
            dropbox_locations=data["dropbox_locations"],
            recently_moved=data["recently_moved"],
            precinct=precinct,
            districts=districts,
        )

        return status

    def fingerprint(self, election: Election, status: RegistrationStatus) -> str:
        election_string = str(election.pk)
        voter_string = repr(self)
        status_string = status.message + (
            status.ballot_url if status.ballot_url else ""
        )
        return "-".join(
            [
                str(settings.API_CACHE_KEY) + election_string,
                str(sum(ord(c) for c in voter_string)),
                str(sum(ord(c) for c in status_string)),
            ]
        )

    def describe(self, election: Election, status: RegistrationStatus):
        message = f"{self} is {status.message} for the {election.message}"
        if status.ballot_url and "your ballot" not in message:
            message += " and a sample ballot is available"
        return message + "."

    def save(self, *args, **kwargs):
        raise NotImplementedError


class Party(TimeStampedModel):
    """Affiliation for a particular candidate."""

    name = models.CharField(max_length=50, unique=True, editable=False, db_index=True)
    color = models.CharField(max_length=7, blank=True, editable=False)

    class Meta:
        verbose_name_plural = "Parties"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BallotWebsite(models.Model):
    """Raw HTML of potential ballot from the MVIC website."""

    mvic_election_id = models.PositiveIntegerField(
        verbose_name="MVIC Election ID", db_index=True
    )
    mvic_precinct_id = models.PositiveIntegerField(
        verbose_name="MVIC Precinct ID", db_index=True
    )

    mvic_html = models.TextField(blank=True, editable=False)

    fetched = models.BooleanField(default=False, editable=False)
    valid = models.BooleanField(null=True, editable=False)
    parsed = models.BooleanField(default=False, editable=False)

    data = models.JSONField(null=True, editable=False)
    data_count = models.IntegerField(default=-1, editable=False)

    last_fetch = models.DateTimeField(null=True, editable=False)
    last_validate = models.DateTimeField(null=True, editable=False)
    last_scrape = models.DateTimeField(null=True, editable=False)
    last_convert = models.DateTimeField(null=True, editable=False)
    last_parse = models.DateTimeField(null=True, editable=False)

    class Meta:
        unique_together = ["mvic_election_id", "mvic_precinct_id"]

    def __str__(self) -> str:
        return self.mvic_url

    @property
    def mvic_url(self) -> str:
        return helpers.build_mvic_url(
            election_id=self.mvic_election_id, precinct_id=self.mvic_precinct_id
        )

    @property
    def stale(self) -> bool:
        if not self.last_fetch:
            log.debug(f"Ballot has never been scraped: {self}")
            return True

        hours = 4
        age = timezone.now() - self.last_fetch
        if age < timedelta(hours=hours):
            log.debug(f"Ballot was scraped in the last {hours} hours: {self}")
            return False

        if self.last_fetch < constants.SCRAPER_LAST_UPDATED:
            log.info(f"Scraping logic is newer than last scrape: {self}")
            return True

        hours = 18
        age = timezone.now() - self.last_fetch
        if age < timedelta(hours=hours):
            log.debug(f"Ballot was scraped in the last {hours} hours: {self}")
            return False

        age_in_days = age.total_seconds() / 3600 / 24
        weight = age_in_days / 14  # fetch once per week on average
        log.debug(f"Ballot was scraped {round(age_in_days, 1)} days ago: {self}")

        return weight > random.random()

    def fetch(self) -> None:
        """Fetch ballot HTML from the URL."""
        self.mvic_html = helpers.fetch_ballot_html(self.mvic_url)

        self.fetched = True
        self.last_fetch = timezone.now()

        self.save()

    def validate(self) -> bool:
        """Determine if fetched HTML contains ballot information."""
        log.info(f"Validating ballot HTML: {self}")
        assert self.mvic_html, f"Ballot URL has not been fetched: {self}"

        html = self.mvic_html.lower()
        if "not available at this time" in html:
            log.warn("Ballot HTML is not available at this time")
            self.valid = False
        elif "county, michigan" not in html:
            log.warn("Ballot HTML missing precinct information")
            self.valid = False
        else:
            log.info("Ballot HTML contains precinct information")
            self.valid = True
            self.last_validate = timezone.now()

        self.save()

        return self.valid

    def scrape(self) -> int:
        """Scrape ballot data from the HTML."""
        log.info(f"Scraping data from ballot: {self}")
        assert self.valid, f"Ballot HTML has not been validated: {self}"

        data: dict[str, Any] = {}
        data["election"] = helpers.parse_election(self.mvic_html)
        data["precinct"] = helpers.parse_precinct(self.mvic_html, self.mvic_url)
        data["ballot"] = {}

        data_count = helpers.parse_ballot(self.mvic_html, data["ballot"])
        log.info(f"Ballot HTML contains {data_count} parsed item(s)")
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
        log.info(f"Converting to a ballot: {self}")
        assert self.data, f"Ballot data has not been scraped: {self}"

        election = self._get_election()
        precinct = self._get_precinct()
        ballot = self._get_ballot(election, precinct)
        self.last_convert = timezone.now()

        self.save()

        return ballot

    def _get_election(self) -> Election:
        election_name, election_date = self.data["election"]

        election, created = Election.objects.get_or_create(
            mvic_id=self.mvic_election_id,
            defaults={"name": election_name, "date": pendulum.date(*election_date)},
        )
        if created:
            log.info(f"Created election: {election}")

        assert (
            election.name == election_name
        ), f"Election {election.mvic_id} name changed: {election_name}"

        return election

    def _get_precinct(self) -> Precinct:
        county_name, jurisdiction_name, ward, number = self.data["precinct"]

        county, created = District.objects.get_or_create(
            category=DistrictCategory.objects.get(name="County"), name=county_name
        )
        if created:
            log.info(f"Created district: {county}")

        jurisdiction, created = District.objects.get_or_create(
            category=DistrictCategory.objects.get(name="Jurisdiction"),
            name=jurisdiction_name,
        )
        if created:
            log.info(f"Created district: {jurisdiction}")

        assert self.mvic_precinct_id
        precinct, created = Precinct.objects.get_or_create(
            county=county, jurisdiction=jurisdiction, ward=ward, number=number
        )
        if created:
            log.info(f"Created precinct: {precinct}")

        return precinct

    def _get_ballot(self, election: Election, precinct: Precinct) -> Ballot:
        ballot, created = Ballot.objects.get_or_create(
            website=self, defaults=dict(election=election, precinct=precinct)
        )
        if created:
            log.info(f"Created ballot: {ballot}")
        return ballot


class Ballot(TimeStampedModel):
    """Full ballot bound to a particular polling location."""

    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    precinct = models.ForeignKey(Precinct, on_delete=models.CASCADE)
    website = models.OneToOneField(BallotWebsite, on_delete=models.CASCADE)

    class Meta:
        ordering = ["election__date"]

    def __str__(self) -> str:
        return " | ".join(self.mvic_name)

    @property
    def mvic_name(self) -> list[str]:
        return self.election.mvic_name + self.precinct.mvic_name

    @property
    def mvic_url(self) -> str | None:
        if self.website:
            return self.website.mvic_url
        return None

    @property
    def stale(self) -> bool:
        assert self.website

        if not self.website.last_parse:
            log.debug("Ballot has never been parsed")
            return True

        if self.website.last_parse < constants.PARSER_LAST_UPDATED:
            log.info(f"Parsing logic is newer than last scrape: {self.website}")
            return True

        age = timezone.now() - self.website.last_parse
        if age < timedelta(hours=23):
            log.debug("Ballot was parsed in the last day")
            return False

        return True

    def parse(self) -> int:
        log.info(f"Parsing ballot: {self}")
        assert (
            self.website and self.website.data
        ), f"Ballot website has not been converted: {self}"

        count = 0
        for section_name, section_data in self.website.data["ballot"].items():
            section_parser = getattr(self, "_parse_" + section_name.replace(" ", "_"))
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

    def _parse_partisan_section(self, data, section=""):
        assert self.website

        for category_name, positions_data in data.items():
            for position_data in positions_data:
                category = district = None
                position_name = position_data["name"]

                if category_name in {
                    "Presidential",
                    "State",
                    "State Board",
                    "State Boards",
                }:
                    district = District.objects.get(name="Michigan")
                elif category_name in {
                    "City",
                    "Township",
                }:
                    district = self.precinct.jurisdiction
                elif category_name in {
                    "Ward",
                }:
                    category = DistrictCategory.objects.get(name=category_name)
                elif category_name in {
                    "Congressional",
                    "Legislative",
                    "County",
                    "Delegate",
                }:
                    pass  # district parsed based on position name
                else:
                    raise exceptions.UnhandledData(
                        f"Unhandled category {category_name!r} on {self.website.mvic_url}"
                    )

                if category and category.name == "Ward":
                    district, created = District.objects.get_or_create(
                        category=category,
                        name=self.precinct.get_ward_label(position_data),
                    )
                    if created:
                        log.info(f"Created district: {district}")

                if district is None:
                    if position_name in {"United States Senator"}:
                        district = District.objects.get(name="Michigan")
                    elif position_name in {"Representative in Congress"}:
                        category = DistrictCategory.objects.get(name="US Congress")
                        district, created = District.objects.get_or_create(
                            category=category, name=position_data["district"]
                        )
                        if created:
                            log.info(f"Created district: {district}")
                    elif position_name in {"State Senator"}:
                        category = DistrictCategory.objects.get(name="State Senate")
                        district, created = District.objects.get_or_create(
                            category=category, name=position_data["district"]
                        )
                        if created:
                            log.info(f"Created district: {district}")
                    elif position_name in {"Representative in State Legislature"}:
                        category = DistrictCategory.objects.get(name="State House")
                        district, created = District.objects.get_or_create(
                            category=category, name=position_data["district"]
                        )
                        if created:
                            log.info(f"Created district: {district}")

                    elif position_name in {"County Commissioner"}:
                        category = DistrictCategory.objects.get(name=position_name)
                        district, created = District.objects.get_or_create(
                            category=category,
                            name=self.precinct.get_county_district_label(
                                position_data["district"]
                            ),
                        )
                        if created:
                            log.info(f"Created district: {district}")
                    elif position_name in {"Delegate to County Convention"}:
                        category = DistrictCategory.objects.get(name="Precinct")
                        district, created = District.objects.get_or_create(
                            category=category,
                            name=self.precinct.get_precinct_label(),
                        )
                        if created:
                            log.info(f"Created district: {district}")
                    elif category_name in {"County"}:
                        district = self.precinct.county
                    else:
                        raise exceptions.UnhandledData(
                            f"Unhandled position {position_name!r} on {self.website.mvic_url}"
                        )

                default_term = constants.TERMS.get(position_data["name"], "")
                position, created = Position.objects.get_or_create(
                    election=self.election,
                    district=district,
                    name=position_data["name"],
                    term=position_data["term"] or default_term,
                    seats=position_data["seats"] or 1,
                    section=section,
                )
                if created:
                    log.info(f"Created position: {position}")
                position.ballots.add(self)
                position.precincts.add(self.precinct)
                position.save()
                yield position

                for candidate_data in position_data["candidates"]:
                    candidate_name = candidate_data["name"]

                    if candidate_name in {"Uncommitted"}:
                        log.debug(f"Skipped placeholder candidate: {candidate_name}")
                        continue

                    if candidate_data["party"] is None:
                        raise exceptions.UnhandledData(
                            f"Expected party for {candidate_name!r} on {self.website.mvic_url}"
                        )

                    party = Party.objects.get(name=candidate_data["party"])
                    candidate, created = Candidate.objects.update_or_create(
                        position=position,
                        name=candidate_name,
                        defaults={
                            "party": party,
                            "reference_url": candidate_data["finance_link"],
                        },
                    )
                    if created:
                        log.info(f"Created candidate: {candidate}")
                    yield candidate

    def _parse_nonpartisan_section(self, data: dict):
        assert self.website

        for category_name, positions_data in data.items():
            for position_data in positions_data:
                category = district = None
                position_name = position_data["name"]

                if category_name in {
                    "City",
                    "City Special Primary",
                    "City Special General",
                    "Township",
                    "Village",
                    "Authority",
                    "Metropolitan",
                }:
                    if position_data["district"]:
                        category = self.precinct.jurisdiction.category
                    else:
                        district = self.precinct.jurisdiction
                elif category_name in {
                    "Community College",
                    "Local School",
                    "Intermediate School",
                    "District Library",
                    "Library",
                    "Ward",
                }:
                    category = DistrictCategory.objects.get(name=category_name)
                elif category_name in {"Judicial"}:
                    pass  # district will be parsed based on position name
                else:
                    raise exceptions.UnhandledData(
                        f"Unhandled category {category_name!r} on {self.website.mvic_url}"
                    )

                if category and category.name == "Ward":
                    district, created = District.objects.get_or_create(
                        category=category,
                        name=self.precinct.get_ward_label(position_data),
                    )
                    if created:
                        log.info(f"Created district: {district}")

                if district is None:
                    if category is None:
                        if position_name in {"Justice of Supreme Court"}:
                            district = District.objects.get(name="Michigan")
                        elif position_name in {"Judge of Court of Appeals"}:
                            category = DistrictCategory.objects.get(
                                name="Court of Appeals"
                            )
                        elif position_name in {"Judge of Municipal Court"}:
                            category = DistrictCategory.objects.get(
                                name="Municipal Court"
                            )
                        elif position_name in {
                            "Judge of Probate Court",
                            "Judge of Probate District Court",
                        }:
                            category = DistrictCategory.objects.get(
                                name="Probate Court"
                            )
                        elif position_name in {"Judge of Circuit Court"}:
                            category = DistrictCategory.objects.get(
                                name="Circuit Court"
                            )
                        elif position_name in {"Judge of District Court"}:
                            category = DistrictCategory.objects.get(
                                name="District Court"
                            )
                        else:
                            raise exceptions.UnhandledData(
                                f"Unhandled position {position_name!r} on {self.website.mvic_url}"
                            )

                    if position_data["district"]:
                        district, created = District.objects.get_or_create(
                            category=category, name=position_data["district"]
                        )
                        if created:
                            log.info(f"Created district: {district}")
                    elif district is None:
                        log.warn(
                            f"Ballot {self.website.mvic_url} missing district: {position_data}"
                        )
                        district = self.precinct.jurisdiction

                parts = [position_data["type"] or "", position_data["term"] or ""]
                position, created = Position.objects.get_or_create(
                    election=self.election,
                    district=district,
                    name=position_data["name"],
                    term=(", ".join(parts)).strip(", "),
                    seats=position_data["seats"] or 1,
                )
                if created:
                    log.info(f"Created position: {position}")
                position.section = "Nonpartisan"
                position.ballots.add(self)
                position.precincts.add(self.precinct)
                position.save()
                yield position

                for candidate_data in position_data["candidates"]:
                    assert candidate_data["party"] is None
                    party = Party.objects.get(name="Nonpartisan")
                    candidate, created = Candidate.objects.update_or_create(
                        position=position,
                        name=candidate_data["name"],
                        defaults={
                            "party": party,
                            "reference_url": candidate_data["finance_link"],
                        },
                    )
                    if created:
                        log.info(f"Created candidate: {candidate}")
                    yield candidate

    def _parse_proposal_section(self, data):
        assert self.website

        for category_name, proposals_data in data.items():
            category = district = None

            if category_name in {
                "State",
            }:
                district = District.objects.get(name="Michigan")
            elif category_name in {
                "County",
            }:
                district = self.precinct.county
            elif category_name in {
                "City",
                "Township",
                "Village",
                "Authority",
                "Authority (Custom Region)",
                "Metropolitan",
            }:
                district = self.precinct.jurisdiction
            elif category_name in {
                "Community College",
                "Intermediate School",
                "Local School",
                "District Library",
                "Ward",
            }:
                category = DistrictCategory.objects.get(name=category_name)
            else:
                raise exceptions.UnhandledData(
                    f"Unhandled category {category_name!r} on {self.website.mvic_url}"
                )

            for proposal_data in proposals_data:
                if category and category.name == "Ward":
                    district, created = District.objects.get_or_create(
                        category=category,
                        name=self.precinct.get_ward_label(proposal_data),
                    )
                    if created:
                        log.info(f"Created district: {district}")

                if district is None:
                    assert category, f"Expected category: {proposals_data}"

                    possible_category_names = [category.name]
                    if category.name == "District Library":
                        possible_category_names.extend(
                            [
                                "Public Library",
                                "Community Library",
                                "Library District",
                                "Library",
                            ]
                        )
                    elif category.name == "Community College":
                        possible_category_names.extend(
                            [
                                "College",
                            ]
                        )
                    elif category.name == "Local School":
                        possible_category_names.extend(
                            [
                                "Public Schools",
                                "Area Schools",
                                "Area School District",
                                "Public School",
                                "Community Schools",
                                "Community School District",
                                "Community School",
                                "Consolidated Schools District",
                                "Consolidated School",
                                "School District",
                                "Area School System",
                                "Rural Agricultural School",
                                "S/D",  # e.g. Hagar Township S/D #6
                                "Schools",
                                "District",
                                "School",
                            ]
                        )
                    elif category.name == "Intermediate School":
                        possible_category_names.extend(
                            [
                                "Regional Education Service Agency",
                                "Regional Educational Service Agency",
                                "Regional Education Service",
                                "Area Educational Service Agency",
                                "Educational Service",
                            ]
                        )

                    original_exception = None
                    for category_name in possible_category_names:
                        try:
                            district_name = helpers.parse_district_from_proposal(
                                category_name,
                                proposal_data["text"],
                                self.website.mvic_url,
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
                        log.info(f"Created district: {district}")

                if proposal_data["text"] is None:
                    raise exceptions.MissingData(
                        f"Proposal text missing on {self.website.mvic_url}"
                    )

                proposal, created = Proposal.objects.update_or_create(
                    election=self.election,
                    district=district,
                    name=proposal_data["title"],
                    defaults={"description": proposal_data["text"]},
                )
                if created:
                    log.info(f"Created proposal: {proposal}")
                proposal.ballots.add(self)
                proposal.precincts.add(self.precinct)
                proposal.save()
                yield proposal


class BallotItem(TimeStampedModel):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, db_index=True)
    district = models.ForeignKey(
        District, null=True, on_delete=models.CASCADE, db_index=True
    )
    precincts = models.ManyToManyField(Precinct)  # type: ignore[var-annotated]
    ballots = models.ManyToManyField(Ballot)  # type: ignore[var-annotated]

    name = models.CharField(max_length=500, db_index=True)
    description = models.TextField(blank=True)
    reference_url = models.URLField(blank=True, null=True, verbose_name="Reference URL")

    class Meta:
        abstract = True


class Proposal(BallotItem):
    """Ballot item with a boolean outcome."""

    class Meta:
        unique_together = ["election", "district", "name"]
        ordering = ["name"]

    def __str__(self):
        return self.name


class Position(BallotItem):
    """Ballot item selecting one ore more candidates."""

    term = models.CharField(max_length=200, blank=True, db_index=True)
    seats = models.PositiveIntegerField(default=1, blank=True)
    section = models.CharField(max_length=50, blank=True)

    described = models.BooleanField(default=False, editable=False)

    class Meta:
        unique_together = [
            "election",
            "section",
            "district",
            "name",
            "term",
            "seats",
        ]
        ordering = ["name", "seats"]

    def __str__(self):
        if self.term:
            return f"{self.name} ({self.term})"
        return self.name

    def update_term(self):
        self.term = self.term or constants.TERMS.get(self.name, "")

    def update_described(self):
        self.described = bool(self.description)

    def save(self, *args, **kwargs):
        self.update_described()
        self.update_term()
        super().save(*args, **kwargs)


class Candidate(TimeStampedModel):
    """Individual running for a particular position."""

    position = models.ForeignKey(
        Position, null=True, on_delete=models.CASCADE, related_name="candidates"
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    reference_url = models.URLField(blank=True, null=True, verbose_name="Reference URL")
    party = models.ForeignKey(Party, blank=True, null=True, on_delete=models.SET_NULL)
    nomination = models.ForeignKey(
        Party,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="nominations",
        help_text="Party that nominated the candidate for a nonpartisan position",
    )

    class Meta:
        unique_together = ["position", "name"]
        ordering = ["party__name", "nomination__name", "name"]

    def __str__(self) -> str:
        return f"{self.name} for {self.position}"

    def clean(self):
        if self.nomination:
            assert (
                self.party and self.party.name == "Nonpartisan"
            ), f"Candidates with nominations must be nonpartisan: {self}"
