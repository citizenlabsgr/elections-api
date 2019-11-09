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
from rest_framework.exceptions import APIException


MI_SOS_URL = "https://mvic.sos.state.mi.us"

useragent = UserAgent()


###############################################################################
# Shared helpers


def titleize(text: str) -> str:
    return (
        string.capwords(text)
        .replace(" Of ", " of ")
        .replace(" To ", " to ")
        .replace(" And ", " and ")
        .replace("U.s.", "U.S.")
        .replace("Ii.", "II.")
        .replace("(r", "(R")
        .strip()
    )


def normalize_candidate(text: str) -> str:
    name = HumanName(text.strip())
    name.capitalize()
    return str(name)


def normalize_jurisdiction(name: str) -> str:
    name = titleize(name)

    for kind in {'City', 'Township', 'Village'}:
        if name.startswith(kind):
            return name

    for kind in {'City', 'Township', 'Village'}:
        if name.endswith(' ' + kind):
            return kind + ' of ' + name[: -len(kind) - 1]

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


class ServiceUnavailable(APIException):
    status_code = 503
    default_code = 'service_unavailable'
    default_detail = f'The Michigan Secretary of State website ({MI_SOS_URL}) is temporarily unavailable, please try again later.'


def _check_availability(response):
    if response.status_code >= 400:
        log.error(f'MI SOS status code: {response.status_code}')
        raise ServiceUnavailable()

    html = BeautifulSoup(response.text, 'html.parser')
    div = html.find(id='pollingLocationError')
    if div:
        if div['style'] != 'display:none;':
            raise ServiceUnavailable()


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
        if "you have recently moved" in response.text:
            # TODO: Figure out what a moved voter looks like
            bugsnag.notify(
                RuntimeError("Voter has moved"),
                meta_data={"voter": repr(voter), "html": response.text},
            )
            log.warn(f"Handling recently moved voter: {voter}")
            page = _find_or_abort(
                r"<a href='(registeredvoter\.aspx\?vid=\d+)' class=VITlinks>Begin",
                response.text,
            )
            url = MI_SOS_URL + page
            response = sess.get(url)
            log.debug(f"Response from MI SOS:\n{response.text}")
            _check_availability(response)

    # Parse registration
    registered = None
    if "Yes! You Are Registered" in response.text:
        registered = True
    elif "No voter record matched your search criteria" in response.text:
        registered = False
    else:
        log.warn("Unable to determine registration status")

    # Parse districts
    districs = {}
    for match in re.findall(r'>([\w ]+):[\s\S]*?">([\w ]*)<', response.text):
        category = _clean_district_category(match[0])
        if category not in {'Phone'}:
            districs[category] = _clean_district_name(match[1])

    # Parse Polling Location
    pollingloc = {"PollingLocation": "", "PollAddress": "", "PollCityStateZip": ""}
    for key in pollingloc:
        index = response.text.find(key)
        if index == -1:
            log.warn("Could not find polling location.")
        else:
            newstring = response.text[(index + len(key) + 2) :]
            end = newstring.find('<')
            pollingloc[key] = newstring[0:end]

    return {
        "registered": registered,
        "districts": districs,
        "polling_location": pollingloc,
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


def parse_district_from_proposal(category: str, text: str) -> str:
    patterns = [f'[a-z] ((?:[A-Z][a-z]+ )+{category})']

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            name = match[1].strip()
            log.debug(f'{pattern!r} matched: {name}')
            if len(name) < 100:
                return name

    raise ValueError(f'Could not find {category}: {text}')


def parse_ballot(html: str, data: Dict) -> int:
    """Call all parsers to insert ballot data into the provided dictionary."""
    soup = BeautifulSoup(html, 'html.parser')
    ballot = soup.find(id='PreviewMvicBallot').div.div.find_all('div', recursive=False)[
        1
    ]
    count = 0
    count += parse_general_election_offices(ballot, data)
    count += parse_proposals(ballot, data)
    return count


def parse_general_election_offices(ballot: BeautifulSoup, data: Dict) -> int:
    """Inserts general election ballot data into the provided dictionary."""
    count = 0

    offices = ballot.find(id='generalElectionOffices')
    if not offices:
        return count

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
            section: Dict[str, Any] = {}
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
                ), (
                    f'Unhandled term: {label}'
                )  # pylint: disable=too-many-boolean-expressions
                office['district'] = titleize(label)
            count += 1

        elif "candidate" in item['class']:
            label = normalize_candidate(item.text)
            assert office is not None, f'Office missing for candidate: {label}'
            if label == 'No candidates on ballot':
                continue
            candidate = {'name': label, 'finance_link': None, 'party': None}
            office['candidates'].append(candidate)
            count += 1

        elif "financeLink" in item['class']:
            label = item.text.strip()
            assert candidate is not None, f'Candidate missing for finance link: {label}'
            candidate['finance_link'] = label or None

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
