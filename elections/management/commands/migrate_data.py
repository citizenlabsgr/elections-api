# pylint: disable=no-self-use

from django.core.management.base import BaseCommand

import log

from elections.models import Party


class Command(BaseCommand):
    help = "Migrate data between existing models and initialize constants"

    def handle(self, *_args, **_kwargs):
        log.init(reset=True)
        self.initialize_parties()

    def initialize_parties(self):
        for name, color in [
            # Placeholders
            ("Nonpartisan", ''),
            ("No Party Affiliation", '#C8CCD1'),
            # Parties
            ("Democratic", '#3333FF'),
            ("Green", '#00A95C'),
            ("Libertarian", '#ECC850'),
            ("Natural Law", '#FFF7D6'),
            ("Republican", '#E81B23'),
            ("U.S. Taxpayers", '#A356DE'),
            ("Working Class", '#A30000'),
        ]:
            Party.objects.update_or_create(
                name=name, defaults=dict(color=color)
            )
