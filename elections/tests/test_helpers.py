# pylint: disable=unused-variable

import os

import arrow
import pytest

from .. import helpers, models


@pytest.fixture
def voter():
    return models.Voter(
        first_name="Jace",
        last_name="Browning",
        birth_date=arrow.get("1987-06-02"),
        zip_code="49503",
    )


def describe_fetch_registration_status_data():
    @pytest.mark.vcr(record_mode="none" if os.getenv("CI") else "once")
    def with_known_voter(expect, voter):
        data = helpers.fetch_registration_status_data(voter)
        expect(data) == {"registered": True}
