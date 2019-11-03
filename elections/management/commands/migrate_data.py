# pylint: disable=no-self-use

import sys
from datetime import timedelta
from pathlib import Path
from typing import Dict, Generator, Tuple

from django.core.management.base import BaseCommand
from django.utils import timezone

import log

from elections import defaults
from elections.helpers import normalize_jurisdiction
from elections.models import District, DistrictCategory, Election, Party, Position


class Command(BaseCommand):
    help = "Initialize contants and migrate data between existing models"

    def handle(self, verbosity: int, **_kwargs):
        log.init(verbosity=verbosity if '-v' in sys.argv else 2)

        defaults.initialize_parties()
        defaults.initialize_districts()

        self.update_elections()
        self.update_jurisdictions()

        self.import_descriptions()
        self.export_descriptions()

    def update_elections(self):
        for election in Election.objects.filter(active=True):
            age = timezone.now() - timedelta(weeks=3)
            if election.date < age.date():
                log.info(f'Deactivating election: {election}')
                election.active = False
                election.save()

    def update_jurisdictions(self):
        jurisdiction = DistrictCategory.objects.get(name="Jurisdiction")
        for district in District.objects.filter(category=jurisdiction):

            old = district.name
            new = normalize_jurisdiction(district.name)

            if new != old:

                if District.objects.filter(category=jurisdiction, name=new):
                    log.warning(f'Deleting district {old!r} in favor of {new!r}')
                    district.delete()
                else:
                    log.info(f'Renaming district {old!r} to {new!r}')
                    district.name = new
                    district.save()

    def import_descriptions(self):
        for name, description in self._read_descriptions('elections'):
            Election.objects.filter(name=name).update(description=description)

        for name, description in self._read_descriptions('districts'):
            DistrictCategory.objects.filter(name=name).update(description=description)

        for name, description in self._read_descriptions('parties'):
            Party.objects.filter(name=name).update(description=description)

        for name, description in self._read_descriptions('positions'):
            Position.objects.filter(name=name).update(description=description)

    def export_descriptions(self):
        elections = {}
        for election in Election.objects.all():
            elections[election.name] = election.description
        self._write('elections', elections)

        districts = {}
        for category in DistrictCategory.objects.all():
            districts[category.name] = category.description
        self._write('districts', districts)

        parties = {}
        for party in Party.objects.all():
            parties[party.name] = party.description
        self._write('parties', parties)

        positions = {}
        for position in Position.objects.all():
            positions[position.name] = position.description
        self._write('positions', positions)

    def _read_descriptions(self, name: str) -> Generator[Tuple[str, str], None, None]:
        for path in Path(f'content/{name}').iterdir():
            if path.name.startswith('.'):
                continue
            log.debug(f'Reading {path}')
            yield path.stem, path.read_text().strip()

    def _write(self, name: str, data: Dict) -> None:
        for key, value in sorted(data.items()):
            path = Path(f'content/{name}/{key}.md')
            with path.open('w') as f:
                log.debug(f'Writing {path}')
                f.write(value + '\n')
