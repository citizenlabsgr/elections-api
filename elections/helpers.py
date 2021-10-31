import re
import string
import time
from contextlib import contextmanager
from datetime import date, datetime
from importlib import resources
from typing import Any, Dict, Generator, List, Optional, Tuple

import log
import pomace
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from fake_useragent import UserAgent
from nameparser import HumanName

from . import exceptions
from .constants import MVIC_URL


useragent = UserAgent()

###############################################################################
# Shared helpers


@contextmanager
def mvic_session() -> Generator[requests.Session, None, None]:
    with resources.path('config', 'mvic.sos.state.mi.us.pem') as path:
        session = requests.Session()
        session.verify = str(path)
        session.headers['User-Agent'] = useragent.random
        yield session


def fetch(url: str, expected_text: str) -> str:
    with mvic_session() as session:
        response = session.get(url)

    if response.status_code >= 400:
        log.error(f'MVIC status code: {response.status_code}')
        raise exceptions.ServiceUnavailable()

    text = response.text.strip()
    assert expected_text in text, f'{expected_text!r} not found on {url}'
    return text


def visit(url: str, expected_text: str) -> pomace.Page:
    page = pomace.visit(url)
    if expected_text not in page:
        log.info(f"Revisiting {url} with session cookies")
        page = pomace.visit(url)
    assert expected_text in page, f'{expected_text!r} not found on {url}'
    return page


def titleize(text: str) -> str:
    return (
        string.capwords(text)
        .replace(" Of ", " of ")
        .replace(" To ", " to ")
        .replace(" And ", " and ")
        .replace(" In ", " in ")
        .replace(" By ", " by ")
        .replace(" At ", " at ")
        .replace(" The ", " the ")
        .replace("U.s.", "U.S.")
        .replace("Ii.", "II.")
        .replace("Iii.", "III.")
        .replace("Iv.", "IV.")
        .replace("Ii ", "II ")
        .replace("Iii ", "III ")
        .replace("Iv ", "IV ")
        .replace("(d", "(D")
        .replace("(l", "(L")
        .replace("(r", "(R")
        .replace("Vice-president", "Vice-President")
        .strip()
    )


def normalize_position(text: str) -> str:
    text = text.split(' (')[0].split(' - ')[0]
    if text.startswith("Alderman"):
        text = "Alderman"
    elif text == "Board Member Bath Township Library":
        text = "Township Library Board Member"
    elif text.startswith("Delta College Board of Trustees Member"):
        text = "Delta College Board of Trustees Member"
    elif text.endswith("Village Charter Commission"):
        text = "Village Charter Commission"
    return titleize(text)


def normalize_candidate(text: str) -> str:
    if '\n' in text:
        log.debug(f'Handling running mate: {text}')
        text1, text2 = text.split('\n')
        name1 = HumanName(text1.strip())
        name2 = HumanName(text2.strip())
        name1.capitalize()
        name2.capitalize()

        if " of " in str(name2):
            log.debug(f"Skipped non-person running mate: {name2}")
            return str(name1)

        return str(name1) + ' & ' + str(name2)

    name = HumanName(text.strip())
    name.capitalize()
    return str(name)


def normalize_district(text: str) -> str:
    return text.replace("District District", "District").replace(" Isd", " ISD").strip()


def normalize_jurisdiction(name: str) -> str:
    name = titleize(name)

    for kind in {'City', 'Township', 'Village'}:
        if name.startswith(kind):
            return name.replace(" Charter", "")

    for kind in {'City', 'Township', 'Village'}:
        if name.endswith(' ' + kind):
            name = kind + ' of ' + name[: -len(kind) - 1]
            return name.replace(" Charter", "")

    return name


def build_mvic_url(election_id: int, precinct_id: int) -> str:
    assert election_id, "MVIC election ID is missing"
    assert precinct_id, "MVIC precinct ID is missing"
    return f'{MVIC_URL}/Voter/GetMvicBallot/{precinct_id}/{election_id}/'


###############################################################################
# Registration helpers


