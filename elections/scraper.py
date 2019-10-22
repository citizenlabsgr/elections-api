import re
from datetime import datetime
from typing import Dict, Optional, Tuple

import log
import requests
from bs4 import BeautifulSoup

from .helpers import titleize


def fetch(url: str) -> str:
    log.info(f'Fetching {url}')
    response = requests.get(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'
        },
        verify=False,
    )
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
    match = re.search(r'(?P<county>[^>]+) County, Michigan', html)
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
    jurisdiction = titleize(match.group('jurisdiction'))

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
            'div', {"class": ["section", "division", "office", "term", "candidate"]}
        ),
        start=1,
    ):
        log.debug(f'Parsing item {index}: {item}')

        if "section" in item['class']:
            section: Dict[str, Dict] = {}
            division: Optional[Dict] = None
            office: Optional[Dict] = None
            label = item.text
            data[label] = section

        elif "division" in item['class']:
            label = item.text.replace(' - Continued', '')

            try:
                division = section[label]
            except KeyError:
                division = {}

            section[label] = division
            office = None

        elif "office" in item['class']:
            label = item.text
            assert division is not None, f'Division missing for office: {label}'

            try:

                office = division[label]
            except KeyError:
                office = {'term': [], 'candidates': []}

            division[label] = office

        elif "term" in item['class']:
            label = item.text
            assert office is not None, f'Office missing for term: {label}'
            office['term'].append(label)
            count += 1

        elif "candidate" in item['class']:
            label = item.text
            assert office is not None, f'Office missing for candidate: {label}'
            office['candidates'].append(item.text)
            count += 1

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
        log.debug(f'Parsing item {index}: {item}')

        if "section" in item['class']:
            section: Dict[str, Dict] = {}
            division: Optional[Dict] = None
            label = item.text
            data[label] = section

        elif "division" in item['class']:
            label = item.text.replace(' - Continued', '')

            try:
                division = section[label]
            except KeyError:
                division = {}

            section[label] = division

        elif "proposalTitle" in item['class']:
            label = item.text
            assert division is not None, f'Division missing for proposal: {label}'

            try:
                proposal = division[label]
            except KeyError:
                proposal = {'text': None}

            division[label] = proposal

        elif "proposalText" in item['class']:
            label = item.text
            assert proposal is not None, f'Proposal missing for text: {label}'
            proposal['text'] = item.text
            count += 1

    return count
