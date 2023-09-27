# pylint: disable=unused-argument,unused-variable

from datetime import datetime

import pytest
from django.utils import timezone

from . import factories


@pytest.fixture
def elections(db):
    factories.ElectionFactory.create(active=True)
    factories.ElectionFactory.create(
        active=False, date=timezone.make_aware(datetime(2017, 8, 7))
    )


def describe_list():
    @pytest.fixture
    def url():
        return "/api/elections/"

    def it_can_be_filtered_by_active(expect, client, url, elections):
        response = client.get(url + "?active=true")

        expect(response.status_code) == 200
        expect(response.data["count"]) == 1

    def it_can_be_filtered_by_all(expect, client, url, elections):
        response = client.get(url + "?active=all")

        expect(response.status_code) == 200
        expect(response.data["count"]) == 2
