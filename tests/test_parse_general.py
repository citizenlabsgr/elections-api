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

        def with_local_school_position(expect, constants):
            models.Precinct.objects.get_or_create(
                county=models.District.objects.get_or_create(
                    category=constants.county, name="Kent"
                )[0],
                jurisdiction=models.District.objects.get_or_create(
                    category=constants.jurisdiction,
                    name="City of Grand Rapids",
                )[0],
                ward='1',
                number='23',
                mi_sos_id=1848,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=constants.election.mi_sos_id,
                mi_sos_precinct_id=1848,
            )
            website.fetch()

            expect(len(website.parse())) == 26

        def with_city_position(expect, constants):
            models.Precinct.objects.get_or_create(
                county=models.District.objects.get_or_create(
                    category=constants.county, name="Kent"
                )[0],
                jurisdiction=models.District.objects.get_or_create(
                    category=constants.jurisdiction, name="City of Wyoming"
                )[0],
                ward='1',
                number='6',
                mi_sos_id=6009,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=constants.election.mi_sos_id,
                mi_sos_precinct_id=6009,
            )
            website.fetch()

            expect(len(website.parse())) == 28

        def with_duplicate_positions(expect, constants):
            models.Precinct.objects.get_or_create(
                county=models.District.objects.get_or_create(
                    category=constants.county, name="Livingston"
                )[0],
                jurisdiction=models.District.objects.get_or_create(
                    category=constants.jurisdiction, name="Hamburg Township"
                )[0],
                ward='',
                number='3',
                mi_sos_id=2,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=constants.election.mi_sos_id,
                mi_sos_precinct_id=2,
            )
            website.fetch()

            expect(len(website.parse())) == 24

        def with_recall_election(expect, constants):
            models.Precinct.objects.get_or_create(
                county=models.District.objects.get_or_create(
                    category=constants.county, name="Cheboygan"
                )[0],
                jurisdiction=models.District.objects.get_or_create(
                    category=constants.jurisdiction, name="Inverness Township"
                )[0],
                ward='',
                number='1',
                mi_sos_id=19,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=constants.election.mi_sos_id,
                mi_sos_precinct_id=19,
            )
            website.fetch()

            expect(len(website.parse())) == 28
