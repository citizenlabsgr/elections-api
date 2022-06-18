# pylint: disable=unused-argument,unused-variable


import pytest

from elections import defaults
from elections.models import BallotWebsite, Candidate, Position, Proposal


def parse_ballot(election_id: int, precinct_id: int) -> int:
    defaults.initialize_districts()
    defaults.initialize_parties()

    website, _ = BallotWebsite.objects.get_or_create(
        mvic_election_id=election_id, mvic_precinct_id=precinct_id
    )
    website.fetch()
    website.validate()
    website.scrape()

    ballot = website.convert()
    ballot.website = website
    return ballot.parse()


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("precinct_id", "item_count"),
    [
        (160, 1),
        # (911, 37), # TODO: Handle ballots with "no candidates" followed by some
        (7608, 29),
        (1828, 25),
        (7489, 25),
        (6911, 37),
    ],
)
def test_2020_primary_ballots(expect, db, precinct_id, item_count):
    expect(parse_ballot(682, precinct_id)) == item_count


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("precinct_id", "item_count"),
    [
        (901, 90),
        (133, 84),
        (268, 93),
        (256, 94),
        (7558, 101),
        (7222, 84),
        (412, 94),
        (7159, 88),
        (6477, 109),
        (4279, 93),
        (4258, 97),
        (1633, 86),
    ],
)
def test_2020_general_ballots(expect, db, precinct_id, item_count):
    expect(parse_ballot(683, precinct_id)) == item_count


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("precinct_id", "item_count"),
    [
        (1, 11),
    ],
)
def test_2021_primary_ballots(expect, db, precinct_id, item_count):
    expect(parse_ballot(686, precinct_id)) == item_count


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("precinct_id", "item_count"),
    [
        (6956, 1),
    ],
)
def test_2021_consolidated_ballots(expect, db, precinct_id, item_count):
    expect(parse_ballot(687, precinct_id)) == item_count


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("precinct_id", "item_count"),
    [
        (6176, 6),
        (6766, 1),
        (56389, 2),
        (56366, 2),
        (56357, 1),
        (56204, 1),
        (55859, 1),
        (55833, 1),
        (54783, 1),
        (45358, 3),
    ],
)
def test_2022_consolidated_ballots(expect, db, precinct_id, item_count):
    expect(parse_ballot(689, precinct_id)) == item_count


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("precinct_id", "item_count"),
    [
        (68616, 32),
    ],
)
def test_2022_primary_ballots(expect, db, precinct_id, item_count):
    expect(parse_ballot(690, precinct_id)) == item_count


@pytest.mark.vcr
def test_reference_url(expect, db):
    parse_ballot(683, 1828)
    candidate = Candidate.objects.get(name="David LaGrand")
    expect(candidate.reference_url) == "https://cfrsearch.nictusa.com/committees/517249"
    candidate = Candidate.objects.get(name="Mark Thomas Boonstra")
    expect(candidate.reference_url) == "https://cfrsearch.nictusa.com/committees/515816"


@pytest.mark.vcr
def test_proposal_district(expect, db):
    parse_ballot(689, 48658)
    proposal = Proposal.objects.get(name="Wyoming Public Schools Bonding Proposal")
    assert proposal.district
    expect(proposal.district.category.name) == "Local School"
    expect(proposal.district.name) == "Wyoming Public Schools"


@pytest.mark.vcr
def test_proposal_description_primary(expect, db):
    parse_ballot(682, 6911)
    proposal = Proposal.objects.get(name="Millage Renewal to Original Levy")
    expect(proposal.description).startswith("Shall the increase")
    expect(proposal.description).endswith("an estimated $975,000.00?")


@pytest.mark.vcr
def test_proposal_description_general(expect, db):
    parse_ballot(683, 1828)

    proposal = Proposal.objects.get(name="Proposal 20-1")
    expect(proposal.description).startswith("A proposed constitutional amendment")
    expect(proposal.description).endswith(
        "conservation.\n\nShould this proposal be adopted?"
    )
    expect(proposal.description).excludes("unreasonable searches")

    proposal = Proposal.objects.get(name="Proposal 20-2")
    expect(proposal.description).contains("unreasonable searches")
    expect(proposal.description).endswith("things.\n\nShould this proposal be adopted?")

    proposal = Proposal.objects.get(name__startswith="I. Proposed Amendment")
    expect(proposal.description).contains("City Charter Title II, Section 9")
    expect(proposal.description).excludes("winning a certain percentage")
    expect(proposal.description).endswith("years.\n\nShall this amendment be adopted?")


@pytest.mark.vcr
def test_default_term(expect, db):
    parse_ballot(683, 6911)
    position = Position.objects.filter(
        name="Representative in State Legislature"
    ).first()
    assert position
    expect(position.term) == "2 Year Term"
    parse_ballot(683, 6911)


@pytest.mark.vcr
def test_justices(expect, db):
    parse_ballot(683, 1828)
    candidate = Candidate.objects.filter(name__startswith="Bridget").first()
    expect(candidate.name) == "Bridget Mary McCormack"
    expect(candidate.position.district.name) == "Michigan"


@pytest.mark.vcr
def test_capitalization(expect, db):
    parse_ballot(683, 1828)
    expect(Position.objects.filter(name__contains="of The").count()) == 0
    expect(Position.objects.filter(name__contains="of the").count()) == 3
