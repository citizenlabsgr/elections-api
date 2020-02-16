# pylint: disable=unused-argument,unused-variable

import pytest

from . import factories


@pytest.fixture
def ballot(db):
    ballot = factories.BallotFactory.create()
    ballot.precinct.number = '1A'
    ballot.precinct.save()
    return ballot


def describe_list():
    @pytest.fixture
    def url():
        return '/api/ballots/'

    def it_handles_ballots_without_websites(expect, client, url, ballot):
        ballot.website = None
        ballot.save()

        response = client.get(url)

        expect(response.status_code) == 200
        expect(response.data['results'][0]['mi_sos_url']) == None

    def it_can_be_filtered_by_election_id(expect, client, url, ballot):
        response = client.get(url + '?election_id=999')

        expect(response.status_code) == 200
        expect(response.data['count']) == 0

        response = client.get(url + f'?election_id={ballot.election.id}')

        expect(response.status_code) == 200
        expect(response.data['count']) == 1

    def it_can_be_filtered_by_precinct_with_letter(expect, client, url, ballot):
        response = client.get(url + f'?precinct_number={ballot.precinct.number}')

        expect(response.status_code) == 200
        expect(response.data['results']) == [
            {
                'url': f'http://testserver/api/ballots/{ballot.id}/',
                'id': ballot.id,
                'election': {
                    'url': f'http://testserver/api/elections/{ballot.election.id}/',
                    'id': ballot.election.id,
                    'name': 'General Election',
                    'description': '',
                    'description_edit_url': 'https://github.com/citizenlabsgr/elections-api/edit/master/content/elections/General%20Election.md',
                    'date': '2018-08-07',
                    'date_humanized': 'Tuesday, August 7th',
                    'active': True,
                    'reference_url': None,
                },
                'precinct': {
                    'url': f'http://testserver/api/precincts/{ballot.precinct.id}/',
                    'id': ballot.precinct.id,
                    'county': '',
                    'jurisdiction': '',
                    'ward': ballot.precinct.ward,
                    'number': ballot.precinct.number,
                },
                'mi_sos_url': 'https://mvic.sos.state.mi.us/Voter/GetMvicBallot/1111/2222/',
            }
        ]
