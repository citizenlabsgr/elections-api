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
        (683, 901, 90),
        (683, 133, 84),
        (683, 268, 93),
        (683, 256, 94),
        (683, 7558, 101),
        (683, 7222, 84),
        (683, 412, 94),
        (683, 7159, 88),
        (683, 6477, 109),
        (683, 4279, 93),
        (683, 4258, 97),
        (683, 1633, 86),
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


def test_proposal_description_primary(expect, db):
    parse_ballot(682, 6911)
    proposal = Proposal.objects.get(name="Millage Renewal to Original Levy")
    expect(proposal.description).startswith("Shall the increase")
    expect(proposal.description).endswith("an estimated $975,000.00?")


def test_proposal_description_general(expect, db):
    parse_ballot(683, 1828)
    proposal = Proposal.objects.get(name="Proposal 20-1")
    expect(proposal.description).startswith("A proposed constitutional amendment")
    expect(proposal.description).endswith("Should this proposal be adopted?")
    expect(proposal.description).excludes("unreasonable searches")
    proposal = Proposal.objects.get(name="Proposal 20-2")
    expect(proposal.description).contains("unreasonable searches")


def test_default_term(expect, db):
    parse_ballot(683, 6911)
    position = Position.objects.filter(
        name="Representative in State Legislature"
    ).first()
    expect(position.term) == "2 Year Term"
    parse_ballot(683, 6911)
