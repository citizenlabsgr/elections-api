from django.core.management.base import BaseCommand


class MichiganCrawler(BaseCommand):  # pylint: disable=abstract-method
    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            metavar='MI_SOS_ID',
            type=int,
            default=1,
            help='Initial MI SOS precinct ID to start from.',
        )
        parser.add_argument(
            '--limit',
            metavar='COUNT',
            type=int,
            help='Number of objects to update before stopping.',
        )
        parser.add_argument(
            '--randomize',
            action='store_true',
            default=False,
            help='Randomly skip precincts for testing purposes.',
        )
