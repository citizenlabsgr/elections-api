# pylint: disable=no-self-use


import warnings
from typing import Set

from django.core.management.base import BaseCommand

import log

from elections.models import BallotWebsite, Election, Precinct


class Command(BaseCommand):
    help = "Convert fetched ballot data into database records"

    def handle(self, verbosity: int, **_kwargs):
        log.init(verbosity=verbosity)

        # https://github.com/citizenlabsgr/elections-api/issues/81
        warnings.simplefilter('once')

        for election in Election.objects.filter(active=True):

            precincts: Set[Precinct] = set()

            for website in BallotWebsite.objects.filter(
                mi_sos_election_id=election.mi_sos_id, valid=True
            ).order_by('-mi_sos_precinct_id'):

                ballot = website.convert()

                if ballot.precinct in precincts:
                    log.warn(f'Duplicate website: {website}')
                else:
                    ballot.website = website
                    ballot.save()
                    precincts.add(ballot.precinct)
