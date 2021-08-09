# pylint: disable=unused-argument,unused-variable

import pendulum
import pytest

from elections import defaults

from . import factories


@pytest.fixture
def election(db):
    instance = factories.ElectionFactory.create(pk=42)
    factories.ElectionFactory.create(
        active=False, date=pendulum.parse('2017-08-07', tz='America/Detroit')
    )
    return instance


def describe_create():
    @pytest.fixture
    def url():
        return '/api/status/'

    @pytest.mark.vcr
    def it_returns_data_for_a_registered_voter(expect, client, url, election):
        defaults.initialize_districts()

        data = {
            'first_name': 'Rosalynn',
            'last_name': 'Bliss',
            'birth_date': '1975-08-03',
            'zip_code': '49503',
        }
        response = client.post(url, data)

        expect(response.status_code) == 200
        expect(response.data) == {
            'id': '42-4085-6892',
            'message': 'You are registered to vote absentee and your ballot was received on 2020-09-29 for the General Election election on 2018-08-07.',
            'election': {
                'name': 'General Election',
                'date': '2018-08-07',
                'description': '',
                'reference_url': None,
            },
            'status': {
                'registered': True,
                'absentee': True,
                'absentee_application_received': '2020-06-06',
                'absentee_ballot_sent': '2020-09-24',
                'absentee_ballot_received': '2020-09-29',
            },
        }

    @pytest.mark.vcr
    def it_handles_unknown_voters(expect, client, url, election):
        data = {
            'first_name': 'Rosalynn',
            'last_name': 'Bliss',
            'birth_date': '1975-08-03',
            'zip_code': '49503',
        }
        response = client.post(url, data)

        expect(response.status_code) == 200
        expect(response.data) == {
            'id': '42-4085-2869',
            'message': 'You are not registered to vote for the General Election election on 2018-08-07.',
            'election': {
                'name': 'General Election',
                'date': '2018-08-07',
                'description': '',
                'reference_url': None,
            },
            'status': {
                'registered': False,
                'absentee': False,
                'absentee_application_received': None,
                'absentee_ballot_sent': None,
                'absentee_ballot_received': None,
            },
        }
