import itertools
from typing import Optional, Set

import log

from .models import BallotWebsite, Election, Precinct


def scrape_ballots(
    *,
    start: int = 1,
    limit: Optional[int] = None,
    max_election_error_count: int = 3,
    max_ballot_error_count: int = 100,
):
    last_election = Election.objects.exclude(active=True).last()
    current_election = Election.objects.filter(active=True).first()

    if current_election:
        starting_election_id = current_election.mi_sos_id
    elif last_election:
        starting_election_id = last_election.mi_sos_id + 1
    else:
        log.warning("No active elections")
        return

    error_count = 0
    for election_id in itertools.count(starting_election_id):
        ballot_count = _scrape_ballots_for_election(
            election_id, start, limit, max_ballot_error_count
        )

        if ballot_count:
            error_count = 0
        else:
            error_count += 1

        if error_count >= max_election_error_count:
            log.info(f'No more ballots to scrape')
            break

        if limit and ballot_count >= limit:
            log.info(f'Stopping after fetching {ballot_count} ballot(s)')
            break


def _scrape_ballots_for_election(
    election_id: int,
    starting_precinct_id: int,
    limit: Optional[int],
    max_ballot_error_count: int,
) -> int:
    log.info(f'Scrapping ballots for election {election_id}')
    log.info(f'Starting from precinct {starting_precinct_id}')
    if limit:
        log.info(f'Stopping after {limit} ballots')

    ballot_count = 0
    error_count = 0

    for precinct_id in itertools.count(starting_precinct_id):
        website, created = BallotWebsite.objects.get_or_create(
            mi_sos_election_id=election_id, mi_sos_precinct_id=precinct_id
        )
        if created:
            log.info(f'Discovered new website: {website}')
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

        if error_count >= max_ballot_error_count:
            log.info(f'No more ballots to scrape for election {election_id}')
            break

    return ballot_count


def parse_ballots(*, refetch: bool = False):
    for election in Election.objects.filter(active=True):

        precincts: Set[Precinct] = set()

        for website in BallotWebsite.objects.filter(
            mi_sos_election_id=election.mi_sos_id, valid=True
        ).order_by('-mi_sos_precinct_id'):

            ballot = website.convert()

            if ballot.precinct in precincts:
                log.warn(f'Duplicate website: {website}')
            else:
                precincts.add(ballot.precinct)

                ballot.website = website

                try:
                    ballot.parse()
                except Exception as e:  # pylint: disable=broad-except
                    if refetch:
                        log.warning(str(e))
                        ballot.website.fetch()
                        ballot.website.validate()
                        ballot.website.scrape()
                        ballot.parse()
                    else:
                        raise e from None

                ballot.save()
