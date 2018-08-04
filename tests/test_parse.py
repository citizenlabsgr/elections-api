# pylint: disable=unused-variable,unused-argument

from types import SimpleNamespace

import pendulum
import pytest

from elections import models


def describe_ballot_website():
    def describe_parse():
        @pytest.fixture
        def constants(db):
            constants = SimpleNamespace()

            constants.election, _ = models.Election.objects.get_or_create(
                name="State Primary",
                date=pendulum.parse("2018-08-07", tz='America/Detroit'),
                mi_sos_id=675,
            )

            models.Party.objects.get_or_create(name="Republican")
            models.Party.objects.get_or_create(name="Democratic")
            models.Party.objects.get_or_create(name="Libertarian")
            models.Party.objects.get_or_create(name="Nonpartisan")

            state, _ = models.DistrictCategory.objects.get_or_create(
                name="State"
            )
            constants.county, _ = models.DistrictCategory.objects.get_or_create(
                name="County"
            )
            constants.county, _ = models.DistrictCategory.objects.get_or_create(
                name="City"
            )
            constants.jurisdiction, _ = models.DistrictCategory.objects.get_or_create(
                name="Jurisdiction"
            )
            constants.us_congress_district, _ = models.DistrictCategory.objects.get_or_create(
                name="US Congress District"
            )
            constants.state_senate_district, _ = models.DistrictCategory.objects.get_or_create(
                name="State Senate District"
            )
            constants.state_house_district, _ = models.DistrictCategory.objects.get_or_create(
                name="State House District"
            )
            constants.circuit_court, _ = models.DistrictCategory.objects.get_or_create(
                name="Circuit Court"
            )
            models.DistrictCategory.objects.get_or_create(name="Precinct")

            models.District.objects.get_or_create(
                category=state, name="Michigan"
            )

            return constants

        def with_single_proposal(expect, constants):
            models.Precinct.objects.get_or_create(
                county=models.District.objects.get_or_create(
                    category=constants.county, name="Macomb"
                )[0],
                jurisdiction=models.District.objects.get_or_create(
                    category=constants.jurisdiction,
                    name="City of Sterling Heights",
                )[0],
                number='26',
                mi_sos_id=2000,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=constants.election.mi_sos_id,
                mi_sos_precinct_id=2000,
            )
            website.fetch()

            expect(len(website.parse())) == 31

        def with_nonpartisan_section(expect, constants):
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

            expect(len(website.parse())) == 26

        def with_county_proposal(expect, constants):
            models.Precinct.objects.get_or_create(
                county=models.District.objects.get_or_create(
                    category=constants.county, name="Sanilac"
                )[0],
                jurisdiction=models.District.objects.get_or_create(
                    category=constants.jurisdiction, name="Lexington Township"
                )[0],
                number='1',
                mi_sos_id=3,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=constants.election.mi_sos_id,
                mi_sos_precinct_id=3,
            )
            website.fetch()

            expect(len(website.parse())) == 33

        def with_township_proposal(expect, constants):
            models.Precinct.objects.get_or_create(
                county=models.District.objects.get_or_create(
                    category=constants.county, name="Livingston"
                )[0],
                jurisdiction=models.District.objects.get_or_create(
                    category=constants.jurisdiction, name="Hamburg Township"
                )[0],
                number='3',
                mi_sos_id=2,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=constants.election.mi_sos_id,
                mi_sos_precinct_id=2,
            )
            website.fetch()

            expect(len(website.parse())) == 27

        def with_library_proposal(expect, constants):
            models.Precinct.objects.get_or_create(
                county=models.District.objects.get_or_create(
                    category=constants.county, name="Kalamazoo"
                )[0],
                jurisdiction=models.District.objects.get_or_create(
                    category=constants.jurisdiction, name="City of Galesburg"
                )[0],
                number='1',
                mi_sos_id=6,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=constants.election.mi_sos_id,
                mi_sos_precinct_id=6,
            )
            website.fetch()

            expect(len(website.parse())) == 26

        def with_city_position(expect, constants):
            models.Precinct.objects.get_or_create(
                county=models.District.objects.get_or_create(
                    category=constants.county, name="Washtenaw"
                )[0],
                jurisdiction=models.District.objects.get_or_create(
                    category=constants.jurisdiction, name="City of Ann Arbor,"
                )[0],
                ward='5',
                number='8',
                mi_sos_id=10,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=constants.election.mi_sos_id,
                mi_sos_precinct_id=10,
            )
            website.fetch()

            expect(len(website.parse())) == 31
