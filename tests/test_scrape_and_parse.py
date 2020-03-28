# pylint: disable=unused-argument,unused-variable


import pytest

from elections import defaults
from elections.models import BallotWebsite


def parse_ballot(election_id: int, precinct_id: int) -> int:
    defaults.initialize_districts()
    defaults.initialize_parties()

    website = BallotWebsite.objects.create(
        mi_sos_election_id=election_id, mi_sos_precinct_id=precinct_id
    )

    website.fetch()
    website.validate()
    website.scrape()
    website.convert()

    ballot = website.convert()
    ballot.website = website

    return ballot.parse()


@pytest.mark.parametrize(
    'election_id, precinct_id, item_count',
    [
        # 2020 May Consolidated
        (681, 6712, 2),
    ],
)
def test_ballots(expect, db, election_id, precinct_id, item_count):
    expect(parse_ballot(election_id, precinct_id)) == item_count
