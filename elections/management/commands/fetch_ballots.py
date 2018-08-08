
from random import random

import bugsnag
import log

from elections import models

from ._bases import MichiganCrawler


class Command(MichiganCrawler):
    help = "Fetch ballot information from the Michigan SOS website"

    def handle(self, start, limit, randomize, *_args, **_kwargs):
        log.init(reset=True)
        try:
            self.fetch_ballots_html(start, limit, randomize)
        except Exception as e:
            bugsnag.notify(e)
            raise e

    def fetch_ballots_html(
        self,
        starting_mi_sos_precinct_id: int,
        max_ballots_count: int,
        randomly_skip_precincts: bool,
    ):
        for election in models.Election.objects.filter(active=True):

            for precinct in models.Precinct.objects.order_by(
                'mi_sos_id'
            ).filter(mi_sos_id__gte=starting_mi_sos_precinct_id):

                # Skip randomly if requested
                if (
                    randomly_skip_precincts
                    and precinct.mi_sos_id != starting_mi_sos_precinct_id
                    and random() < 0.8
                ):
                    continue

                # Get ballot
                ballot, created = models.Ballot.objects.get_or_create(
                    election=election, precinct=precinct
                )
                if created:
                    self.stdout.write(f'Created ballot: {ballot}')

                # Get website
                if not ballot.website:
                    website, created = models.BallotWebsite.objects.get_or_create(
                        mi_sos_election_id=ballot.election.mi_sos_id,
                        mi_sos_precinct_id=ballot.precinct.mi_sos_id,
                    )
                    if created:
                        self.stdout.write(f'Created website: {website}')
                        website.fetch()
                        website.save()
                    ballot.website = website
                    ballot.save()

                # Fetch website
                if ballot.website.stale(fuzz=0.5) and ballot.website.fetch():
                    self.stdout.write(f'Updated website: {ballot.website}')
                    ballot.website.save()

                # Parse website
                ballot.website.parse()

                # Stop early if requested
                count = models.Ballot.objects.count()
                if max_ballots_count and count >= max_ballots_count:
                    self.stdout.write(f'Stopping at {count} ballot(s)')
                    return