def fetch_registration_status_data(voter):
    url = f'{MVIC_URL}/Voter/SearchByName'
    log.info(f"Submitting form on {url}")
    with mvic_session() as session:
        try:
            response = session.post(
                url,
                headers={'Content-Type': "application/x-www-form-urlencoded"},
                data={
                    'FirstName': voter.first_name,
                    'LastName': voter.last_name,
                    'NameBirthMonth': voter.birth_month,
                    'NameBirthYear': voter.birth_year,
                    'ZipCode': voter.zip_code,
                },
                timeout=10,
            )
        except requests.exceptions.ConnectionError as e:
            log.error(f'MVIC connection error: {e}')
            raise exceptions.ServiceUnavailable()

    if response.status_code >= 400:
        log.error(f'MVIC status code: {response.status_code}')
        raise exceptions.ServiceUnavailable()

    html = BeautifulSoup(response.text, 'html.parser')

    # Parse registration
    registered = None
    for delay in [0, 1]:
        time.sleep(delay)
        if "Yes, you are registered!" in response.text:
            registered = True
            break
        if "No voter record matched your search criteria" in response.text:
            registered = False
            break
        log.warn("Unable to determine registration status")

    # Parse moved status
    recently_moved = "you have recently moved" in response.text

    # Parse ballot status
    ballot = "Ballot preview" in response.text

    # Parse absentee status
    absentee = "You are on the permanent absentee voter list" in response.text

    # Parse absentee dates
    absentee_dates: Dict[str, Optional[date]] = {
        "Application Received": None,
        "Ballot Sent": None,
        "Ballot Received": None,
    }
    element = html.find(id='lblAbsenteeVoterInformation')
    if element:
        strings = list(element.strings) + [""] * 20
        for index, key in enumerate(absentee_dates):
            text = strings[4 + index * 2].strip()
            if text:
                absentee_dates[key] = datetime.strptime(text, '%m/%d/%Y').date()
    else:
        log.warn("Unable to determine absentee status")

    # Parse districts
    districts: Dict = {}
    element = html.find(id='lblCountyName')
    if element:
        districts['County'] = normalize_district(element.text)
    element = html.find(id='lblJurisdName')
    if element:
        districts['Jurisdiction'] = normalize_jurisdiction(element.text)
    for category_name, element_id in [
        ('Circuit Court', 'lblCircuitName'),
        ('Community College', 'lblCommCollegeName'),
        ('County Commissioner', 'lblCountyCommDistrict'),
        ('Court of Appeals', 'lblAppealsName'),
        ('District Court', 'lblDistCourtName'),
        ('Intermediate School', 'lblIsdName'),
        ('Library', 'lblLibraryName'),
        ('Metropolitan', 'lblMetroName'),
        ('Municipal Court', 'lblMuniCourtName'),
        ('Precinct', 'lblPrecinctNumber'),
        ('Probate Court', 'lblProbateName'),
        ('Probate Court', 'lblProbateName'),
        ('Probate District Court', 'lblProbateDistName'),
        ('School', 'lblSchoolDistrict'),
        ('State House', 'lblHouseDistrict'),
        ('State Senate', 'lblSenateDistrict'),
        ('US Congress', 'lblCongressDistrict'),
        ('Village', 'lblVillageName'),
        ('Ward', 'lblWardNumber'),
    ]:
        element = html.find(id=element_id)
        if element:
            districts[category_name] = normalize_district(
                element.text.strip().strip(",").replace("Not applicable", "")
            )

    # Parse polling location
    polling_location: Dict = {}
    element = html.find(id='lblPollingLocation')
    if element:
        polling_location['PollingLocation'] = element.text.strip()
    element = html.find(id='lblPollAddress')
    if element:
        polling_location['PollAddress'] = element.text.strip()
    element = html.find(id='lblPollCityStateZip')
    if element:
        polling_location['PollCityStateZip'] = element.text.strip()
    else:
        log.warn("Unable to determine polling location")

    # Parse dropbox locations
    dropbox_locations: List[Dict[str, List[str]]] = []
    element = html.find('span', {'class': 'additional-location-badge'})
    if element:
        lines: List[str] = []
        for element in element.next_siblings:
            try:
                text = element.get_text('\n').strip()
            except AttributeError:
                text = element.replace('\xa0', ' ').strip()
            if "Drop box locations" in text:
                lines = []  # the previous lines were above the dropbox list
            elif text and text != "Hours:":
                lines.extend(text.split('\n'))

        for line in lines:
            if line[0].isnumeric():
                dropbox_locations.append({'address': [line], 'hours': []})
            elif len(dropbox_locations[-1]['address']) == 1:
                dropbox_locations[-1]['address'].append(line)
            else:
                dropbox_locations[-1]['hours'].append(line)

        if not dropbox_locations:
            log.warn("No dropbox locations found")
    else:
        log.warn("Unable to determine dropbox locations")

    return {
        "registered": registered,
        "ballot": ballot,
        "absentee": absentee,
        "absentee_dates": absentee_dates,
        "districts": districts,
        "polling_location": polling_location,
        'dropbox_locations': dropbox_locations,
        "recently_moved": recently_moved,
    }


