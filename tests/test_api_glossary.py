# pylint: disable=unused-argument,unused-variable

import pytest

from elections.models import Party


def describe_list():
    @pytest.fixture
    def url():
        return '/api/glossary/'

    def it_includes_edit_links(expect, client, url, db):
        Party.objects.create(name="Foobar", description="TBD")

        response = client.get(url)

        expect(response.data) == [
            {
                'category': 'parties',
                'name': 'Foobar',
                'description': 'TBD',
                'edit_url': 'https://github.com/citizenlabsgr/elections-api/edit/master/content/parties/Foobar.md',
            }
        ]
