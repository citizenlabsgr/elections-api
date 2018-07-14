# pylint: disable=unused-argument,unused-variable

import pendulum
import pytest

from . import factories


def describe_registrations():
    @pytest.fixture
    def url():
        return '/api/registrations/'

    def with_valid_identity(expect, client, url, db):
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
                'url': 'http://testserver/api/precincts/1/',
                'id': 1,
                'county': 'Kent',
                'jurisdiction': 'City of Grand Rapids',
                'ward': '1',
                'number': '9',
            },
            'districts': [
                {
                    'url': 'http://testserver/api/districts/1/',
                    'id': 1,
                    'category': 'Circuit Court',
                    'name': '17th Circuit',
                },
                {
                    'url': 'http://testserver/api/districts/2/',
                    'id': 2,
                    'category': 'Community College District',
                    'name': 'Grand Rapids Community College',
                },
                {
                    'url': 'http://testserver/api/districts/3/',
                    'id': 3,
                    'category': 'County',
                    'name': 'Kent',
                },
                {
                    'url': 'http://testserver/api/districts/4/',
                    'id': 4,
                    'category': 'County Commissioner District',
                    'name': '15th District',
                },
                {
                    'url': 'http://testserver/api/districts/5/',
                    'id': 5,
                    'category': 'Court of Appeals',
                    'name': '3rd District',
                },
                {
                    'url': 'http://testserver/api/districts/6/',
                    'id': 6,
                    'category': 'District Court',
                    'name': '61st District',
                },
                {
                    'url': 'http://testserver/api/districts/7/',
                    'id': 7,
                    'category': 'Intermediate School District',
                    'name': 'Kent ISD',
                },
                {
                    'url': 'http://testserver/api/districts/8/',
                    'id': 8,
                    'category': 'Jurisdiction',
                    'name': 'City of Grand Rapids',
                },
                {
                    'url': 'http://testserver/api/districts/9/',
                    'id': 9,
                    'category': 'Probate Court',
                    'name': 'Kent County Probate Court',
                },
                {
                    'url': 'http://testserver/api/districts/10/',
                    'id': 10,
                    'category': 'School District',
                    'name': 'Grand Rapids Public Schools',
                },
                {
                    'url': 'http://testserver/api/districts/11/',
                    'id': 11,
                    'category': 'State House District',
                    'name': '75th District',
                },
                {
                    'url': 'http://testserver/api/districts/12/',
                    'id': 12,
                    'category': 'State Senate District',
                    'name': '29th District',
                },
                {
                    'url': 'http://testserver/api/districts/13/',
                    'id': 13,
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

        def when_no_ward(expect, client, url, precinct):
            response = client.get(f'{url}{precinct.id}/')

            expect(response.status_code) == 200
            expect(response.data) == {
                'url': 'http://testserver/api/precincts/2/',
                'id': 2,
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

        def filter_by_precinct_with_letter(expect, client, url, ballot):
            response = client.get(
                url + f'?precinct_number={ballot.precinct.number}'
            )

            expect(response.status_code) == 200
            expect(response.data['results']) == [
                {
                    'url': 'http://testserver/api/ballots/1/',
                    'id': 1,
                    'election': {
                        'url': 'http://testserver/api/elections/5/',
                        'id': 5,
                        'name': '',
                        'date': '2018-08-07',
                        'active': True,
                        'reference_url': None,
                    },
                    'precinct': {
                        'url': 'http://testserver/api/precincts/3/',
                        'id': 3,
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
