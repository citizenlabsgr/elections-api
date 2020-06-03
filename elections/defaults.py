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
        # Precinct
        "County",  # e.g. Kent
        "Jurisdiction",  # e.g. City of Grand Rapids
        "Ward",  # e.g. City of Grand Rapids, Ward 3
        "Precinct",  # e.g. City of Grand Rapids, Ward 3, Precinct 2
        # Local
        "School",  # e.g. Grand Rapids Public Schools
        "Local School",
        "Intermediate School",  # e.g. Kent ISD
        "Community College",  # e.g. Grand Rapids Community College
        "Library",
        "District Library",
        # Municipalities
        "City",
        "Township",
        "Village",
        "Metropolitan",
        "Authority",
        # Congress
        "County Commissioner",  # e.g. 15th District
        "State House",  # e.g. 75th District
        "State Senate",  # e.g. 29th District
        "US Congress",  # e.g. 3rd District
        # Courts
        "Court of Appeals",  # e.g. 3rd District
        "Circuit Court",  # e.g. 17th Circuit
        "Probate Court",  # e.g. Kent County Probate Court
        "Probate District Court",
        "District Court",  # e.g. 61st District
        "Municipal Court",
    ]:
        category, created = DistrictCategory.objects.get_or_create(name=name)
        if created:
            log.info(f'Added district category: {category}')

    michigan, created = District.objects.get_or_create(category=state, name="Michigan")
    if created:
        log.info(f'Added district: {michigan}')
