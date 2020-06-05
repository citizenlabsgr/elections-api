# pylint: disable=unused-argument,unused-variable

import pytest

from . import factories


@pytest.fixture
def positions(db):
    position = factories.PositionFactory.create(
        section="Democratic", name="Delegate to County Convention"
    )
    factories.PositionFactory.create(
        election=position.election,
        section="Republican",
        name="Delegate to County Convention",
    )
    factories.PositionFactory.create(
        election=position.election, name="Library Board Director"
    )


def describe_list():
    @pytest.fixture
    def url():
        return '/api/positions/'

    def it_returns_all_positions_by_default(expect, client, url, positions):
        response = client.get(url)

        expect(response.status_code) == 200
        expect(len(response.data['results'])) == 3

    def it_can_be_filtered_by_section(expect, client, url, positions):
        response = client.get(url + f'?section=Democratic')

        expect(response.status_code) == 200
        expect(len(response.data['results'])) == 2
