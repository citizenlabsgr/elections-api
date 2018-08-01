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
                mi_sos_id=1828,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=constants.election.mi_sos_id,
                mi_sos_precinct_id=1828,
            )
            website.fetch()

            expect(len(website.parse())) == 26
