# pylint: disable=unused-variable

import os

import pendulum
import pytest

from .. import helpers, models


@pytest.fixture
def voter():
    return models.Voter(
        first_name="Jace",
        last_name="Browning",
        birth_date=pendulum.parse("1987-06-02", tz='America/Detroit'),
        zip_code="49503",
    )


def describe_fetch_registration_status_data():
    @pytest.mark.vcr(record_mode="none" if os.getenv("CI") else "once")
    def with_known_voter(expect, voter):
        data = helpers.fetch_registration_status_data(voter)
        expect(data) == {
            "registered": True,
            "districts": {
                "Circuit Court": "17th Circuit",
                "Community College District": "Grand Rapids Community College",
                "County": "Kent County",
                "County Commissioner District": "15th District",
                "Court of Appeals": "3rd District",
                "District Court": "61st District",
                "Intermediate School District": "Kent ISD",
                "Jurisdiction": "City of Grand Rapids",
                "Library District": "",
                "Metropolitan District": "",
                "Municipal Court": "",
                "Precinct": "9",
                "Probate Court": "Kent County Probate Court",
                "Probate District Court": "",
                "School District": "Grand Rapids Public Schools",
                "State House District": "75th District",
                "State Senate District": "29th District",
                "US Congress District": "3rd District",
                "Village": "",
                "Ward": "1",
            },
        }
