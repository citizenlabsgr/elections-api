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
            websites = ballot.websites.all()
            count = len(websites)
            log.debug(f'Ballot {ballot.id}: {count} website(s)')

            if count == 1:
                website = websites[0]
                if not website.source:
                    self.stdout.write(f'Set source of truth: {website}')
                    website.source = True
                    website.save()
                if ballot.precinct.mi_sos_id != website.mi_sos_precinct_id:
                    self.stdout.write(f'Set precinct ID: {ballot.precinct}')
                    assert website.mi_sos_precinct_id
                    ballot.precinct.mi_sos_id = website.mi_sos_precinct_id
                    ballot.precinct.save()

            elif count > 1:
                log.warn(f'Ballot has {count} websites: {ballot}')
                for website in websites:
                    log.info(f'{website.table_count} tables: {website}')

            else:
                log.warn(f'Ballot has no websites: {ballot}')

    def get_current_election(self) -> Election:
        return (
            Election.objects.filter(active=True)
            .exclude(mi_sos_id=None)
            .first()
        )
