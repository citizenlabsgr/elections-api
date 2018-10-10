# pylint: disable=no-self-use

from django.conf import settings
from django.core.management.base import BaseCommand

import bugsnag
import log

from elections.models import Ballot, Election, Precinct


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
        election = Election.objects.filter(active=True).get()

        for precinct in Precinct.objects.all():
            precincts = Precinct.objects.filter(mi_sos_id=precinct.mi_sos_id)
            if len(precincts) == 2:

                count_0 = 0
                if precincts[0].ward:
                    count_0 += 1
                if precincts[0].number:
                    count_0 += 1

                count_1 = 0
                if precincts[1].ward:
                    count_1 += 1
                if precincts[1].number:
                    count_1 += 1

                if count_0 > count_1:
                    duplicate = precincts[1]
                else:
                    duplicate = precincts[0]

                self.stdout.write(f'Deleted duplicate precinct: {duplicate}')
                duplicate.delete()

        for ballot in Ballot.objects.filter(election=election):

            websites = ballot.websites.order_by('mi_sos_precinct_id')
            count = len(websites)
            log.debug(f'Ballot {ballot.id}: {count} website(s)')

            if count == 1:
                website = websites[0]

                if not website.source:
                    self.stdout.write(f'Set source: {website}')
                    website.source = True
                    website.save()

                if ballot.precinct.mi_sos_id != website.mi_sos_precinct_id:
                    self.stdout.write(f'Set precinct ID: {ballot.precinct}')
                    assert website.mi_sos_precinct_id
                    ballot.precinct.mi_sos_id = website.mi_sos_precinct_id
                    ballot.precinct.save()

            elif count > 1:
                newest = max(websites, key=lambda _: _.mi_sos_precinct_id)
                if newest.table_count:
                    for website in websites:
                        if website.id == newest.id and not website.source:
                            self.stdout.write(f'Set source: {website}')
                            website.source = True
                            website.save()
                        elif website.source:
                            website.source = False
                            website.save()
                else:
                    log.warn(f'Ballot has {count} websites: {ballot}')
                    for website in websites:
                        log.info(f'{website.table_count} tables: {website}')
            else:
                log.warn(f'Ballot has no websites: {ballot}')
