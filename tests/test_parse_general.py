# pylint: disable=unused-variable,unused-argument

from types import SimpleNamespace

import pendulum
import pytest

from elections import models


@pytest.fixture
def constants(db):
    constants = SimpleNamespace()

    # Elections

    constants.election, _ = models.Election.objects.get_or_create(
        name="State General",
        date=pendulum.parse("2018-08-07", tz='America/Detroit'),
        mi_sos_id=676,
    )

    # Parties

    models.Party.objects.get_or_create(name="Republican")
    models.Party.objects.get_or_create(name="Democratic")
    models.Party.objects.get_or_create(name="Libertarian")
    models.Party.objects.get_or_create(name="U.S. Taxpayers")
    models.Party.objects.get_or_create(name="Green")
    models.Party.objects.get_or_create(name="Natural Law")
    models.Party.objects.get_or_create(name="Nonpartisan")
    models.Party.objects.get_or_create(name="No Party Affiliation")
    models.Party.objects.get_or_create(name="Working Class")

    # Categories

    state, _ = models.DistrictCategory.objects.get_or_create(name="State")
    constants.county, _ = models.DistrictCategory.objects.get_or_create(
        name="County"
    )
    constants.jurisdiction, _ = models.DistrictCategory.objects.get_or_create(
        name="Jurisdiction"
    )
    for name in {
        "City",
        "US Congress",
        "State Senate",
        "State House",
        "Circuit Court",
        "Precinct",
        "Local School",
        "Township",
        "District Library",
        "Intermediate School",
        "Court of Appeals",
        "Probate Court",
        "District Court",
        "Community College",
    }:
        models.DistrictCategory.objects.get_or_create(name=name)

    # Districts

    models.District.objects.get_or_create(category=state, name="Michigan")

    return constants


def describe_ballot_website():
    def describe_parse():
        def with_county_proposal(expect, constants):
            models.Precinct.objects.get_or_create(
                county=models.District.objects.get_or_create(
                    category=constants.county, name="Kent"
                )[0],
                jurisdiction=models.District.objects.get_or_create(
                    category=constants.jurisdiction,
                    name="City of Grand Rapids",
                )[0],
                ward='1',
                number='9',
                mi_sos_id=1828,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=constants.election.mi_sos_id,
                mi_sos_precinct_id=1828,
            )
            website.fetch()

            expect(len(website.parse())) == 24
