# pylint: disable=unused-argument,unused-variable

import pendulum
import pytest

from . import factories


def describe_registrations():
    @pytest.fixture
    def url():
        return '/api/registrations/'

    def with_valid_identity(expect, anything, client, url, db):
        response = client.get(
            url + '?first_name=Jace'
            '&last_name=Browning'
            '&birth_date=1987-06-02'
            '&zip_code=49503'
        )

        expect(response.status_code) == 200
        expect(response.data) == {
            'registered': True,
            'precinct': {
                'url': anything,
                'id': anything,
                'county': 'Kent',
                'jurisdiction': 'City of Grand Rapids',
                'ward': '1',
                'number': '9',
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
                {
                    'url': anything,
                    'id': anything,
                    'category': 'County',
                    'name': 'Kent',
                },
                {
                    'url': anything,
                    'id': anything,
                    'category': 'County Commissioner District',
                    'name': '15th District',
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

    def with_unknown_identity(expect, client, url):
        response = client.get(
            url + '?first_name=Jane'
            '&last_name=Doe'
            '&birth_date=2000-01-01'
            '&zip_code=999999'
        )

        expect(response.status_code) == 200
        expect(response.data) == {
            'registered': False,
            'precinct': None,
            'districts': [],
        }


def describe_precincts():
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


def describe_elections():
    @pytest.fixture
    def url():
        return '/api/elections/'

    def describe_list():
        @pytest.fixture
        def elections(db):
            factories.ElectionFactory.create(active=True)
            factories.ElectionFactory.create(
                active=False,
                date=pendulum.parse('2017-08-07', tz='America/Detroit'),
            )

        def filter_by_active(expect, client, url, elections):
            response = client.get(url)  # filter by active should be default

            expect(response.status_code) == 200
            expect(response.data['count']) == 1

        def filter_by_all(expect, client, url, elections):
            response = client.get(url + '?active=all')

            expect(response.status_code) == 200
            expect(response.data['count']) == 2


def describe_ballots():
    @pytest.fixture
    def url():
        return '/api/ballots/'

    def describe_list():
        @pytest.fixture
        def ballot(db):
            ballot = factories.BallotFactory.create()
            ballot.precinct.number = '1A'
            ballot.precinct.save()
            return ballot

        def filter_by_precinct_with_letter(
            expect, client, url, ballot, anything
        ):
            response = client.get(
                url + f'?precinct_number={ballot.precinct.number}'
            )

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
                        'ward': '2',
                        'number': '1A',
                    },
                    'mi_sos_url': 'https://webapps.sos.state.mi.us/MVIC/SampleBallot.aspx?d=1111&ed=2222',
                }
            ]

        def filter_by_election_id(expect, client, url, ballot):
            response = client.get(url + '?election_id=999')

            expect(response.status_code) == 200
            expect(response.data['count']) == 0

            response = client.get(url + f'?election_id={ballot.election.id}')

            expect(response.status_code) == 200
            expect(response.data['count']) == 1
