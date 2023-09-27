import itertools
from datetime import timedelta

import log
from django.utils import timezone

from .models import BallotWebsite, Election, Precinct


def update_elections():
    for election in Election.objects.filter(active=True):
        age = timezone.now() - timedelta(weeks=2)
        if election.date < age.date():
            log.info(f"Deactivating election: {election}")

            while True:
                websites = BallotWebsite.objects.filter(
                    mvic_election_id=election.mvic_id, valid=False
                )
                if not websites.exists():
                    break
                log.info("Deleting 1000 invalid ballot websites")
                for website in websites[:1000]:
                    website.delete()

            election.active = False
            election.save()


def scrape_ballots(
    *,
    starting_election_id: int | None = None,
    starting_precinct_id: int = 1,
    ballot_limit: int | None = None,
    max_election_error_count: int = 5,
    max_ballot_error_count: int = 40000,
):
    current_election = Election.objects.filter(active=True).last()
    last_election = Election.objects.exclude(active=True).first()
    log.info(f"Current election: {current_election}")
    log.info(f"Last election: {last_election}")

    if starting_election_id is not None:
        pass  # use the provided ID
    elif current_election:
        starting_election_id = current_election.mvic_id
    elif last_election:
        starting_election_id = last_election.mvic_id + 1
    else:
        log.warn("No active elections")
        return

    error_count = 0
    for election_id in itertools.count(starting_election_id):
        ballot_count = _scrape_ballots_for_election(
            election_id, starting_precinct_id, ballot_limit, max_ballot_error_count
        )

        if ballot_count:
            error_count = 0
        else:
            error_count += 1

        if error_count >= max_election_error_count:
            log.info("No more elections to scrape")
            break

        if ballot_limit and ballot_count >= ballot_limit:
            log.info(f"Stopping after fetching {ballot_count} ballot(s)")
            break


def _scrape_ballots_for_election(
    election_id: int,
    starting_precinct_id: int,
    limit: int | None,
    max_ballot_error_count: int,
) -> int:
    log.info(f"Scrapping ballots for election {election_id}")
    log.info(f"Starting from precinct {starting_precinct_id}")
    if limit:
        log.info(f"Stopping after {limit} ballots")

    ballot_count = 0
    error_count = 0

    for precinct_id in itertools.count(starting_precinct_id):
        website: BallotWebsite
        website, created = BallotWebsite.objects.get_or_create(
            mvic_election_id=election_id, mvic_precinct_id=precinct_id
        )
        if created:
            log.info(f"Discovered new website: {website}")

        if website.stale or limit:
            website.fetch()
            website.validate() and website.scrape() and website.convert()
        if website.valid:
            ballot_count += 1
            error_count = 0
        else:
            error_count += 1

        if limit and ballot_count >= limit:
            break

        if error_count >= 1000 and not ballot_count:
            log.warn(f"No ballots to scrape for election {election_id}")
            break

        if error_count > 1000:
            log.warn(
                f"Found {ballot_count} ballots with {error_count} successive errors"
            )

        if error_count >= max_ballot_error_count:
            log.info(f"No more ballots to scrape for election {election_id}")
            break

    return ballot_count


def parse_ballots(*, election_id: int | None = None):
    if election_id:
        elections = Election.objects.filter(mvic_id=election_id)
    else:
        elections = Election.objects.filter(active=True)

    for election in elections:
        _parse_ballots_for_election(election)


def _parse_ballots_for_election(election: Election):
    log.info(f"Parsing ballots for election {election.mvic_id}")

    precincts: set[Precinct] = set()

    websites = (
        BallotWebsite.objects.filter(mvic_election_id=election.mvic_id, valid=True)
        .order_by("mvic_precinct_id")
        .defer("mvic_html", "data")
    )
    log.info(f"Mapping {websites.count()} websites to ballots")

    for website in websites:
        if not website.data:
            website.scrape()

        ballot = website.convert()
        precincts.add(ballot.precinct)

        if ballot.stale:
            ballot.parse()

    log.info(f"Parsed ballots for {len(precincts)} unique precincts")
