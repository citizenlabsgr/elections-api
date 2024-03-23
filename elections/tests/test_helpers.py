# pylint: disable=unused-variable


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


def describe_normalize_position():
    @pytest.mark.parametrize(
        ("before", "after"),
        [
            ("Commissioner At-Large", "Commissioner at Large"),
        ],
    )
    def it_removes_extra_words_and_titleizes(expect, before, after):
        expect(helpers.normalize_position(before)) == after


def describe_fetch_registration_status_data():
    @pytest.mark.vcr
    def with_known_voter(expect, voter):
        data = helpers.fetch_registration_status_data(voter)
        expect(data) == {
            "registered": True,
            # TODO: Enable this when there is real election data
            # "ballot": True,
            # "ballot_url": "https://mvic.sos.state.mi.us/Voter/GetMvicBallot/1792/683/",
            "absentee": True,
            # "absentee_dates": {
            #     "Election Date": datetime.date(2020, 11, 3),
            #     "Application Received": datetime.date(2020, 6, 6),
            #     "Ballot Sent": datetime.date(2020, 9, 24),
            #     "Ballot Received": datetime.date(2020, 9, 29),
            # },
            "ballot": expect.anything,
            "ballot_url": expect.anything,
            "absentee_dates": expect.anything,
            "districts": {
                "County": "Kent County",
                "Jurisdiction": "City of Grand Rapids",
                "Circuit Court": "17th Circuit",
                "Community College": "Grand Rapids Community College",
                "County Commissioner": "16th District",
                "Court of Appeals": "3rd District",
                "District Court": "61st District",
                "Intermediate School": "Kent ISD",
                "Library": "",
                "Metropolitan": "",
                "Municipal Court": "",
                "Precinct": "36",
                "Probate Court": "Kent County Probate Court",
                "Probate District Court": "",
                "School": "Grand Rapids Public Schools",
                "State House": "84th District",
                "State Senate": "30th District",
                "US Congress": "3rd District",
                "Village": "",
                "Ward": "2",
            },
            "polling_location": {
                "PollAddress": "617 Coit Ne (livingston Ent)",
                "PollCityStateZip": "Grand Rapids, MI 49503",
            },
            "dropbox_locations": [
                {
                    "address": ["300 Monroe NW", "Grand Rapids, MI 49503"],
                    "hours": [
                        "Mon. 8am-5pm",
                        "Tue. 8am-5pm",
                        "Wed. 8am-5pm",
                        "Thu. 8am-5pm",
                        "Fri. 8am-5pm",
                    ],
                },
                {
                    "address": ["110 Fountain NE", "Grand Rapids, MI 49503"],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": ["1201 Madison SE", "Grand Rapids, MI 49507"],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": ["1150 Giddings SE", "Grand Rapids, MI 49506"],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": ["2350 Eastern SE", "Grand Rapids, MI 49507"],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": ["1563 Plainfield NE", "Grand Rapids, MI 49505"],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": ["1017 Leonard NW", "Grand Rapids, MI 49504"],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": ["713 Bridge NW", "Grand Rapids, MI 49504"],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": ["2025 Leonard NE", "Grand Rapids, MI 49505"],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": ["300 Ottawa NW", "Grand Rapids, MI 49503"],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
                {
                    "address": ["1100 Cesar E Chavez SW", "Grand Rapids, MI 49503"],
                    "hours": ["Available 24 Hours/7 Days a Week"],
                },
            ],
            "recently_moved": False,
        }
