# pylint: disable=unused-argument,unused-variable


import log
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
        (68322, 20),
        (56663, 32),
        (50021, 22),
        (48210, 23),
        (43465, 19),
    ],
)
def test_2022_primary_ballots(expect, db, precinct_id, item_count):
    expect(parse_ballot(690, precinct_id)) == item_count


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("precinct_id", "item_count"),
    [
        (1878, 99),
        (68643, 73),
    ],
)
def test_2022_general_ballots(expect, db, precinct_id, item_count):
    expect(parse_ballot(691, precinct_id)) == item_count


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("precinct_id", "item_count"),
    [
        (2300, 1),
    ],
)
def test_2023_consolidated_ballots(expect, db, precinct_id, item_count):
    expect(parse_ballot(694, precinct_id)) == item_count


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("precinct_id", "item_count"),
    [
        (4190, 4),
        (7192, 5),
    ],
)
def test_2023_november_consolidated_ballots(expect, db, precinct_id, item_count):
    expect(parse_ballot(695, precinct_id)) == item_count


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
    parse_ballot(691, 63051)
    proposal = Proposal.objects.get(name__startswith="Proposal 22-1")
    expect(proposal.name).contains("12 Total Years in Legislature")
    expect(proposal.name).excludes("\n")
    expect(proposal.description).startswith("This proposed constitutional amendment")
    expect(proposal.description).contains(
        "political organizations\n- Require legislature"
    )
    expect(proposal.description).endswith(
        "became a candidate\n\nShould this proposal be adopted?"
    )


@pytest.mark.vcr
def test_running_mate(expect, db):
    parse_ballot(691, 63051)
    candidate = Candidate.objects.get(name__contains="Kevin Hogan")
    expect(candidate.name) == "Kevin Hogan & Destiny Clayton"


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
def test_capitalization(expect, db):
    parse_ballot(683, 1828)
    expect(Position.objects.filter(name__contains="of The").count()) == 0
    expect(Position.objects.filter(name__contains="of the").count()) == 3


@pytest.mark.vcr
def test_ward_positions(expect, db):
    parse_ballot(691, 68112)
    position = Position.objects.get(name__contains="Ward")
    assert position.district
    expect(position.name) == "Council Member by Ward"
    expect(position.district.name) == "City of Grand Rapids, Ward 2"
    expect(position.candidates.count()) == 2


@pytest.mark.vcr
def test_ward_positions_partial_term(expect, db):
    parse_ballot(695, 7192)
    positions = Position.objects.filter(name__contains="Ward")
    terms = sorted(position.term for position in positions)
    expect(terms) == ["4 Year Term", "Partial Term Ending 12/31/2025"]


@pytest.mark.vcr
def test_court_of_appeals_incumbency(expect, db):
    parse_ballot(691, 46994)
    positions = Position.objects.filter(name__contains="Court of Appeals")
    for position in positions:
        log.info(position)
    expect(len(positions)) == 3
