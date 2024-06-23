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
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("election_id", "precinct_id", "item_count"),
    [
        # 2023 Consolidated
        (694, 2300, 1),
        # 2023 November Consolidated
        (695, 4190, 4),
        (695, 7192, 5),
        # 2024 Primary
        (696, 529, 11),
        (696, 1561, 12),
        # 2024 May Consolidated
        (697, 4185, 1),
        (697, 5951, 1),
        # 2024 August Primary
        (698, 4316, 32),
        (698, 4321, 41),
        (698, 49195, 32),
        (698, 50416, 36),
    ],
)
def test_parse_ballot(expect, election_id, precinct_id, item_count):
    expect(parse_ballot(election_id, precinct_id)) == item_count


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
    parse_ballot(683, 6911)  # ensure no conflict


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
    districts = sorted(str(position.district) for position in positions)
    terms = sorted(position.term for position in positions)
    seats = sorted(position.seats for position in positions)
    expect(districts) == ["City of Menominee, Ward 4", "City of Menominee, Ward 4"]
    expect(terms) == ["4 Year Term", "Partial Term Ending 12/31/2025"]
    expect(seats) == [1, 1]


@pytest.mark.vcr
def test_court_of_appeals_incumbency(expect, db):
    parse_ballot(691, 46994)
    positions = Position.objects.filter(name__contains="Court of Appeals")
    for position in positions:
        log.info(position)
    expect(len(positions)) == 3
