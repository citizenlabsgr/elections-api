# pylint: disable=no-self-use

import sys
from datetime import timedelta
from pathlib import Path
from typing import Dict, Generator, Tuple

from django.core.management.base import BaseCommand
from django.utils import timezone

import log

from elections import defaults, helpers
from elections.models import District, DistrictCategory, Election, Position


class Command(BaseCommand):
    help = "Initialize contants and migrate data between existing models"

    def handle(self, verbosity: int, **_kwargs):
        log.reset()
        log.init(verbosity=verbosity if '-v' in sys.argv[-1] else 2)

        defaults.initialize_parties()
        defaults.initialize_districts()

        self.update_elections()
        self.update_jurisdictions()

        self.import_descriptions()
        self.export_descriptions()

    def update_elections(self):
        for election in Election.objects.filter(active=True):
            age = timezone.now() - timedelta(weeks=2)
            if election.date < age.date():
                log.info(f'Deactivating election: {election}')
                election.active = False
                election.save()

    def update_jurisdictions(self):
        jurisdiction = DistrictCategory.objects.get(name="Jurisdiction")
        for district in District.objects.filter(category=jurisdiction):
            old = district.name
            new = helpers.normalize_jurisdiction(old)
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
            elections = Election.objects.filter(name=name)
            if elections:
                for election in elections:
                    if description and election.description != description:
                        log.info(f'Updating description for {name}')
                        election.description = description
                        election.save()
            else:
                log.warning(f'Election not found in database: {name}')

        for name, description in self._read_descriptions('districts'):
            try:
                category = DistrictCategory.objects.get(name=name)
            except DistrictCategory.DoesNotExist as e:
                message = f'District category not found in database: {name}'
                if name in {'Precinct'}:
                    log.warning(message)
                else:
                    log.error(message)
                    raise e from None
            if description and category.description != description:
                log.info(f'Updating description for {name}')
                category.description = description
                category.save()

        for name, description in self._read_descriptions('positions'):
            positions = Position.objects.filter(name=name)
            if positions:
                for position in positions:
                    if description and position.description != description:
                        log.info(f'Updating description for {name}')
                        position.description = description
                        position.save()
            else:
                log.warning(f'Position not found in database: {name}')

    def export_descriptions(self):
        elections = {}
        for election in Election.objects.all():
            elections[election.name] = election.description
        self._write('elections', elections)

        districts = {}
        for category in DistrictCategory.objects.all():
            districts[category.name] = category.description
        self._write('districts', districts)

        positions = {}
        for position in Position.objects.all():
            name = position.name.split('(')[0].strip()
            positions[name] = position.description
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
