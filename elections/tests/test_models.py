# pylint: disable=unused-variable,unused-argument,expression-not-assigned


import pendulum
import pytest

from .. import models


@pytest.fixture
def voter():
    return models.Voter(
        first_name="Jane",
        last_name="Doe",
        birth_date=pendulum.parse("1985-06-19", tz='America/Detroit'),
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
        date=pendulum.parse("2018-08-07", tz='America/Detroit'),
        mi_sos_id=676,
    )


@pytest.fixture
def website():
    return models.BallotWebsite(
        mi_sos_election_id=676, mi_sos_precinct_id=1828
    )


@pytest.fixture
def precinct(district):
    county = district
    jurisdiction = models.District(
        name="City of Grand Rapids",
        category=models.DistrictCategory(name="Jurisdiction"),
    )
    return models.Precinct(
        county=county,
        jurisdiction=jurisdiction,
        ward=1,
        number='9',
        mi_sos_id=1828,
    )


@pytest.fixture
def ballot(election, precinct):
    return models.Ballot(election=election, precinct=precinct)


def describe_voter_identity():
    def describe_repr():
        def it_includes_all_info(expect, voter):
            expect(
                repr(voter)
            ) == "<voter: Jane Doe, birth=1985-06-19, zip=12345>"

    def describe_str():
        def it_includes_full_name(expect, voter):
            expect(str(voter)) == "Jane Doe"

    def describe_birth_month():
        def is_parsed_from_date(expect, voter):
            expect(voter.birth_month) == 6

    def describe_birth_year():
        def is_parsed_from_date(expect, voter):
            expect(voter.birth_year) == 1985


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
            precinct.number = ''
            expect(
                str(precinct)
            ) == "Kent County, Michigan | City of Grand Rapids, Ward 1 "

        def when_precinct_only(expect, precinct):
            precinct.ward = ''
            expect(
                str(precinct)
            ) == "Kent County, Michigan | City of Grand Rapids,  Precinct 9"


def describe_ballot_website():
    def describe_mi_sos_url():
        def it_includes_ids_from_election_and_precinct(expect, website):
            expect(
                website.mi_sos_url
            ) == "https://mvic.sos.state.mi.us/Voter/GetMvicBallot/1828/676/"


def describe_ballot():
    def describe_str():
        def it_includes_the_election_and_precinct(expect, ballot):
            expect(
                str(ballot)
            ) == "State Primary | Tuesday, August 7, 2018 | Kent County, Michigan | City of Grand Rapids, Ward 1 Precinct 9"
