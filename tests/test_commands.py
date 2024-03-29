# pylint: disable=unused-argument,unused-variable


from datetime import datetime

import pytest
from django.utils import timezone

from elections import commands, defaults
from elections.models import Ballot, BallotWebsite, District, Election


@pytest.fixture
def past_election(db):
    return Election.objects.create(
        name="Unknown Election",
        date=timezone.make_aware(datetime(2020, 6, 6)),
        mvic_id=681,
        active=False,
    )


@pytest.fixture
def active_election(db):
    return Election.objects.create(
        name="State Primary",
        date=timezone.make_aware(datetime(2020, 8, 4)),
        mvic_id=682,
    )


def describe_update_elections():
    def it_marks_past_elections_inactive(expect, past_election):
        past_election.active = True
        past_election.save()

        commands.update_elections()

        past_election.refresh_from_db()
        expect(past_election.active) == False


def describe_scrape_ballots():
    @pytest.mark.vcr
    def with_no_active_election(expect, db):
        commands.scrape_ballots(ballot_limit=1)

        expect(BallotWebsite.objects.count()) == 0

    @pytest.mark.vcr
    def with_past_election(expect, past_election):
        defaults.initialize_districts()

        commands.scrape_ballots(
            ballot_limit=1, max_election_error_count=1, max_ballot_error_count=1
        )

        expect(Election.objects.count()) == 2
        expect(BallotWebsite.objects.count()) == 1


def describe_parse_ballots():
    @pytest.mark.vcr
    def with_no_active_election(expect, db):
        commands.parse_ballots()

        expect(Ballot.objects.count()) == 0

    @pytest.mark.vcr
    def with_active_election_and_no_scrapped_ballots(expect, active_election):
        commands.parse_ballots()

        expect(Ballot.objects.count()) == 0

    @pytest.mark.vcr
    def with_active_election_and_one_scrapped_ballot(expect, active_election):
        defaults.initialize_districts()
        defaults.initialize_parties()

        commands.scrape_ballots(starting_precinct_id=1828, ballot_limit=1)
        commands.parse_ballots()

        expect(Ballot.objects.count()) == 1
        expect(District.objects.count()) == 7
