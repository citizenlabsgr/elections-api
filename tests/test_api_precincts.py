# pylint: disable=unused-argument,unused-variable

import pytest

from . import factories


@pytest.fixture
def precinct(db):
    precinct = factories.PrecinctFactory.create()
    precinct.county.name = "Marquette"
    precinct.county.save()
    precinct.jurisdiction.name = "Forsyth Township"
    precinct.jurisdiction.save()
    precinct.ward = ""
    precinct.number = "3"
    precinct.save()
    return precinct


def describe_detail():
    @pytest.fixture
    def url(precinct):
        return f"/api/precincts/{precinct.id}/"

    def it_handles_precincts_without_a_ward(expect, client, url, precinct):
        response = client.get(url)

        expect(response.status_code) == 200
        expect(response.data) == {
            "url": f"http://testserver/api/precincts/{precinct.id}/",
            "id": precinct.id,
            "county": "Marquette",
            "jurisdiction": "Forsyth Township",
            "ward": None,
            "number": "3",
        }
