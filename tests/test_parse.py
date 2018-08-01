# pylint: disable=unused-variable,unused-argument

import pendulum

from elections import models


def describe_ballot_website():
    def describe_parse():
        def with_single_proposal(expect, db):
            models.Election.objects.get_or_create(
                name="State Primary",
                date=pendulum.parse("2018-08-07", tz='America/Detroit'),
                mi_sos_id=675,
            )

            models.Party.objects.get_or_create(name="Republican")
            models.Party.objects.get_or_create(name="Democratic")
            models.Party.objects.get_or_create(name="Libertarian")

            state, _ = models.DistrictCategory.objects.get_or_create(
                name="State"
            )
            us_congress_district, _ = models.DistrictCategory.objects.get_or_create(
                name="US Congress District"
            )
            state_senate_district, _ = models.DistrictCategory.objects.get_or_create(
                name="State Senate District"
            )
            state_house_district, _ = models.DistrictCategory.objects.get_or_create(
                name="State House District"
            )

            models.District.objects.get_or_create(
                category=state, name="Michigan"
            )
            models.District.objects.get_or_create(
                category=us_congress_district, name="9th District"
            )
            models.District.objects.get_or_create(
                category=state_senate_district, name="10th District"
            )
            models.District.objects.get_or_create(
                category=state_house_district, name="25th District"
            )

            models.Precinct.objects.get_or_create(
                county=models.District.objects.get_or_create(
                    category=models.DistrictCategory.objects.get_or_create(
                        name="County"
                    )[0],
                    name="Macomb",
                )[0],
                jurisdiction=models.District.objects.get_or_create(
                    category=models.DistrictCategory.objects.get_or_create(
                        name="Jurisdiction"
                    )[0],
                    name="City of Sterling Heights",
                )[0],
                mi_sos_id=2000,
            )

            website = models.BallotWebsite(
                mi_sos_election_id=675, mi_sos_precinct_id=2000
            )
            website.fetch()

            expect(len(website.parse())) == 31
