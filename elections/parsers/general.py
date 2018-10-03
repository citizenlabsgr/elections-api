from typing import Optional

import bugsnag
import log
from bs4 import element

from elections import helpers
from elections.models import (
    Candidate,
    District,
    DistrictCategory,
    Election,
    Party,
    Position,
    Precinct,
    Proposal,
)


def handle_main_wrapper(table: element.Tag, **_) -> bool:
    if table.get('class') == ['mainTable']:
        td = table.find('td', class_='section')
        log.debug(f'Found header: {td.text!r}')
        if "partisan section" in td.text.lower():
            return True
    return False


def handle_general_wrapper(table: element.Tag, **_) -> bool:
    if table.get('class') == ['generalTable']:
        td = table.find('td', class_='section')
        log.debug(f'Found header: {td.text!r}')
        if "partisan section" in td.text.lower():
            return True
    return False


def handle_partisan_section(
    table: element.Tag,
    *,
    election: Election,
    precinct: Precinct,
    party: Optional[Party],
    **_,
) -> Optional[Position]:
    if party and party.name == "Nonpartisan":
        return None
    if table.get('class') != ['tblOffice']:
        return None
    td = table.find(class_='section')
    if td and td.text == "NONPARTISAN SECTION":
        return None

    # Parse category

    category = None
    td = table.find(class_='division')
    if td:
        category_name = helpers.titleize(td.text)
        if category_name in {"State Board"}:
            log.debug(f'Assuming category from division: {category_name}')
            category = DistrictCategory.objects.get(name="State")
        elif category_name not in {"Congressional", "Legislative", "Delegate"}:
            log.debug(f'Parsing category from division: {td.text!r}')
            category = DistrictCategory.objects.get(name=category_name)

    if not category:
        td = table.find(class_='office')
        if td:
            office = helpers.titleize(td.text)

            if office == "United States Senator":
                log.debug(f'Parsing category from office: {td.text!r}')
                category = DistrictCategory.objects.get(name="State")

            elif office == "Representative In Congress":
                log.debug(f'Parsing category from office: {td.text!r}')
                category = DistrictCategory.objects.get(name="US Congress")
            elif office == "State Senator":
                log.debug(f'Parsing category from office: {td.text!r}')
                category = DistrictCategory.objects.get(name="State Senate")
            elif office == "Representative In State Legislature":
                log.debug(f'Parsing category from office: {td.text!r}')
                category = DistrictCategory.objects.get(name="State House")

    if not category:
        class_ = 'mobileOnly'
        td = table.find(class_=class_)
        if td:
            category_name = helpers.titleize(td.text)
            log.debug(f'Parsing category from {class_!r}: {td.text!r}')
            if category_name in {"State Board"}:
                category = DistrictCategory.objects.get(name="State")
            else:
                category = DistrictCategory.objects.get(name=category_name)

    log.info(f'Parsed {category!r}')
    assert category

    # Parse district

    district = None
    td = table.find(class_='office')
    if td:
        office = helpers.titleize(td.text)
        if category.name == "State":
            log.debug(f'Assuming state position: {office}')
            district = District.objects.get(category=category, name="Michigan")
        elif office in {"Governor", "Governor and Lieutenant Governor"}:
            # TODO: Delete?
            log.debug(f'Parsing district from office: {td.text!r}')
            district = District.objects.get(category=category, name="Michigan")
        elif office == "United States Senator":
            # TODO: Delete?
            log.debug(f'Parsing district from office: {td.text!r}')
            district = District.objects.get(category=category, name="Michigan")

        elif category.name == "County":
            log.debug(f'Parsing district from office: {td.text!r}')
            district = precinct.county

        elif category.name in {"City", "Township"}:
            log.debug(f'Assuming jurisdiction position: {office}')
            district = precinct.jurisdiction

        elif category.name == "Precinct":
            log.debug(f'Parsing district from office: {td.text!r}')
            district = precinct

        else:
            td = table.find(class_='term')
            log.debug(f'Parsing district from term: {td.text!r}')
            assert 'term' not in td.text.lower()
            assert 'vote for' not in td.text.lower()
            district_name = helpers.titleize(td.text)
            district, created = District.objects.get_or_create(
                category=category, name=district_name
            )
            if created:
                log.warn(f'Added missing district: {district}')

    log.info(f'Parsed {district!r}')
    assert district

    # Parse position

    office = table.find(class_='office').text
    term = table.find_all(class_='term')[-1].text
    log.debug(f'Parsing position from: {office!r} when {term!r}')
    assert 'term' not in office.lower()
    assert 'vote for' not in office.lower()
    position_name = helpers.titleize(office)
    seats = int(term.strip().split()[-1])
    if isinstance(district, Precinct):
        position_name = f'{position_name} ({party} | {district})'
        district = None
    position, _ = Position.objects.get_or_create(
        election=election,
        district=district,
        name=position_name,
        defaults={'seats': seats},
    )
    log.info(f'Parsed {position!r}')
    if position.seats != seats:
        bugsnag.notify(
            f'Number of seats for {position} differs: '
            f'{position.seats} vs. {seats}'
        )

    # Add precinct

    position.precincts.add(precinct)
    position.save()

    # Parse parties

    parties = []
    for td in table.find_all(class_='party'):
        log.debug(f'Parsing party: {td.text!r}')
        party = Party.objects.get(name=td.text.strip())
        log.info(f'Parsed {party!r}')
        parties.append(party)

    log.debug(f'Expecting {len(parties)} candidate(s) for {position}')

    # Parse candidates

    for index, td in enumerate(table.find_all(class_='candidate')):

        log.debug(f'Parsing candidate: {td.text!r}')
        candidate_name = td.text.strip()

        if candidate_name == "No candidates on ballot":
            log.warn(f'No {party} candidates for {position}')
            break

        if " and " in position.name and index % 2:
            log.warn(f'Skipped running mate: {candidate_name}')
            continue

        party = parties[index // 2]

        candidate, _ = Candidate.objects.get_or_create(
            name=candidate_name, party=party, position=position
        )
        log.info(f'Parsed {candidate!r}')

    return position


def handle_nonpartisan_section(
    table: element.Tag, *, election: Election, precinct: Precinct, **_
) -> Optional[Proposal]:
    td = table.find(class_='section')
    if td and td.text != "NONPARTISAN SECTION":
        return None
    if table.find(class_='proposalTitle'):
        return None

    # Set party

    party = Party.objects.get(name="Nonpartisan")

    # Parse category

    category = None

    td = table.find(class_='division')
    if not category and td:
        division = helpers.titleize(td.text)
        if division in {"Judicial"}:
            pass  # parse category from 'office'
        else:
            log.debug(f'Parsing category from division: {td.text!r}')
            category = DistrictCategory.objects.get(
                name=helpers.clean_district_category(division)
            )

    td = table.find(class_='mobileOnly')
    if not category and td:
        mobileonly = helpers.titleize(td.text)
        if mobileonly not in {"Judicial"}:
            log.debug(f'Parsing category from mobileOnly: {td.text!r}')
            category = DistrictCategory.objects.get(
                name=helpers.clean_district_category(mobileonly)
            )

    td = table.find(class_='office')
    if not category and td:
        office = helpers.titleize(td.text)
        log.debug(f'Parsing category from office: {td.text!r}')
        if office in {"Justice of Supreme Court"}:
            category = DistrictCategory.objects.get(name="State")
        else:
            category = DistrictCategory.objects.get(
                name=helpers.clean_district_category(office)
            )

    log.info(f'Parsed {category!r}')
    assert category

    # Parse district

    district = None
    td = table.find(class_='term')
    if td:
        if category.name == "State":
            log.debug(f'Assuming district is state from {category}')
            district = District.objects.get(category=category, name="Michigan")
        elif category.name in {"City", "Township"}:
            log.debug(f'Assuming district is jurisdiction from {category}')
            district = precinct.jurisdiction
        else:
            log.debug(f'Parsing district from term: {td.text!r}')
            assert 'term' not in td.text.lower()
            assert 'vote for' not in td.text.lower()
            district_name = helpers.titleize(td.text)
            district, created = District.objects.get_or_create(
                category=category, name=district_name
            )
            if created:
                log.warn(f'Added missing district: {district}')

    log.info(f'Parsed {district!r}')
    assert district

    # Parse position

    office = table.find(class_='office').text
    terms = table.find_all(class_='term')
    term = ''
    if len(terms) >= 2:
        if "term" in terms[-2].text.lower():
            term = terms[-2].text
        if (
            "position" in terms[1].text.lower()
            or "judgeship" in terms[1].text.lower()
        ):
            assert term, f'Expected term: {term!r}'
            term += f', {terms[1].text}'
        seats = terms[-1].text
    else:
        seats = terms[-1].text
    log.debug(f'Parsing position from: {office!r} for {term!r} when {seats!r}')
    assert "vote for" in seats.lower()
    position, _ = Position.objects.get_or_create(
        election=election,
        district=district,
        name=helpers.titleize(office),
        term=term,
        seats=int(seats.strip().split()[-1]),
    )
    log.info(f'Parsed {position!r}')
    assert position

    # Add precinct

    position.precincts.add(precinct)
    position.save()

    # Parse candidates

    for td in table.find_all(class_='candidate'):
        log.debug(f'Parsing candidate: {td.text!r}')
        candidate_name = td.text.strip()

        if candidate_name == "No candidates on ballot":
            log.warn(f'No {party} candidates for {position}')
            break

        candidate, _ = Candidate.objects.get_or_create(
            name=candidate_name, party=party, position=position
        )
        log.info(f'Parsed {candidate!r}')

    return position


def handle_general_header(table: element.Tag, **_) -> bool:
    if table.get('class') == ['mainTable']:
        td = table.find('td', class_='section')
        log.debug(f'Found header: {td.text!r}')
        if "nonpartisan section" in td.text.lower():
            return True
    return False


def handle_proposals_header(table: element.Tag, **_) -> bool:
    if table.get('class') == None:
        td = table.find('td', class_='section')
        if td:
            header = td.text.strip()
            log.debug(f'Found header: {header!r}')
            return True
    return False


def handle_proposals(
    table: element.Tag,
    *,
    election: Election,
    precinct: Precinct,
    district: Optional[District],
    **_,
) -> Optional[Proposal]:
    if table.get('class') != ['proposal']:
        return None

    # Parse category

    category = None
    td = table.find(class_='division')
    if td:
        log.debug(f'Parsing category from division: {td.text!r}')
        category_name = helpers.clean_district_category(
            helpers.titleize(td.text.split("PROPOSALS")[0])
        )
        if category_name == "Authority":
            log.warn('Assuming category is county')
            category_name = "County"
        category = DistrictCategory.objects.get(name=category_name)
    else:
        log.debug(f'Reusing category from previous district: {district}')
        assert district
        category = district.category

    log.info(f'Parsed {category!r}')
    assert category

    # Parse district

    if category.name == "State":
        log.debug('Inferring district as state')
        district = District.objects.get(category=category, name="Michigan")
    elif category.name == "County":
        log.debug('Inferring district as county')
        district = precinct.county
    elif category.name in {"Jurisdiction", "City", "Township"}:
        log.debug('Inferring district as jurisdiction')
        district = precinct.jurisdiction
    else:
        proposal_title = table.find(class_='proposalTitle').text
        proposal_text = table.find(class_='proposalText').text
        log.debug(f'Parsing district from title: {proposal_title!r}')
        title = helpers.titleize(proposal_title)
        if category.name in title:
            district = District.objects.get(
                category=category, name=title.split(category.name)[0].strip()
            )
        elif precinct.jurisdiction.name in proposal_text:
            log.warn('Assuming district is jurisdiction from proposal')
            district = precinct.jurisdiction
        elif precinct.county.name in proposal_text:
            log.warn('Assuming district is county from proposal')
            district = precinct.county
        else:
            assert 0, f'Could not determine district: {table}'

    log.info(f'Parsed {district!r}')
    assert district

    # Parse proposal

    proposal_title = table.find(class_='proposalTitle').text
    proposal_text = table.find(class_='proposalText').text
    log.debug(f'Parsing proposal from text: {proposal_text!r}')
    proposal, _ = Proposal.objects.get_or_create(
        election=election,
        district=district,
        name=helpers.titleize(proposal_title),
        description=proposal_text.strip(),
    )
    log.info(f'Parsed {proposal!r}')

    # Add precinct

    proposal.precincts.add(precinct)
    proposal.save()

    return proposal
