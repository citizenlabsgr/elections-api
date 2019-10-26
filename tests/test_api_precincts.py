# pylint: disable=unused-argument,unused-variable

import pytest

from . import factories


@pytest.fixture
def url():
    return '/api/precincts/'


def describe_detail():
    @pytest.fixture
    def precinct(db):
        precinct = factories.PrecinctFactory.create()
        precinct.county.name = "Marquette"
        precinct.county.save()
        precinct.jurisdiction.name = "Forsyth Township"
        precinct.jurisdiction.save()
        precinct.ward = ''
        precinct.number = '3'
        precinct.save()
        return precinct

    def when_no_ward(expect, client, url, precinct, anything):
        response = client.get(f'{url}{precinct.id}/')

        expect(response.status_code) == 200
        expect(response.data) == {
            'url': anything,
            'id': anything,
            'county': 'Marquette',
            'jurisdiction': 'Forsyth Township',
            'ward': None,
            'number': '3',
        }
