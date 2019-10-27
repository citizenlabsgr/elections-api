import log

from .models import District, DistrictCategory, Party


def initialize_parties():
    for name, color in [
        # Placeholders
        ("Nonpartisan", '#999'),
        ("No Party Affiliation", '#999'),
        # Parties
        ("Democratic", '#3333FF'),
        ("Green", '#00A95C'),
        ("Libertarian", '#ECC850'),
        ("Natural Law", '#FFF7D6'),
        ("Republican", '#E81B23'),
        ("U.S. Taxpayers", '#A356DE'),
        ("Working Class", '#A30000'),
    ]:
        party, created = Party.objects.update_or_create(
            name=name, defaults=dict(color=color)
        )
        if created:
            log.info(f'Added party: {party}')


def initialize_districts():
    state, created = DistrictCategory.objects.get_or_create(name="State")
    if created:
        log.info(f'Added district category: {state}')

    for name in [
        # State
        "County",
        "Jurisdiction",
        "Precinct",
        # Local
        "City",
        "District Library",
        "Local School",
        "Intermediate School",
        "Township",
        "Metropolitan",
        "Village",
        "Authority",
        "Library",
    ]:
        category, created = DistrictCategory.objects.get_or_create(name=name)
        if created:
            log.info(f'Added district category: {category}')

    michigan, created = District.objects.get_or_create(category=state, name="Michigan")
    if created:
        log.info(f'Added district: {michigan}')
