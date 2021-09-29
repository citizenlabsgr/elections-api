# pylint: disable=unused-argument,unused-variable

from django.conf import settings

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

        response = client.get(
            url + '?first_name=Rosalynn'
            '&last_name=Bliss'
            '&birth_date=1975-08-03'
            '&zip_code=49503'
        )

        expect(response.status_code) == 200
        expect(response.data) == {
            'id': f'{settings.API_CACHE_KEY}42-4085-6199',
            'message': 'Rosalynn Bliss is registered to vote absentee and your ballot was received on 2020-09-29 for the General Election election on 2018-08-07.',
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
        response = client.get(
            url + '?first_name=Jane'
            '&last_name=Doe'
            '&birth_date=2000-01-01'
            '&zip_code=999999'
        )

        expect(response.status_code) == 200
        expect(response.data) == {
            'id': f'{settings.API_CACHE_KEY}42-3436-2176',
            'message': 'Jane Doe is not registered to vote for the General Election election on 2018-08-07.',
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
