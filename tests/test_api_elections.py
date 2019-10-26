# pylint: disable=unused-argument,unused-variable

import pendulum
import pytest

from . import factories


@pytest.fixture
def url():
    return '/api/elections/'


@pytest.fixture
def elections(db):
    factories.ElectionFactory.create(active=True)
    factories.ElectionFactory.create(
        active=False, date=pendulum.parse('2017-08-07', tz='America/Detroit')
    )


def describe_list():
    def filter_by_active(expect, client, url, elections):
        response = client.get(url + '?active=true')

        expect(response.status_code) == 200
        expect(response.data['count']) == 1

    def filter_by_all(expect, client, url, elections):
        response = client.get(url + '?active=all')

        expect(response.status_code) == 200
        expect(response.data['count']) == 2
