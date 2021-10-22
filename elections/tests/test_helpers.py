# pylint: disable=unused-variable


import datetime

import pendulum
import pytest

from .. import helpers, models


@pytest.fixture
def voter():
    return models.Voter(
        first_name="Rosalynn",
        last_name="Bliss",
        birth_date=pendulum.parse("1975-08-03"),
        zip_code="49503",
    )


def describe_fetch_registration_status_data():
    @pytest.mark.vcr
    def with_known_voter(expect, voter):
        data = helpers.fetch_registration_status_data(voter)
        expect(data) == {
            "registered": True,
            "ballot": True,
            "absentee": True,
            "absentee_dates": {
                'Application Received': datetime.date(2020, 6, 6),
                'Ballot Sent': datetime.date(2020, 9, 24),
                'Ballot Received': datetime.date(2020, 9, 29),
            },
            "districts": {
                "Circuit Court": "17th Circuit",
                "Community College": "Grand Rapids Community College",
                "County Commissioner": "18th District",
                "County": "Kent County",
                "Court of Appeals": "3rd District",
                "District Court": "61st District",
                "Intermediate School": "Kent ISD",
                "Jurisdiction": "City of Grand Rapids",
                "Library": "",
                "Metropolitan": "",
                "Municipal Court": "",
                "Precinct": "30",
                "Probate Court": "Kent County Probate Court",
                "Probate District Court": "",
                "School": "Grand Rapids Public Schools",
                "State House": "75th District",
                "State Senate": "29th District",
                "US Congress": "3rd District",
                "Village": "",
                "Ward": "2",
            },
            "polling_location": {
                "PollingLocation": "Encounter Church",
                "PollAddress": "1736 Lyon Ne",
                "PollCityStateZip": "Grand Rapids, Michigan 49503",
            },
            "dropbox_location": [
                'Election Central',
                '201 Market',
                'Grand Rapids, Michigan',
            ],
            "recently_moved": False,
        }
