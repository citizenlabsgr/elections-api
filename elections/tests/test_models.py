# pylint: disable=unused-variable,unused-argument,expression-not-assigned

import arrow
import pytest

from .. import models


def describe_voter_identity():
    @pytest.fixture
    def voter():
        return models.Voter(
            first_name="Jane",
            last_name="Doe",
            birth_date=arrow.get("1985-06-19"),
            zip_code=12345,
        )

    def describe_repr():
        def includes_all_info(expect, voter):
            expect(
                repr(voter)
            ) == "<voter: Jane Doe, birth=1985-06-19, zip=12345>"

    def describe_str():
        def includes_full_name(expect, voter):
            expect(str(voter)) == "Jane Doe"

    def describe_birth_month():
        def is_parsed_from_date(expect, voter):
            expect(voter.birth_month) == "June"

    def describe_birth_year():
        def is_parsed_from_date(expect, voter):
            expect(voter.birth_year) == 1985


def describe_district_category():
    @pytest.fixture
    def district_category():
        return models.DistrictCategory(name="County")

    def describe_str():
        def users_the_Name(expect, district_category):
            expect(str(district_category)) == "County"


def describe_district():
    @pytest.fixture
    def district():
        return models.District(name="Kent County")

    def describe_str():
        def users_the_Name(expect, district):
            expect(str(district)) == "Kent County"
