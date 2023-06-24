# pylint: disable=unused-variable,unused-argument,expression-not-assigned


import log
import pendulum
import pytest
import time_machine

from .. import models


@pytest.fixture
def voter():
    return models.Voter(
        first_name="Jane",
        last_name="Doe",
        birth_date=pendulum.parse("1985-06-19", tz="America/Detroit"),  # type: ignore
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
        date=pendulum.parse("2018-08-07", tz="America/Detroit").date(),  # type: ignore
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

    def describe_message():
        @time_machine.travel("2018-08-06")
        def without_sample_ballot(expect, voter, election):
            status = models.RegistrationStatus(registered=True)
            message = voter.describe(election, status)
            expect(
                message
            ) == "Jane Doe is registered to vote for the State Primary election on 2018-08-07."

        @time_machine.travel("2018-08-06")
        def with_sample_ballot(expect, voter, election):
            status = models.RegistrationStatus(
                registered=True, ballot_url="http://example.com"
            )
            message = voter.describe(election, status)
            expect(
                message
            ) == "Jane Doe is registered to vote for the State Primary election on 2018-08-07 and a sample ballot is available."

        @time_machine.travel("2018-08-06")
        def with_sample_ballot_and_absentee(expect, voter, election):
            status = models.RegistrationStatus(
                registered=True,
                ballot_url="http://example.com",
                absentee_ballot_sent=pendulum.parse("2021-08-09", tz="America/Detroit"),  # type: ignore
            )
            message = voter.describe(election, status)
            expect(
                message
            ) == "Jane Doe is registered to vote and your ballot was mailed to you on 2021-08-09 for the State Primary election on 2018-08-07."

        @time_machine.travel("2018-08-08")
        def with_past_election(expect, voter, election):
            status = models.RegistrationStatus(registered=True)
            message = voter.describe(election, status)
            expect(message) == "Jane Doe is registered to vote for the next election."


def describe_registration_status():
    DATE = pendulum.parse("2021-08-09", tz="America/Detroit")

    def describe_message():
        @pytest.mark.parametrize(
            (
                "registered",
                "absentee",
                "absentee_application_received",
                "absentee_ballot_sent",
                "absentee_ballot_received",
                "message",
            ),
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
                    "registered to vote and applied for an absentee ballot",
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

    def describe_scrape():
        @pytest.mark.vcr
        @pytest.mark.django_db
        def it_removes_extra_line_breaks(expect, website):
            website = models.BallotWebsite(mvic_election_id=689, mvic_precinct_id=4542)
            website.fetch()
            website.validate()
            website.scrape()

            actual = website.data["ballot"]["proposal section"]["Local School"][0][
                "text"
            ]
            expected = """
Shall Coopersville Area Public Schools, Ottawa and Muskegon Counties, Michigan, borrow the sum of not to exceed Forty-Two Million Nine Hundred Thousand Dollars ($42,900,000) and issue its general obligation unlimited tax bonds therefor, in one or more series, for the purpose of:

erecting, furnishing, and equipping additions to West Elementary School and Coopersville High School; remodeling, furnishing and refurnishing, and equipping and re-equipping school facilities; acquiring and installing instructional technology and instructional technology equipment for school facilities; erecting a storage building; purchasing school buses; and remodeling, preparing, developing, improving, and equipping athletic facilities, athletic fields, playgrounds and sites?
The following is for informational purposes only:

The estimated millage that will be levied for the proposed bonds in 2022, under current law, is 1.24 mills ($1.24 on each $1,000 taxable valuation), for a -0- mill net increase over the prior year's levy. The maximum number of years the bonds of any series may be outstanding, exclusive of any refunding, is thirty (30) years. The estimated simple average annual millage anticipated to be required to retire this bond debt is 4.08 mills ($4.08 on each $1,000 of taxable valuation).

The school district expects to borrow from the State School Bond Qualification and Loan Program to pay debt service on these bonds. The estimated total principal amount of that borrowing is $8,278,037 and the estimated total interest to be paid thereon is $13,155,210. The estimated duration of the millage levy associated with that borrowing is 32 years and the estimated computed millage rate for such levy is 8.99 mills. The estimated computed millage rate may change based on changes in certain circumstances.

The total amount of qualified bonds currently outstanding is $51,340,000. The total amount of qualified loans currently outstanding is approximately $12,640,391.

(Pursuant to State law, expenditure of bond proceeds must be audited and the proceeds cannot be used for repair or maintenance costs, teacher, administrator or employee salaries, or other operating expenses.)
""".strip()
            log.info(f"{actual=}")
            log.info(f"{expected=}")
            expect(actual) == expected

        @pytest.mark.vcr
        @pytest.mark.django_db
        def it_removes_mce_formatting(expect, website):
            website = models.BallotWebsite(mvic_election_id=694, mvic_precinct_id=2300)
            website.fetch()
            website.validate()
            website.scrape()

            actual = website.data["ballot"]["proposal section"]["Local School"][0][
                "text"
            ]
            expected = """
Shall Central Montcalm Public School, Montcalm and Ionia Counties, Michigan, borrow the sum of not to exceed Forty-Seven Million Five Hundred Thousand Dollars ($47,500,000) and issue its general obligation unlimited tax bonds therefor, in one or more series, for the purpose of:

erecting, furnishing, and equipping an addition to the elementary school building; erecting, furnishing, and equipping additions to the middle school/high school building; remodeling, furnishing and refurnishing, and equipping and re-equipping school buildings and facilities; acquiring and installing instructional technology in school buildings; purchasing school buses; erecting, furnishing, and equipping restroom and team room buildings and a press box; and preparing, developing, improving, and equipping playgrounds, athletic fields and facilities, and sites?

The following is for informational purposes only:

The estimated millage that will be levied for the proposed bonds in 2024, is 2.74 mills ($2.74 on each $1,000 of taxable valuation) for a -0- mill net increase over the prior year's levy. The maximum number of years the bonds of any series may be outstanding, exclusive of any refunding, is twenty-six (26) years. The estimated simple average annual millage anticipated to be required to retire this bond debt is 5.44 mills ($5.44 on each $1,000 of taxable valuation).

The school district does not expect to borrow from the State to pay debt service on the bonds. The total amount of qualified bonds currently outstanding is $8,095,000. The total amount of qualified loans currently outstanding is $0. The estimated computed millage rate may change based on changes in certain circumstances.

(Pursuant to State law, expenditure of bond proceeds must be audited and the proceeds cannot be used for repair or maintenance costs, teacher, administrator or employee salaries, or other operating expenses.)
""".strip()
            log.info(f"{actual=}")
            log.info(f"{expected=}")
            expect(actual) == expected


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
