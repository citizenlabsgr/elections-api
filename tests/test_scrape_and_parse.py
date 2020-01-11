# pylint: disable=unused-argument,unused-variable


import pytest

from elections import defaults
from elections.models import BallotWebsite, Candidate, Position


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
        # 2019 November Consolidated
        (679, 1828, 12),
        (679, 411, 1),
        (679, 780, 1),
        (679, 716, 1),
        (679, 227, 5),
        (679, 208, 1),
        (679, 2974, 1),
        (679, 2971, 1),
        (679, 2932, 11),
        (679, 1020, 1),
        (679, 1652, 1),
        (679, 4561, 8),
        (679, 6348, 13),
        (679, 6495, 4),
        (679, 7629, 9),
        (679, 7343, 5),
        (679, 4193, 5),
        # 2020 Presidential Primary
        (680, 2985, 25),
        (680, 7609, 23),
    ],
)
def test_ballots(expect, db, election_id, precinct_id, item_count):
    expect(parse_ballot(election_id, precinct_id)) == item_count


def test_commissioner_by_ward(expect, db):
    parse_ballot(679, 1828)

    position = Position.objects.get(name='Commissioner by Ward')
    expect(position.district.name) == 'City of Grand Rapids, Ward 1'


def test_presidential_primary(expect, db):
    parse_ballot(680, 2985)

    candidate = Candidate.objects.get(name='Elizabeth Warren')
    expect(candidate.party.name) == 'Democratic'
