# pylint: disable=unused-argument,unused-variable

import pytest

from . import factories


@pytest.fixture
def ballot(db):
    ballot = factories.BallotFactory.create()
    ballot.precinct.number = "1A"
    ballot.precinct.save()
    return ballot


def describe_list():
    @pytest.fixture
    def url():
        return "/api/ballots/"

    def it_can_be_filtered_by_election_id(expect, client, url, ballot):
        response = client.get(url + "?election_id=999")

        expect(response.status_code) == 200
        expect(response.data["count"]) == 0

        response = client.get(url + f"?election_id={ballot.election.id}")

        expect(response.status_code) == 200
        expect(response.data["count"]) == 1

    def it_can_be_filtered_by_precinct_with_letter(expect, client, url, ballot):
        response = client.get(url + f"?precinct_number={ballot.precinct.number}")

        expect(response.status_code) == 200
        expect(response.data["results"]) == [
            {
                "url": f"http://testserver/api/ballots/{ballot.id}/",
                "id": ballot.id,
                "election": {
                    "id": ballot.election.id,
                    "name": "General Election",
                    "date": "2018-08-07",
                    "date_humanized": "Tuesday, August 7th",
                    "active": True,
                    "reference_url": None,
                },
                "precinct": {
                    "url": f"http://testserver/api/precincts/{ballot.precinct.id}/",
                    "id": ballot.precinct.id,
                    "county": "",
                    "jurisdiction": "",
                    "ward": ballot.precinct.ward,
                    "number": ballot.precinct.number,
                },
                "mvic_url": "https://mvic.sos.state.mi.us/Voter/GetMvicBallot/1111/2222/",
            }
        ]


def describe_detail():
    @pytest.fixture
    def url(ballot):
        return f"/api/ballots/{ballot.id}/"

    def it_ignores_active_election_filter(expect, client, url, ballot):
        response = client.get(url + "?active_election=false")

        expect(response.status_code) == 200
        expect(response.data).contains("election")

    def it_handles_unknown_ballots(expect, client, url, ballot):
        ballot.delete()
        response = client.get(url)

        expect(response.status_code) == 404
