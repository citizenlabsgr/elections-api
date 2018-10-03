# pylint: disable=no-self-use

from django.conf import settings
from django.core.management.base import BaseCommand

import bugsnag
import log

from elections.models import Ballot, Election


class Command(BaseCommand):
    help = "Validate ballot websites to select the source of truth"

    def handle(self, *_args, **_kwargs):
        log.init(reset=True)
        try:
            self.run()
        except Exception as e:
            if not settings.DEBUG:
                bugsnag.notify(e)
            raise e from None

    def run(self):
        election = self.get_current_election()
        for ballot in Ballot.objects.filter(election=election):
            count = len(ballot.websites.all())
            self.stdout.write(f'Ballot {ballot.id}: {count} website(s)')

    def get_current_election(self) -> Election:
        return (
            Election.objects.filter(active=True)
            .exclude(mi_sos_id=None)
            .first()
        )
