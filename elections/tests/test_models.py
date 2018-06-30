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
        )

    def describe_str():
        def includes_full_name(expect, voter):
            expect(str(voter)) == "Jane Doe"

    def describe_birth_month():
        def is_parsed_from_date(expect, voter):
            expect(voter.birth_month) == "June"

    def describe_birth_year():
        def is_parsed_from_date(expect, voter):
            expect(voter.birth_year) == 1985


def describe_region_type():
    @pytest.fixture
    def region_type():
        return models.RegionType(name="County")

    def describe_str():
        def users_the_Name(expect, region_type):
            expect(str(region_type)) == "County"
