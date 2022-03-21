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
        birth_date=pendulum.parse("1975-08-03"),  # type: ignore
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
                "Application Received": datetime.date(2020, 6, 6),
                "Ballot Sent": datetime.date(2020, 9, 24),
                "Ballot Received": datetime.date(2020, 9, 29),
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
                "PollAddress": "1736 Lyon NE",
                "PollCityStateZip": "Grand Rapids, MI 49503",
            },
            "dropbox_locations": [
                {
                    "address": [
                        "300 Ottawa Ave NW",
                        "Grand Rapids, MI 49503",
                    ],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": [
                        "1563 Plainfield Avenue NE",
                        "Grand Rapids, MI 49505",
                    ],
                    "hours": [
                        "Available 24 Hours/7 Days a Week",
                    ],
                },
                {
                    "address": [
                        "1017 Leonard, NW",
                        "Grand Rapids, MI 49504",
                    ],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": [
                        "427 Market, SW",
                        "Grand Rapids, MI 49503",
                    ],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": [
                        "1150 Giddings SE",
                        "Grand Rapids, MI 49506",
                    ],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": [
                        "2350 Eastern SE",
                        "Grand Rapids, MI 49507",
                    ],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": [
                        "300 Monroe Avenue, NW",
                        "Grand Rapids, MI 49503",
                    ],
                    "hours": [
                        "Mon. 8am-5pm",
                        "Tue. 8am-5pm",
                        "Wed. 8am-5pm",
                        "Thu. 8am-5pm",
                        "Fri. 8am-5pm",
                    ],
                },
            ],
            "recently_moved": False,
        }
