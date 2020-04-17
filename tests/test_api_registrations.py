# pylint: disable=unused-argument,unused-variable

import pytest

from elections import defaults


def describe_list():
    @pytest.fixture
    def url():
        return '/api/registrations/'

    def it_returns_data_for_a_registered_voter(expect, anything, client, url, db):
        defaults.initialize_districts()

        response = client.get(
            url + '?first_name=Rosalynn'
            '&last_name=Bliss'
            '&birth_date=1975-08-03'
            '&zip_code=49503'
        )

        expect(response.status_code) == 200
        expect(response.data) == {
            'registered': True,
            'absentee': True,
            'polling_location': [
                'Mayfair Christian Reformed Church',
                '1736 Lyon Ne',
                'Grand Rapids, Michigan 49503',
            ],
            'recently_moved': False,
            'precinct': {
                'url': anything,
                'id': anything,
                'county': 'Kent',
                'jurisdiction': 'City of Grand Rapids',
                'ward': '2',
                'number': '30',
            },
            'districts': [
                {
                    'url': anything,
                    'id': anything,
                    'category': 'Circuit Court District',
                    'name': '17th Circuit',
                },
                {
                    'url': anything,
                    'id': anything,
                    'category': 'Community College District',
                    'name': 'Grand Rapids Community College',
                },
                {'url': anything, 'id': anything, 'category': 'County', 'name': 'Kent'},
                {
                    'url': anything,
                    'id': anything,
                    'category': 'County Commissioner District',
                    'name': '18th District',
                },
                {
                    'url': anything,
                    'id': anything,
                    'category': 'Court of Appeals District',
                    'name': '3rd District',
                },
                {
                    'url': anything,
                    'id': anything,
                    'category': 'District Court District',
                    'name': '61st District',
                },
                {
                    'url': anything,
                    'id': anything,
                    'category': 'Intermediate School District',
                    'name': 'Kent ISD',
                },
                {
                    'url': anything,
                    'id': anything,
                    'category': 'Jurisdiction',
                    'name': 'City of Grand Rapids',
                },
                {
                    'url': anything,
                    'id': anything,
                    'category': 'Probate Court District',
                    'name': 'Kent County Probate Court',
                },
                {
                    'url': anything,
                    'id': anything,
                    'category': 'School District',
                    'name': 'Grand Rapids Public Schools',
                },
                {
                    'url': anything,
                    'id': anything,
                    'category': 'State House District',
                    'name': '75th District',
                },
                {
                    'url': anything,
                    'id': anything,
                    'category': 'State Senate District',
                    'name': '29th District',
                },
                {
                    'url': anything,
                    'id': anything,
                    'category': 'US Congress District',
                    'name': '3rd District',
                },
            ],
        }

    def it_handles_unknown_voters(expect, client, url):
        response = client.get(
            url + '?first_name=Jane'
            '&last_name=Doe'
            '&birth_date=2000-01-01'
            '&zip_code=999999'
        )

        expect(response.status_code) == 200
        expect(response.data) == {
            'registered': False,
            'absentee': False,
            'polling_location': None,
            'recently_moved': False,
            'precinct': None,
            'districts': [],
        }
