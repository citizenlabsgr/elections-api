# pylint: disable=unused-argument,unused-variable

import pytest

from elections import defaults

from . import factories


@pytest.fixture
def ballot(db):
    return factories.BallotFactory.create(
        website=factories.BallotWebsiteFactory.create(
            mvic_election_id=683, mvic_precinct_id=1792
        )
    )


def describe_list():
    @pytest.fixture
    def url():
        return "/api/registrations/"

    @pytest.mark.vcr
    def it_returns_data_for_a_registered_voter(expect, client, url, ballot):
        defaults.initialize_districts()

        response = client.get(
            url + "?first_name=Rosalynn"
            "&last_name=Bliss"
            "&birth_date=1975-08-03"
            "&zip_code=49503",
        )

        expect(response.status_code) == 200
        expect(response.data) == {
            "registered": True,
            "ballot": True,
            "ballots": [
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "mvic_url": "https://mvic.sos.state.mi.us/Voter/GetMvicBallot/1792/683/",
                    "mvic_name": expect.anything,
                }
            ],
            "absentee": True,
            "absentee_application_received": "2020-06-06",
            "absentee_ballot_sent": "2020-09-24",
            "absentee_ballot_received": "2020-09-29",
            "polling_location": [
                "Encounter Church",
                "1736 Lyon NE",
                "Grand Rapids, MI 49503",
            ],
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
                    "hours": ["Available 24 Hours/7 Days a Week"],
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
            "precinct": {
                "url": expect.anything,
                "id": expect.anything,
                "county": "Kent",
                "jurisdiction": "City of Grand Rapids",
                "ward": "2",
                "number": "30",
            },
            "districts": [
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "Circuit Court District",
                    "name": "17th Circuit",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "Community College District",
                    "name": "Grand Rapids Community College",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "County",
                    "name": "Kent",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "County Commissioner District",
                    "name": "18th District",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "Court of Appeals District",
                    "name": "3rd District",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "District Court District",
                    "name": "61st District",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "Intermediate School District",
                    "name": "Kent ISD",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "Jurisdiction",
                    "name": "City of Grand Rapids",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "Probate Court District",
                    "name": "Kent County Probate Court",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "School District",
                    "name": "Grand Rapids Public Schools",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "State House District",
                    "name": "75th District",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "State Senate District",
                    "name": "29th District",
                },
                {
                    "url": expect.anything,
                    "id": expect.anything,
                    "category": "US Congress District",
                    "name": "3rd District",
                },
            ],
        }

    @pytest.mark.vcr
    def it_handles_unknown_voters(expect, client, url):
        response = client.get(
            url + "?first_name=JanE"
            "&last_name=Doe"
            "&birth_date=2000-01-01"
            "&zip_code=999999",
        )

        expect(response.status_code) == 200
        expect(response.data) == {
            "registered": False,
            "ballot": None,
            "ballots": [],
            "absentee": None,
            "absentee_application_received": None,
            "absentee_ballot_sent": None,
            "absentee_ballot_received": None,
            "polling_location": None,
            "dropbox_locations": None,
            "recently_moved": None,
            "precinct": None,
            "districts": [],
        }
