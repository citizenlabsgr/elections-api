# pylint: disable=unused-argument,unused-variable

from . import factories


def describe_registrations():
    def with_valid_identity(expect, client, db):
        response = client.get(
            "/api/registrations/"
            "?first_name=Jace"
            "&last_name=Browning"
            "&birth_date=1987-06-02"
            "&zip_code=49503"
        )

        expect(response.status_code) == 200
        expect(response.data) == [
            {
                'registered': True,
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
                        'category': 'Precinct',
                        'name': '9',
                    },
                    {
                        'url': 'http://testserver/api/districts/10/',
                        'id': 10,
                        'category': 'Probate Court',
                        'name': 'Kent County Probate Court',
                    },
                    {
                        'url': 'http://testserver/api/districts/11/',
                        'id': 11,
                        'category': 'School District',
                        'name': 'Grand Rapids Public Schools',
                    },
                    {
                        'url': 'http://testserver/api/districts/12/',
                        'id': 12,
                        'category': 'State House District',
                        'name': '75th District',
                    },
                    {
                        'url': 'http://testserver/api/districts/13/',
                        'id': 13,
                        'category': 'State Senate District',
                        'name': '29th District',
                    },
                    {
                        'url': 'http://testserver/api/districts/14/',
                        'id': 14,
                        'category': 'US Congress District',
                        'name': '3rd District',
                    },
                    {
                        'url': 'http://testserver/api/districts/15/',
                        'id': 15,
                        'category': 'Ward',
                        'name': '1',
                    },
                ],
            }
        ]


def describe_polls():
    def when_no_ward(expect, client, db):
        poll = factories.PollFactory.create()
        poll.county.name = "Marquette"
        poll.county.save()
        poll.jurisdiction.name = "Forsyth Township"
        poll.jurisdiction.save()
        poll.ward_number = 0
        poll.precinct_number = 3
        poll.save()

        response = client.get(f"/api/polls/{poll.id}/")

        expect(response.status_code) == 200
        expect(response.data) == {
            'url': 'http://testserver/api/polls/1/',
            'id': 1,
            'county': 'Marquette',
            'jurisdiction': 'Forsyth Township',
            'ward_number': None,
            'precinct_number': 3,
            'precinct_letter': None,
        }
