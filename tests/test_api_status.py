# pylint: disable=unused-argument,unused-variable

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import time_machine
from django.conf import settings
from django.utils import timezone

from elections import defaults, exceptions

from . import factories


@pytest.fixture
def election(db):
    election = factories.ElectionFactory.create(pk=42)
    factories.ElectionFactory.create(
        active=False, date=timezone.make_aware(datetime(2017, 8, 7))
    )
    return election


@pytest.fixture
def ballot(election):
    ballot = factories.BallotFactory.create(
        election=election,
        website=factories.BallotWebsiteFactory.create(
            mvic_election_id=683, mvic_precinct_id=1792
        ),
    )
    return ballot


def describe_create():
    @pytest.fixture
    def url():
        return "/api/status/"

    @pytest.mark.vcr
    @time_machine.travel("2018-08-06")
    def it_returns_data_for_a_registered_voter(expect, client, url, election, ballot):
        defaults.initialize_districts()

        response = client.get(
            url + "?first_name=Rosalynn"
            "&last_name=Bliss"
            "&birth_date=1975-08-03"
            "&zip_code=49503"
        )

        expect(response.status_code) == 200
        expect(response.data) == {
            "id": f"{settings.API_CACHE_KEY}42-4085-6191",
            "message": "Rosalynn Bliss is registered to vote absentee and your ballot was received on 2024-02-06 for the General Election election on 2018-08-07.",
            "election": {
                "id": 42,
                "name": "General Election",
                "date": "2018-08-07",
                "reference_url": None,
            },
            "precinct": {
                "id": expect.anything,
                "county": "Kent",
                "jurisdiction": "City of Grand Rapids",
                "ward": "2",
                "number": "36",
            },
            "status": {
                "registered": True,
                "ballot": False,
                "absentee": True,
                "absentee_application_received": "2024-01-10",
                "absentee_ballot_sent": "2024-01-22",
                "absentee_ballot_received": "2024-02-06",
            },
            # TODO: Enable this when there is real election data
            # "ballot": {
            #     "id": expect.anything,
            #     "mvic_url": "https://mvic.sos.state.mi.us/Voter/GetMvicBallot/1792/683/",
            #     "items": -1,
            # },
            "ballot": expect.anything,
        }

    @pytest.mark.vcr
    @time_machine.travel("2018-08-06")
    def it_handles_unknown_voters(expect, client, url, election):
        response = client.get(
            url + "?first_name=Jane"
            "&last_name=Doe"
            "&birth_date=2000-01-01"
            "&zip_code=999999"
        )

        expect(response.status_code) == 200
        expect(response.data) == {
            "id": f"{settings.API_CACHE_KEY}42-3436-2176",
            "message": "Jane Doe is not registered to vote for the General Election election on 2018-08-07.",
            "election": {
                "id": 42,
                "name": "General Election",
                "date": "2018-08-07",
                "reference_url": None,
            },
            "precinct": {
                "county": "",
                "jurisdiction": "",
                "ward": "",
                "number": "",
            },
            "status": {
                "registered": False,
                "ballot": None,
                "absentee": None,
                "absentee_application_received": None,
                "absentee_ballot_sent": None,
                "absentee_ballot_received": None,
            },
            "ballot": {},
        }

    @patch(
        "elections.helpers.fetch_registration_status_data",
        Mock(side_effect=exceptions.ServiceUnavailable),
    )
    @time_machine.travel("2018-08-06")
    def it_handles_mvic_outages(expect, client, url, election):
        response = client.get(
            url + "?first_name=Rosalynn"
            "&last_name=Bliss"
            "&birth_date=1975-08-03"
            "&zip_code=49503"
        )

        expect(response.status_code) == 202
        expect(response.data) == {
            "id": f"{settings.API_CACHE_KEY}42-4085-2176",
            "message": "The Michigan Secretary of State website is temporarily unavailable, please try again later.",
            "election": {
                "id": 42,
                "name": "General Election",
                "date": "2018-08-07",
                "reference_url": None,
            },
            "precinct": {
                "county": "",
                "jurisdiction": "",
                "ward": "",
                "number": "",
            },
            "status": {
                "registered": None,
                "ballot": None,
                "absentee": None,
                "absentee_application_received": None,
                "absentee_ballot_sent": None,
                "absentee_ballot_received": None,
            },
            "ballot": {},
        }
