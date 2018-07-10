# pylint: disable=unused-argument,unused-variable

import pytest

from . import factories


def describe_registrations():
    def with_valid_identity(expect, client, db):
        response = client.get(
            '/api/registrations/'
            '?first_name=Jace'
            '&last_name=Browning'
            '&birth_date=1987-06-02'
            '&zip_code=49503'
        )

        expect(response.status_code) == 200
        expect(response.data) == [
            {
                'registered': True,
                'poll': {
                    'url': 'http://testserver/api/polls/1/',
                    'id': 1,
                    'county': 'Kent',
                    'jurisdiction': 'City of Grand Rapids',
                    'ward': '1',
                    'precinct': '9',
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
        ]


def describe_polls():
    @pytest.fixture
    def url():
        return '/api/polls/'

    def describe_detail():
        @pytest.fixture
        def poll(db):
            poll = factories.PollFactory.create()
            poll.county.name = "Marquette"
            poll.county.save()
            poll.jurisdiction.name = "Forsyth Township"
            poll.jurisdiction.save()
            poll.ward = ''
            poll.precinct = '3'
            poll.save()
            return poll

        def when_no_ward(expect, client, url, poll):
            response = client.get(f'{url}{poll.id}/')

            expect(response.status_code) == 200
            expect(response.data) == {
                'url': 'http://testserver/api/polls/2/',
                'id': 2,
                'county': 'Marquette',
                'jurisdiction': 'Forsyth Township',
                'ward': None,
                'precinct': '3',
            }


def describe_ballots():
    @pytest.fixture
    def url():
        return '/api/ballots/'

    def describe_list():
        @pytest.fixture
        def ballot(db):
            ballot = factories.BallotFactory.create()
            ballot.poll.precinct = '1A'
            ballot.poll.save()
            return ballot

        def filter_by_precinct_with_letter(expect, client, url, ballot):
            response = client.get(url + '?precinct=1A')

            expect(response.status_code) == 200
            expect(response.data) == [
                {
                    'url': 'http://testserver/api/ballots/1/',
                    'id': 1,
                    'election': {
                        'url': 'http://testserver/api/elections/1/',
                        'id': 1,
                        'name': '',
                        'date': '2018-08-07',
                        'reference_url': None,
                    },
                    'poll': {
                        'url': 'http://testserver/api/polls/3/',
                        'id': 3,
                        'county': '',
                        'jurisdiction': '',
                        'ward': '2',
                        'precinct': '1A',
                    },
                    'mi_sos_url': 'https://webapps.sos.state.mi.us/MVIC/SampleBallot.aspx?d=1111&ed=2222',
                }
            ]
