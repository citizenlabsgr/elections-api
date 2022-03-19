# pylint: disable=unused-variable,unused-argument,expression-not-assigned


import pendulum
import pytest

from .. import models


@pytest.fixture
def voter():
    return models.Voter(
        first_name="Jane",
        last_name="Doe",
        birth_date=pendulum.parse("1985-06-19", tz="America/Detroit"),
        zip_code=12345,
    )


@pytest.fixture
def district_category():
    return models.DistrictCategory(name="County")


@pytest.fixture
def district(district_category):
    return models.District(name="Kent", category=district_category)


@pytest.fixture
def election():
    return models.Election(
        name="State Primary",
        date=pendulum.parse("2018-08-07", tz="America/Detroit"),
        mvic_id=676,
    )


@pytest.fixture
def website():
    return models.BallotWebsite(mvic_election_id=676, mvic_precinct_id=1828)


@pytest.fixture
def precinct(district):
    county = district
    jurisdiction = models.District(
        name="City of Grand Rapids",
        category=models.DistrictCategory(name="Jurisdiction"),
    )
    return models.Precinct(county=county, jurisdiction=jurisdiction, ward=1, number="9")


@pytest.fixture
def ballot(election, precinct):
    return models.Ballot(election=election, precinct=precinct)


def describe_voter():
    def describe_repr():
        def it_includes_all_info(expect, voter):
            expect(repr(voter)) == "<voter: Jane Doe, birth=1985-06-19, zip=12345>"

    def describe_str():
        def it_includes_full_name(expect, voter):
            expect(str(voter)) == "Jane Doe"

    def describe_birth_month():
        def is_parsed_from_date(expect, voter):
            expect(voter.birth_month) == 6

    def describe_birth_year():
        def is_parsed_from_date(expect, voter):
            expect(voter.birth_year) == 1985


def describe_registration_status():

    DATE = pendulum.parse("2021-08-09", tz="America/Detroit")

    def describe_message():
        @pytest.mark.parametrize(
            "registered, absentee, absentee_application_received, absentee_ballot_sent, absentee_ballot_received, message",
            [
                (
                    False,
                    False,
                    None,
                    None,
                    None,
                    "not registered to vote",
                ),
                (
                    True,
                    False,
                    None,
                    None,
                    None,
                    "registered to vote",
                ),
                (
                    True,
                    True,
                    None,
                    None,
                    None,
                    "registered to vote absentee",
                ),
                (
                    True,
                    True,
                    pendulum.parse("2021-08-10", tz="America/Detroit"),
                    None,
                    None,
                    "registered to vote absentee (application received on 2021-08-10)",
                ),
                (
                    True,
                    True,
                    pendulum.parse("2021-08-10", tz="America/Detroit"),
                    pendulum.parse("2021-08-11", tz="America/Detroit"),
                    None,
                    "registered to vote absentee and your ballot was mailed to you on 2021-08-11",
                ),
                (
                    True,
                    True,
                    pendulum.parse("2021-08-10", tz="America/Detroit"),
                    pendulum.parse("2021-08-11", tz="America/Detroit"),
                    pendulum.parse("2021-08-12", tz="America/Detroit"),
                    "registered to vote absentee and your ballot was received on 2021-08-12",
                ),
            ],
        )
        def permutations(
            expect,
            registered,
            absentee,
            absentee_application_received,
            absentee_ballot_sent,
            absentee_ballot_received,
            message,
        ):
            registration_status = models.RegistrationStatus(
                registered=registered,
                absentee=absentee,
                absentee_application_received=absentee_application_received,
                absentee_ballot_sent=absentee_ballot_sent,
                absentee_ballot_received=absentee_ballot_received,
            )
            expect(registration_status.message) == message


def describe_district_category():
    def describe_str():
        def it_includes_the_name(expect, district_category):
            expect(str(district_category)) == "County"


def describe_district():
    def describe_str():
        def it_includes_the_name(expect, district):
            expect(str(district)) == "Kent"


def describe_election():
    def describe_str():
        def it_includes_the_date(expect, election):
            expect(str(election)) == "State Primary | Tuesday, August 7, 2018"


def describe_precinct():
    def describe_str():
        def when_ward_and_precinct(expect, precinct):
            expect(
                str(precinct)
            ) == "Kent County, Michigan | City of Grand Rapids, Ward 1 Precinct 9"

        def when_ward_only(expect, precinct):
            precinct.number = ""
            expect(
                str(precinct)
            ) == "Kent County, Michigan | City of Grand Rapids, Ward 1 "

        def when_precinct_only(expect, precinct):
            precinct.ward = ""
            expect(
                str(precinct)
            ) == "Kent County, Michigan | City of Grand Rapids,  Precinct 9"


def describe_ballot_website():
    def describe_mvic_url():
        def it_includes_ids_from_election_and_precinct(expect, website):
            expect(
                website.mvic_url
            ) == "https://mvic.sos.state.mi.us/Voter/GetMvicBallot/1828/676/"


def describe_ballot():
    def describe_str():
        def it_includes_the_election_and_precinct(expect, ballot):
            expect(
                str(ballot)
            ) == "State Primary | Tuesday, August 7, 2018 | Kent County, Michigan | City of Grand Rapids, Ward 1 Precinct 9"


def describe_position():
    def describe_update_term():
        def it_sets_term_for_known_positions(expect, election):
            position = models.Position(name="United States Senator", election=election)
            position.update_term()
            expect(position.term) == "6 Year Term"
