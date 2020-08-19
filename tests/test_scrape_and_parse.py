# pylint: disable=unused-argument,unused-variable


import pytest

from elections import defaults
from elections.models import BallotWebsite, Candidate, Proposal


def parse_ballot(election_id: int, precinct_id: int) -> int:
    defaults.initialize_districts()
    defaults.initialize_parties()

    website = BallotWebsite.objects.create(
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
        # 2020 May Consolidated
        (681, 6712, 2),
        # 2020 State Primary
        (682, 160, 1),
        (682, 911, 37),
        (682, 7608, 29),
        (682, 1828, 25),
        (682, 7489, 25),
        (682, 6911, 37),
        # 2020 State General
        (683, 901, 17),
        (683, 133, 18),
        (683, 268, 12),
    ],
)
def test_ballots(expect, db, election_id, precinct_id, item_count):
    expect(parse_ballot(election_id, precinct_id)) == item_count


def test_reference_url(expect, db):
    parse_ballot(682, 1828)
    candidate = Candidate.objects.get(name="David LaGrand")
    expect(candidate.reference_url) == 'https://cfrsearch.nictusa.com/committees/517249'


def test_proposal_description(expect, db):
    parse_ballot(682, 6911)
    proposal = Proposal.objects.first()
    expect(proposal.description).startswith("Shall the limitation")
    expect(proposal.description).endswith("an estimated $175,000.00?")
