# pylint: disable=unused-argument,unused-variable


import pytest

from elections import defaults
from elections.models import BallotWebsite, Candidate, Position, Proposal


def parse_ballot(election_id: int, precinct_id: int) -> int:
    defaults.initialize_districts()
    defaults.initialize_parties()

    website, _ = BallotWebsite.objects.get_or_create(
        mi_sos_election_id=election_id, mi_sos_precinct_id=precinct_id
    )
    website.fetch()
    website.validate()
    website.scrape()

    ballot = website.convert()
    ballot.website = website
    return ballot.parse()


@pytest.mark.parametrize(
    'election_id, precinct_id, item_count',
    [
        # 2020 State Primary
        (682, 160, 1),
        # (682, 911, 37), # TODO: Handle ballots with "no candidates" followed by some
        (682, 7608, 29),
        (682, 1828, 25),
        (682, 7489, 25),
        (682, 6911, 37),
        # 2020 State General
        (683, 901, 89),
        (683, 133, 83),
        (683, 268, 92),
        (683, 256, 93),
        (683, 7558, 100),
        (683, 7222, 83),
        (683, 412, 93),
        (683, 7159, 87),
        (683, 6477, 108),
        (683, 4279, 92),
        (683, 4258, 96),
        (683, 1633, 85),
    ],
)
def test_ballots(expect, db, election_id, precinct_id, item_count):
    expect(parse_ballot(election_id, precinct_id)) == item_count


def test_reference_url(expect, db):
    parse_ballot(683, 1828)
    candidate = Candidate.objects.get(name="David LaGrand")
    expect(candidate.reference_url) == 'https://cfrsearch.nictusa.com/committees/517249'
    candidate = Candidate.objects.get(name="Mark Thomas Boonstra")
    expect(candidate.reference_url) == 'https://cfrsearch.nictusa.com/committees/515816'


def test_proposal_description(expect, db):
    parse_ballot(682, 6911)
    proposal = Proposal.objects.first()
    expect(proposal.description).startswith("Shall the limitation")
    expect(proposal.description).endswith("an estimated $175,000.00?")


def test_default_term(expect, db):
    parse_ballot(683, 6911)
    position = Position.objects.filter(
        name="Representative in State Legislature"
    ).first()
    expect(position.term) == "2 Year Term"
    parse_ballot(683, 6911)
