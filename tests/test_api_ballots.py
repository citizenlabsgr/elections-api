# pylint: disable=unused-argument,unused-variable

import pytest

from . import factories


@pytest.fixture
def url():
    return '/api/ballots/'


@pytest.fixture
def ballot(db):
    ballot = factories.BallotFactory.create()
    ballot.precinct.number = '1A'
    ballot.precinct.save()
    return ballot


def describe_list():
    def filter_by_precinct_with_letter(expect, client, url, ballot, anything):
        response = client.get(url + f'?precinct_number={ballot.precinct.number}')

        expect(response.status_code) == 200
        expect(response.data['results']) == [
            {
                'url': 'http://testserver/api/ballots/1/',
                'id': 1,
                'election': {
                    'url': anything,
                    'id': anything,
                    'name': '',
                    'date': '2018-08-07',
                    'active': True,
                    'reference_url': None,
                },
                'precinct': {
                    'url': anything,
                    'id': anything,
                    'county': '',
                    'jurisdiction': '',
                    'ward': '1',
                    'number': '1A',
                },
                'mi_sos_url': 'https://mvic.sos.state.mi.us/Voter/GetMvicBallot/1111/2222/',
            }
        ]

    def filter_by_election_id(expect, client, url, ballot):
        response = client.get(url + '?election_id=999')

        expect(response.status_code) == 200
        expect(response.data['count']) == 0

        response = client.get(url + f'?election_id={ballot.election.id}')

        expect(response.status_code) == 200
        expect(response.data['count']) == 1
