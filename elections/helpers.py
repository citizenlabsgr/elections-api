import importlib.resources  # New in 3.7
import re
import string
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import bugsnag
import log
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from nameparser import HumanName

from . import exceptions
from .constants import MI_SOS_URL


useragent = UserAgent()

###############################################################################
# Shared helpers


def titleize(text: str) -> str:
    return (
        string.capwords(text)
        .replace(" Of ", " of ")
        .replace(" To ", " to ")
        .replace(" And ", " and ")
        .replace(" In ", " in ")
        .replace(" By ", " by ")
        .replace(" At ", " at ")
        .replace("U.s.", "U.S.")
        .replace("Ii.", "II.")
        .replace("(d", "(D")
        .replace("(l", "(L")
        .replace("(r", "(R")
        .strip()
    )


def normalize_candidate(text: str) -> str:
    if '\n' in text:
        log.debug(f'Handling running mate: {text}')
        text1, text2 = text.split('\n')
        name1 = HumanName(text1.strip())
        name2 = HumanName(text2.strip())
        name1.capitalize()
        name2.capitalize()
        return str(name1) + ' & ' + str(name2)

    name = HumanName(text.strip())
    name.capitalize()
    return str(name)


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


def build_mi_sos_url(election_id: int, precinct_id: int) -> str:
    assert election_id, "MI SOS election ID is missing"
    assert precinct_id, "MI SOS precinct ID is missing"
    return f'{MI_SOS_URL}/Voter/GetMvicBallot/{precinct_id}/{election_id}/'


###############################################################################
# Registration helpers


@contextmanager
def _get_mvic_session(*, random_agent: bool = True):
    """
    Get a Requests Session configured for talking with MVIC.

    (Mostly, SSL settings.)
    """
    with importlib.resources.path('elections', 'mvic.sos.state.mi.us.pem') as certpath:
        sess = requests.Session()

        sess.verify = str(certpath)
        sess.headers['User-Agent'] = (
            useragent.random
            if random_agent
            else 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'
        )

        yield sess


def _check_availability(response):
    if response.status_code >= 400:
        log.error(f'MI SOS status code: {response.status_code}')
        raise exceptions.ServiceUnavailable()

    html = BeautifulSoup(response.text, 'html.parser')
    div = html.find(id='pollingLocationError')
    if div:
        if div['style'] != 'display:none;':
            raise exceptions.ServiceUnavailable()


def fetch_registration_status_data(voter):
    with _get_mvic_session() as sess:
        response = sess.post(
            f'{MI_SOS_URL}/Voter/SearchByName',
            headers={'Content-Type': "application/x-www-form-urlencoded"},
            data={
                'FirstName': voter.first_name,
                'LastName': voter.last_name,
                'NameBirthMonth': voter.birth_month,
                'NameBirthYear': voter.birth_year,
                'ZipCode': voter.zip_code,
            },
        )
        _check_availability(response)

        # Handle recently moved voters

    # Parse registration
    registered = None
    if "Yes! You Are Registered" in response.text:
        registered = True
    elif "No voter record matched your search criteria" in response.text:
        registered = False
    else:
        log.warn("Unable to determine registration status")

    # Parse moved status
    recently_moved = "you have recently moved" in response.text
    if recently_moved:
        # TODO: Figure out how to request the new records
        bugsnag.notify(
            exceptions.UnhandledData("Voter has moved"),
            meta_data={"voter": repr(voter), "html": response.text},
        )

    # Parse absentee status
    absentee = "You are on the permanent absentee voter list" in response.text

    # Parse districts
    districts = {}
    for match in re.findall(r'>([\w ]+):[\s\S]*?">([\w ]*)<', response.text):
        category = _clean_district_category(match[0])
        if category == "Jurisdiction":
            districts[category] = normalize_jurisdiction(match[1])
        elif category not in {'Phone', 'Mailing Address', 'Open'}:
            districts[category] = _clean_district_name(match[1])

    # Parse Polling Location
    polling_location = {
        "PollingLocation": "",
        "PollAddress": "",
        "PollCityStateZip": "",
    }
    for key in polling_location:
        index = response.text.find('lbl' + key)
        if index == -1:
            log.warn("Could not find polling location.")
        else:
            newstring = response.text[(index + len(key) + 5) :]
            end = newstring.find('<')
            polling_location[key] = newstring[0:end]

    return {
        "registered": registered,
        "absentee": absentee,
        "districts": districts,
        "polling_location": polling_location,
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


def _clean_district_name(text: str):
    return text.replace("District District", "District").strip()


###############################################################################
# Ballot helpers


def fetch_ballot(url: str) -> str:
    log.info(f'Fetching ballot: {url}')
    with _get_mvic_session(random_agent=False) as sess:
        response = sess.get(url)
        response.raise_for_status()
    return response.text.strip()


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


def parse_district_from_proposal(category: str, text: str, mi_sos_url: str) -> str:
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

    raise ValueError(f'Could not find {category!r} in {text!r} on {mi_sos_url}')


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

    assert ballot.find(id='primaryColumnHeading1').text.strip() == 'DEMOCRATIC PARTY'
    assert ballot.find(id='primaryColumnHeading2').text.strip() == 'REPUBLICAN PARTY'

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
        log.debug(f'Parsing office item {index}: {item}')

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
            label = titleize(item.text)
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
                # TODO: Remove this assert after parsing an entire general election
                assert (
                    "WARD" in label
                    or "DISTRICT" in label
                    or "COURT" in label
                    or "COLLEGE" in label
                    or "Village of " in label
                    or label.endswith(" SCHOOL")
                    or label.endswith(" SCHOOLS")
                    or label.endswith(" ISD")
                    or label.endswith(" ESA")
                    or label.endswith(" COMMUNITY")
                    or label.endswith(" LIBRARY")
                ), f'Unhandled term: {label}'  # pylint: disable=too-many-boolean-expressions
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
        log.debug(f'Parsing office item {index}: {item}')

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
            label = titleize(item.text)
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
                # TODO: Remove this assert after parsing an entire general election
                assert (
                    "WARD" in label
                    or "DISTRICT" in label
                    or "COURT" in label
                    or "COLLEGE" in label
                    or "Village of " in label
                    or label.endswith(" SCHOOL")
                    or label.endswith(" SCHOOLS")
                    or label.endswith(" ISD")
                    or label.endswith(" ESA")
                    or label.endswith(" COMMUNITY")
                    or label.endswith(" LIBRARY")
                ), f'Unhandled term: {label}'  # pylint: disable=too-many-boolean-expressions
                office['district'] = titleize(label)
            count += 1

        elif "candidate" in item['class']:
            label = normalize_candidate(item.get_text('\n'))
            assert office is not None, f'Office missing for candidate: {label}'
            if label == 'No candidates on ballot':
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
        log.debug(f'Parsing proposal item {index}: {item}')

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
            if label.isupper():
                label = titleize(label)
            if '\n' in label:
                # TODO: Remove duplicate text in description?
                log.warning(f'Newlines in proposal title: {label}')
                if label.count('\n') == 1:
                    label = label.replace('\n', ': ')
            assert division is not None, f'Division missing for proposal: {label}'
            proposal = {'title': label, 'text': None}
            division.append(proposal)

        elif "proposalText" in item['class']:
            label = item.text.strip()
            assert proposal is not None, f'Proposal missing for text: {label}'
            proposal['text'] = label
            count += 1

    return count
