# pylint: disable=unused-argument,unused-variable


import pendulum
import pytest

from elections import commands, defaults
from elections.models import Ballot, BallotWebsite, District, Election


@pytest.fixture
def past_election(db):
    return Election.objects.create(
        name="Unknown Election",
        date=pendulum.parse("2019-10-26", tz='America/Detroit'),
        mi_sos_id=678,
        active=False,
    )


@pytest.fixture
def active_election(db):
    return Election.objects.create(
        name="November Consolidated",
        date=pendulum.parse("2019-11-05", tz='America/Detroit'),
        mi_sos_id=679,
    )


def describe_scrape_ballots():
    def with_no_active_election(expect, db):
        commands.scrape_ballots(ballot_limit=1)

        expect(BallotWebsite.objects.count()) == 0

    def with_past_election(expect, past_election):
        defaults.initialize_districts()

        commands.scrape_ballots(
            ballot_limit=1, max_election_error_count=1, max_ballot_error_count=1
        )

        expect(Election.objects.count()) == 2
        expect(BallotWebsite.objects.count()) == 1


def describe_parse_ballots():
    def with_no_active_election(expect, db):
        commands.parse_ballots()

        expect(Ballot.objects.count()) == 0

    def with_active_election_and_no_scrapped_ballots(expect, active_election):
        commands.parse_ballots()

        expect(Ballot.objects.count()) == 0

    def with_active_election_and_one_scrapped_ballot(expect, active_election):
        defaults.initialize_districts()
        defaults.initialize_parties()

        commands.scrape_ballots(starting_precinct_id=1828, ballot_limit=1)
        commands.parse_ballots()

        expect(Ballot.objects.count()) == 1
        expect(District.objects.count()) == 4