def _find_or_abort(pattern: str, text: str):
    match = re.search(pattern, text)
    assert match, f"Unable to match {pattern!r} to {text!r}"
    return match[1]


def _clean_district_category(text: str):
    words = text.replace("Judge of ", "").split()
    while words and words[-1] == "District":
        words.pop()
    return " ".join(words)


###############################################################################
# Ballot helpers


def fetch_ballot(url: str) -> str:
    log.info(f'Fetching ballot: {url}')
    return fetch(url, "PreviewMvicBallot")


def parse_election(html: str) -> Tuple[str, Tuple[int, int, int]]:
    """Parse election information from ballot HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    header = soup.find(id='PreviewMvicBallot').div.div.div.text

    election_name_text, election_date_text, *_ = header.strip().split('\n')
    election_name = titleize(election_name_text)
    election_date = datetime.strptime(election_date_text.strip(), '%A, %B %d, %Y')

    return election_name, (election_date.year, election_date.month, election_date.day)


def parse_precinct(html: str, url: str) -> Tuple[str, str, str, str]:
    """Parse precinct information from ballot HTML."""

    # Parse county
    match = re.search(r'(?P<county>[^>]+) County, Michigan', html, re.IGNORECASE)
    assert match, f'Unable to find county name: {url}'
    county = titleize(match.group('county'))

    # Parse jurisdiction
    match = None
    for pattern in [
        r'(?P<jurisdiction>[^>]+), Ward (?P<ward>\d+) Precinct (?P<precinct>\d+)',
        r'(?P<jurisdiction>[^>]+),  Precinct (?P<precinct>\d+[A-Z]?)',
        r'(?P<jurisdiction>[^>]+), Ward (?P<ward>\d+)',
    ]:
        match = re.search(pattern, html)
        if match:
            break
    assert match, f'Unable to find precinct information: {url}'
    jurisdiction = normalize_jurisdiction(match.group('jurisdiction'))

    # Parse ward
    try:
        ward = match.group('ward')
    except IndexError:
        ward = ''

    # Parse number
    try:
        precinct = match.group('precinct')
    except IndexError:
        precinct = ''

    return county, jurisdiction, ward, precinct


def parse_district_from_proposal(category: str, text: str, mvic_url: str) -> str:
    patterns = [
        f'[a-z] ((?:[A-Z][A-Za-z.-]+ )+{category})',
        f'\n((?:[A-Z][A-Za-z.-]+ )+{category})',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            name = match[1].strip()
            log.debug(f'{pattern!r} matched: {name}')
            if len(name) < 100:
                return name

    raise ValueError(f'Could not find {category!r} in {text!r} on {mvic_url}')


def parse_ballot(html: str, data: Dict) -> int:
    """Call all parsers to insert ballot data into the provided dictionary."""
    soup = BeautifulSoup(html, 'html.parser')
    ballot = soup.find(id='PreviewMvicBallot').div.div.find_all('div', recursive=False)[
        1
    ]
    count = 0
    count += parse_primary_election_offices(ballot, data)
    count += parse_general_election_offices(ballot, data)
    count += parse_proposals(ballot, data)
    return count


def parse_primary_election_offices(ballot: BeautifulSoup, data: Dict) -> int:
    """Inserts primary election ballot data into the provided dictionary."""
    count = 0

    offices = ballot.find(id='twoPartyPrimaryElectionOffices')
    if not offices:
        return count

    section: Dict = {}
    label = 'primary section'
    data[label] = section

    count += _parse_primary_election_offices("Democratic", ballot, section)
    count += _parse_primary_election_offices("Republican", ballot, section)
    return count


def _parse_primary_election_offices(
    party: str, ballot: BeautifulSoup, data: Dict
) -> int:
    """Inserts primary election ballot data into the provided dictionary."""
    count = 0

    assert ballot.text.find('DEMOCRATIC') < ballot.text.find('REPUBLICAN')
    offices = ballot.find(
        id='columnOnePrimary' if party == 'Democratic' else 'columnTwoPrimary'
    )
    if not offices:
        return count

    section: Dict[str, Any] = {}
    division: Optional[List] = None
    data[party] = section

    for index, item in enumerate(
        offices.find_all(
            'div',
            {
                "class": [
                    "division",
                    "office",
                    "term",
                    "candidate",
                    "financeLink",
                    "party",
                ]
            },
        ),
        start=1,
    ):
        log.debug(f'Parsing office element {index}: {item}')

        if "division" in item['class']:
            label = (
                titleize(item.text).replace(" - Continued", "").replace(" District", "")
            )
            try:
                division = section[label]
            except KeyError:
                division = []
            section[label] = division
            office = None

        elif "office" in item['class']:
            label = normalize_position(item.text)
            assert division is not None, f'Division missing for office: {label}'
            office = {
                'name': label,
                'district': None,
                'type': None,
                'term': None,
                'seats': None,
                'incumbency': None,
                'candidates': [],
            }
            division.append(office)

        elif "term" in item['class']:
            label = item.text
            assert office is not None, f'Office missing for term: {label}'
            if "Incumbent" in label:
                office['type'] = label
            elif "Term" in label:
                office['term'] = label
            elif "Vote for" in label:
                office['seats'] = int(label.replace("Vote for not more than ", ""))
            elif label in {"Incumbent Position", "New Judgeship"}:
                office['incumbency'] = label
            else:
                office['district'] = titleize(label)
            count += 1

        elif "candidate" in item['class']:
            label = normalize_candidate(item.get_text('\n'))
            assert office is not None, f'Office missing for candidate: {label}'
            if label == 'No candidates on ballot':
                continue
            candidate: Dict[str, Any] = {
                'name': label,
                'finance_link': None,
                'party': None,
            }
            office['candidates'].append(candidate)
            count += 1

        elif "financeLink" in item['class']:
            if item.a:
                candidate['finance_link'] = item.a['href']

        elif "party" in item['class']:
            label = titleize(item.text)
            assert candidate is not None, f'Candidate missing for party: {label}'
            candidate['party'] = label or None

    return count


def parse_general_election_offices(ballot: BeautifulSoup, data: Dict) -> int:
    """Inserts general election ballot data into the provided dictionary."""
    count = 0

    offices = ballot.find(id='generalElectionOffices')
    if not offices:
        return count

    section: Optional[Dict] = None
    for index, item in enumerate(
        offices.find_all(
            'div',
            {
                "class": [
                    "section",
                    "division",
                    "office",
                    "term",
                    "candidate",
                    "financeLink",
                    "party",
                ]
            },
        ),
        start=1,
    ):
        log.debug(f'Parsing office element {index}: {item}')

        if "section" in item['class']:
            section = {}
            division: Optional[List] = None
            office: Optional[Dict] = None
            label = item.text.lower()
            if label in data:
                log.warning(f'Duplicate section on ballot: {label}')
                section = data[label]
            else:
                data[label] = section

        elif "division" in item['class']:
            office = None
            label = (
                titleize(item.text).replace(" - Continued", "").replace(" District", "")
            )
            if section is None:
                log.warn(f"Section missing for division: {label}")
                assert list(data.keys()) == ['primary section']
                section = {}
                data['nonpartisan section'] = section
            try:
                division = section[label]
            except KeyError:
                division = []
            section[label] = division
            office = None

        elif "office" in item['class']:
            label = normalize_position(item.text)
            if division is None:
                assert (
                    label == "Library Board Director"
                ), f'Division missing for office: {label}'
                division = []
                assert isinstance(section, dict), f'Section missing for office: {label}'
                section["Library"] = division
            office = {
                'name': label,
                'district': None,
                'type': None,
                'term': None,
                'seats': None,
                'incumbency': None,
                'candidates': [],
            }
            division.append(office)

        elif "term" in item['class']:
            label = item.text
            assert office is not None, f'Office missing for term: {label}'
            if "Incumbent" in label:
                office['type'] = label
            elif "Term" in label:
                office['term'] = label
            elif "Vote for" in label:
                office['seats'] = int(label.replace("Vote for not more than ", ""))
            elif label in {"Incumbent Position", "New Judgeship"}:
                office['incumbency'] = label
            else:
                office['district'] = titleize(label)
            count += 1

        elif "candidate" in item['class']:
            label = normalize_candidate(item.get_text('\n'))
            assert office is not None, f'Office missing for candidate: {label}'
            if label == 'No candidates on ballot':
                if office['seats'] is None:
                    log.warn(f"No seats for offce: {office}")
                    office['seats'] = 1
                continue
            candidate = {'name': label, 'finance_link': None, 'party': None}
            office['candidates'].append(candidate)
            count += 1

        elif "financeLink" in item['class']:
            if item.a:
                candidate['finance_link'] = item.a['href']

        elif "party" in item['class']:
            label = titleize(item.text)
            assert candidate is not None, f'Candidate missing for party: {label}'
            candidate['party'] = label or None

    return count


def parse_proposals(ballot: BeautifulSoup, data: Dict) -> int:
    """Inserts proposal data into the provided dictionary."""
    count = 0

    proposals = ballot.find(id='proposals')
    if not proposals:
        return count

    for index, item in enumerate(
        proposals.find_all(
            'div', {"class": ["section", "division", "proposalTitle", "proposalText"]}
        ),
        start=1,
    ):
        log.debug(f'Parsing proposal element {index}: {item}')

        if "section" in item['class']:
            section: Dict[str, Any] = {}
            division: Optional[List] = None
            proposal = None
            label = item.text.lower()
            data[label] = section

        elif "division" in item['class']:
            proposal = None
            label = (
                titleize(item.text).replace(" Proposals", "").replace(" District", "")
            )
            assert label and "Continued" not in label
            try:
                division = section[label]
            except KeyError:
                division = []
            section[label] = division

        elif "proposalTitle" in item['class']:
            label = item.text.strip()
            if '\n' in label and len(label) > 200:
                log.debug("Parsing proposal text as part of proposal title")
                label, text = label.split('\n', 1)
            else:
                text = None
            if label.isupper():
                label = titleize(label)
            assert division is not None, f'Division missing for proposal: {label}'
            proposal = {'title': label, 'text': text}
            division.append(proposal)

            if proposal['text']:
                count += 1
            else:
                # Handle proposal text missing a class
                label = ""
                element = item.parent.next_sibling
                while element is not None:
                    try:
                        label += '\n\n' + element.get_text('\n\n').strip()
                    except AttributeError:
                        label += '\n\n' + element.strip()
                    element = element.next_sibling
                    if isinstance(element, Tag):
                        if element.find('div', {'class': 'proposalTitle'}):
                            break
                        if element.find('div', {'class': 'division'}):
                            break
                if label:
                    log.debug("Parsing proposal text as sibling of proposal title")
                    assert proposal is not None, f'Proposal missing for text: {label}'
                    proposal['text'] = label.strip().replace('\xa0', '')
                    count += 1

        elif "proposalText" in item['class']:
            label = item.text.strip()
            assert proposal is not None, f'Proposal missing for text: {label}'
            proposal['text'] = label
            count += 1

    return count
