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
        # 2020 Primary
        (682, 160, 1),
        (682, 7608, 29),
        (682, 1828, 25),
        (682, 7489, 25),
        (682, 6911, 37),
        # 2020 General
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
        # 2021 Primary
        (686, 1, 11),
        # 2021 Consolidated
        (687, 6956, 1),
        # 2022 Consolidated
        (689, 6176, 6),
        (689, 6766, 1),
        (689, 56389, 2),
        (689, 56366, 2),
        (689, 56357, 1),
        (689, 56204, 1),
        (689, 55859, 1),
        (689, 55833, 1),
        (689, 54783, 1),
        (689, 45358, 3),
        # 2022 Primary
        (690, 68616, 32),
        (690, 68322, 20),
        (690, 56663, 32),
        (690, 50021, 22),
        (690, 48210, 23),
        (690, 43465, 19),
        # 2022 General
        (691, 1878, 99),
        (691, 68643, 73),
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
