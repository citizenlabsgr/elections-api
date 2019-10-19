from django.core.management.base import BaseCommand


from elections.models import Election
import log


class Command(BaseCommand):
    help = "Crawl the Michigan SOS website to parse ballots"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            metavar='MI_SOS_ID',
            type=int,
            default=1,
            help='Initial Michigan SOS precinct ID to start from.',
        )
        parser.add_argument(
            '--limit',
            metavar='COUNT',
            type=int,
            help='Maximum number of fetches to perform before stopping.',
        )

    def handle(self, verbosity: int, start: int, limit: int, **_kwargs):
        log.init(verbosity=verbosity)

        last_election = Election.objects.exclude(active=True).last()
        election_id = last_election.mi_sos_id + 1
        precinct_id = start

        log.info(f'Scrapping ballots: election {election_id}, precinct {precinct_id}')
        if limit:
            log.info(f'Stopping after {limit} ballots')

