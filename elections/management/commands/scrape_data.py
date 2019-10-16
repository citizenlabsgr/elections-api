from django.core.management.base import BaseCommand


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

    def handle(self, start: int, limit: int, **_kwargs):
        self.stdout.write(f'Scraping ballots starting at precinct {start}')
        if limit:
            self.stdout.write(f'Stopping after {limit} ballots')
