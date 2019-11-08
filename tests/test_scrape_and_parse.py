# pylint: disable=unused-argument,unused-variable


import pytest

from elections import defaults
from elections.models import BallotWebsite


@pytest.mark.parametrize(
    'election_id, precinct_id, item_count',
    [
        (676, 1, 128),
        (676, 7, 122),
        (676, 295, 110),
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
    ],
)
def test_ballots(expect, db, election_id, precinct_id, item_count):
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

    expect(ballot.parse()) == item_count
