# pylint: disable=no-self-use


import warnings

from django.core.management.base import BaseCommand

import log


class Command(BaseCommand):
    help = "Convert fetched ballot data into database records"

    def handle(self, verbosity: int, **_kwargs):
        log.init(verbosity=verbosity)

        # https://github.com/citizenlabsgr/elections-api/issues/81
        warnings.simplefilter('once')

        log.c("TODO: sync data")
