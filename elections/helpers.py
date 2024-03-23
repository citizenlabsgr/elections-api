import re
import string
import time
from contextlib import contextmanager
from datetime import date, datetime
from functools import cache
from importlib import resources
from typing import Any, Generator

import log
import pomace
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from fake_useragent import UserAgent
from nameparser import HumanName

from . import exceptions
from .constants import MVIC_URL

user_agent = UserAgent()

###############################################################################
# Shared helpers


@contextmanager
def mvic_session() -> Generator[requests.Session, None, None]:
    certificate = resources.files("config") / "mvic.sos.state.mi.us.pem"
    session = requests.Session()
    session.verify = str(certificate)
    session.headers["User-Agent"] = user_agent.random
    yield session


def fetch(url: str, expected_text: str) -> str:
    with mvic_session() as session:
        response = session.get(url)

    if response.status_code >= 400:
        log.error(f"MVIC status code: {response.status_code}")
        raise exceptions.ServiceUnavailable()

    text = response.text.strip()
    assert expected_text in text, f"{expected_text!r} not found on {url}"
    return text


def visit(url: str, expected_text: str) -> pomace.Page:
    page = pomace.visit(url)
    if expected_text not in page:
        log.info(f"Revisiting {url} with session cookies")
        page = pomace.visit(url)
    assert expected_text in page, f"{expected_text!r} not found on {url}"
    return page


@cache
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
        .replace("(c", "(C")
        .replace("(d", "(D")
        .replace("(l", "(L")
        .replace("(r", "(R")
        .replace("Vice-president", "Vice-President")
        .strip()
    )


@cache
def normalize_position(text: str) -> str:
    text = text.split(" (")[0].split(" - ")[0]
    text = text.replace(" At-Large", " At Large")
    if text.startswith("Alderman"):
        text = "Alderman"
    elif text == "Board Member Bath Township Library":
        text = "Township Library Board Member"
    elif text.startswith("Delta College Board of Trustees Member"):
        text = "Delta College Board of Trustees Member"
    elif text.endswith("Village Charter Commission"):
        text = "Village Charter Commission"
    elif text.startswith("City Council Ward"):
        text = "City Council"
    elif text.startswith("Council Member District"):
        text = "Council Member"
    return titleize(text)


@cache
def normalize_candidate(text: str) -> str:
    if "\n" in text:
        log.debug(f"Handling potential running mate: {text!r}")
        names = [HumanName(n) for n in text.split("\n")]
        for name in names:
            name.capitalize()

        if "Formerly:" in names[1]:
            log.debug(f"Skipped former name: {names[1]}")
            return str(names[0])
        if " of " in str(names[1]):
            log.debug(f"Skipped non-person running mate: {names[1]}")
            return str(names[0])

        return str(names[0]) + " & " + str(names[1])

    name = HumanName(text.strip())
    name.capitalize()
    return str(name)


@cache
def normalize_district(text: str) -> str:
    return text.replace("District District", "District").replace(" Isd", " ISD").strip()


@cache
def normalize_jurisdiction(name: str) -> str:
    name = titleize(name)

    name = name.replace("Charter Township", "Township")

    for kind in {"City", "Township", "Village"}:
        if name.startswith(kind):
            return name.replace(" Charter", "")

    for kind in {"City", "Township", "Village"}:
        if name.endswith(" " + kind):
            name = kind + " of " + name[: -len(kind) - 1]
            return name.replace(" Charter", "")

    return name


@cache
def normalize_address(line: str) -> str:
    line = line.strip()
    for direction in {"Ne", "Nw", "Se", "Sw"}:
        if line.endswith(direction):
            line = line.replace(" " + direction, " " + direction.upper())
    return line.replace(", Michigan", ", MI")


def build_mvic_url(election_id: int, precinct_id: int) -> str:
    assert election_id, "MVIC election ID is missing"
    assert precinct_id, "MVIC precinct ID is missing"
    return f"{MVIC_URL}/Voter/GetMvicBallot/{precinct_id}/{election_id}/"


###############################################################################
# Registration helpers


def fetch_registration_status_data(voter):
    url = f"{MVIC_URL}/Voter/SearchByName"
    log.info(f"Submitting form on {url}")
    with mvic_session() as session:
        try:
            response = session.post(
                url,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "FirstName": voter.first_name,
                    "LastName": voter.last_name,
                    "NameBirthMonth": voter.birth_month,
                    "NameBirthYear": voter.birth_year,
                    "ZipCode": voter.zip_code,
                },
            )
        except requests.exceptions.RequestException as e:
            log.error(f"MVIC connection error: {e}")
            raise exceptions.ServiceUnavailable()

    if response.status_code >= 400:
        log.error(f"MVIC status code: {response.status_code}")
        raise exceptions.ServiceUnavailable()

    if "No map" in response.text:
        log.error("District information is unavailable")
        raise exceptions.ServiceUnavailable()

    html = BeautifulSoup(response.text, "html.parser")

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
    ballot_url = None
    if ballot := "Ballot preview" in response.text:
        if match := re.search(r"/Voter/GetMvicBallot/\d+/\d+/", response.text):
            ballot_url = MVIC_URL + match.group()
        else:
            log.warn("Unable to determine ballot URL")

    # Parse absentee status
    absentee = "You are on the permanent absentee voter list" in response.text

    # Parse absentee dates
    absentee_dates: dict[str, date | None] = {
        "Election Date": None,
        "Application Received": None,
        "Ballot Sent": None,
        "Ballot Received": None,
    }
    element = html.find(id="lblAbsenteeVoterInformation")
    if element:
        strings = list(element.strings)
        for index, string in enumerate(strings):
            key = string.strip(": ").title()
            if key in absentee_dates:
                if value := strings[index + 1].strip():
                    absentee_dates[key] = datetime.strptime(value, "%m/%d/%Y").date()
    else:
        log.warn("Unable to determine absentee status")

    # Parse districts
    districts: dict = {}
    element = html.find(id="lblCountyName")
    if element:
        districts["County"] = normalize_district(element.text)
    element = html.find(id="lblJurisdName")
    if element:
        districts["Jurisdiction"] = normalize_jurisdiction(element.text)
    for category_name, element_id in [
        ("Circuit Court", "lblCircuitName"),
        ("Community College", "lblCommCollegeName"),
        ("County Commissioner", "lblCountyCommDistrict"),
        ("Court of Appeals", "lblAppealsName"),
        ("District Court", "lblDistCourtName"),
        ("Intermediate School", "lblIsdName"),
        ("Library", "lblLibraryName"),
        ("Metropolitan", "lblMetroName"),
        ("Municipal Court", "lblMuniCourtName"),
        ("Precinct", "lblPrecinctNumber"),
        ("Probate Court", "lblProbateName"),
        ("Probate Court", "lblProbateName"),
        ("Probate District Court", "lblProbateDistName"),
        ("School", "lblSchoolDistrict"),
        ("State House", "lblHouseDistrict"),
        ("State Senate", "lblSenateDistrict"),
        ("US Congress", "lblCongressDistrict"),
        ("Village", "lblVillageName"),
        ("Ward", "lblWardNumber"),
    ]:
        element = html.find(id=element_id)
        if element:
            districts[category_name] = normalize_district(
                element.text.strip().strip(",").replace("Not applicable", "")
            )

    # Parse polling location
    polling_location: dict = {}
    element = html.find(id="lblPollingLocation")
    if element:
        polling_location["PollingLocation"] = element.text.strip()
    element = html.find(id="lblPollAddress")
    if element:
        polling_location["PollAddress"] = normalize_address(element.text)
    element = html.find(id="lblPollCityStateZip")
    if element:
        polling_location["PollCityStateZip"] = normalize_address(element.text)
    else:
        log.warn("Unable to determine polling location")

    # Parse drop box locations
    dropbox_locations: list[dict[str, list[str]]] = []
    elements = html.find_all("div", class_="voter-info-card")
    for element in elements:
        if "Drop box locations" not in element.text:
            continue
        for address_block in element.find_all("address"):
            dropbox_location: dict[str, list[str]] = {"address": [], "hours": []}

            # Parse address
            for line in address_block.find_all("div"):
                dropbox_location["address"].append(normalize_address(line.text))

            # Parse hours
            lines = [
                e.get_text("\n").strip() for e in address_block.find_next_siblings()
            ]
            for index, line in enumerate(lines):
                if line == "Hours:":
                    dropbox_location["hours"] = lines[index + 1].split("\n")
                    break
            else:
                log.warn("Unable to determine drop box hours")

            dropbox_locations.append(dropbox_location)

        if not dropbox_locations:
            log.warn("No drop box locations found")
        break
    else:
        log.warn("Unable to determine drop box locations")

    return {
        "registered": registered,
        "ballot": ballot,
        "ballot_url": ballot_url,
        "absentee": absentee,
        "absentee_dates": absentee_dates,
        "districts": districts,
        "polling_location": polling_location,
        "dropbox_locations": dropbox_locations,
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
    log.info(f"Fetching ballot: {url}")
    return fetch(url, "PreviewMvicBallot")


def parse_election(html: str) -> tuple[str, tuple[int, int, int]]:
    """Parse election information from ballot HTML."""
    soup = BeautifulSoup(html, "html.parser")
    header = soup.find(id="PreviewMvicBallot").div.div.div.text

    election_name_text, election_date_text, *_ = header.strip().split("\n")
    election_name = titleize(election_name_text)
    election_date = datetime.strptime(election_date_text.strip(), "%A, %B %d, %Y")

    return election_name, (election_date.year, election_date.month, election_date.day)


def parse_precinct(html: str, url: str) -> tuple[str, str, str, str]:
    """Parse precinct information from ballot HTML."""

    # Parse county
    match = re.search(r"(?P<county>[^>]+) County, Michigan", html, re.IGNORECASE)
    assert match, f"Unable to find county name: {url}"
    county = titleize(match.group("county"))

    # Parse jurisdiction
    match = None
    for pattern in [
        r"(?P<jurisdiction>[^>]+), Ward (?P<ward>\d+) Precinct (?P<precinct>\d+)",
        r"(?P<jurisdiction>[^>]+),  Precinct (?P<precinct>\d+[A-Z]?)",
        r"(?P<jurisdiction>[^>]+), Ward (?P<ward>\d+)",
    ]:
        match = re.search(pattern, html)
        if match:
            break
    assert match, f"Unable to find precinct information: {url}"
    jurisdiction = normalize_jurisdiction(match.group("jurisdiction"))

    # Parse ward
    try:
        ward = match.group("ward")
    except IndexError:
        ward = ""

    # Parse number
    try:
        precinct = match.group("precinct")
    except IndexError:
        precinct = ""

    return county, jurisdiction, ward, precinct


def parse_district_from_proposal(category: str, text: str, mvic_url: str) -> str:
    patterns = [
        f"[a-z] ((?:[A-Z][A-Za-z.-]+ )+{category})",
        f"\n((?:[A-Z][A-Za-z.-]+ )+{category})",
        f"{category} of the ([^,.]+),",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            name = match[1].strip()
            log.debug(f"{pattern!r} matched: {name}")
            if len(name) < 100:
                return name

    pattern = r"[(](.+ School)[)]"
    if match2 := re.search(pattern, text):
        name = match2[1].strip()
        log.debug(f"{pattern!r} matched: {name}")
        return name

    raise ValueError(f"Could not find {category!r} in {text!r} on {mvic_url}")


def parse_seats(text: str) -> int:
    """Parse the number of seats from a ballot text."""
    try:
        count = int(text.removeprefix("Vote for not more than "))
        if count <= 0:
            log.error(f"Invalid seat count: {count}")
            count = 1
        return count
    except ValueError:
        return 0


def parse_ballot(html: str, data: dict) -> int:
    """Call all parsers to insert ballot data into the provided dictionary."""
    html = (
        html.replace("&nbsp;", " ")
        .replace("<br>", "\n")
        .replace("\n ", "\n")
        .replace(" \n", "\n")
        .replace("  ", " ")
        .replace("  ", " ")
    )
    soup = BeautifulSoup(html, "html.parser")
    ballot = soup.find(id="PreviewMvicBallot").div.div.find_all("div", recursive=False)[
        1
    ]
    count = 0
    count += parse_primary_election_offices(ballot, data)
    count += parse_general_election_offices(ballot, data)
    count += parse_proposals(ballot, data)
    return count


def parse_primary_election_offices(ballot: BeautifulSoup, data: dict) -> int:
    """Inserts primary election ballot data into the provided dictionary."""
    count = 0

    offices = ballot.find(id="twoPartyPrimaryElectionOffices")
    if not offices:
        return count

    section: dict = {}
    label = "primary section"
    data[label] = section

    count += _parse_primary_election_offices("Democratic", ballot, section)
    count += _parse_primary_election_offices("Republican", ballot, section)
    return count


def _parse_primary_election_offices(
    party: str, ballot: BeautifulSoup, data: dict
) -> int:
    """Inserts primary election ballot data into the provided dictionary."""
    count = 0

    assert ballot.text.find("DEMOCRATIC") < ballot.text.find("REPUBLICAN")
    offices = ballot.find(
        id="columnOnePrimary" if party == "Democratic" else "columnTwoPrimary"
    )
    if not offices:
        return count

    section: dict[str, Any] = {}
    division: list | None = None
    data[party] = section

    for index, item in enumerate(
        offices.find_all(
            "div",
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
        log.debug(f"Parsing office element {index}: {item}")

        if "division" in item["class"]:
            label = (
                titleize(item.text).replace(" - Continued", "").replace(" District", "")
            )
            try:
                division = section[label]
            except KeyError:
                division = []
            section[label] = division
            office = None

        elif "office" in item["class"]:
            label = normalize_position(item.text)
            assert division is not None, f"Division missing for office: {label}"
            office = {
                "name": label,
                "district": None,
                "type": None,
                "term": None,
                "seats": None,
                "candidates": [],
            }
            division.append(office)

        elif "term" in item["class"]:
            label = item.text
            assert office is not None, f"Office missing for term: {label}"
            if "Incumbent " in label or "New " in label:
                office["type"] = label
            elif "Term" in label:
                office["term"] = label
            elif seats := parse_seats(label):
                office["seats"] = seats
            else:
                office["district"] = titleize(label)
            count += 1

        elif "candidate" in item["class"]:
            label = normalize_candidate(item.get_text("\n"))
            assert office is not None, f"Office missing for candidate: {label}"
            if label == "No candidates on ballot":
                continue
            candidate: dict[str, Any] = {
                "name": label,
                "finance_link": None,
                "party": None,
            }
            office["candidates"].append(candidate)
            count += 1

        elif "financeLink" in item["class"]:
            if item.a:
                candidate["finance_link"] = item.a["href"]

        elif "party" in item["class"]:
            label = titleize(item.text)
            assert candidate is not None, f"Candidate missing for party: {label}"
            candidate["party"] = label or None

    return count


def parse_general_election_offices(ballot: BeautifulSoup, data: dict) -> int:
    """Inserts general election ballot data into the provided dictionary."""
    count = 0

    offices = ballot.find(id="generalElectionOffices")
    if not offices:
        return count

    section: dict | None = None
    for index, item in enumerate(
        offices.find_all(
            "div",
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
        log.debug(f"Parsing office element {index}: {item}")

        if "section" in item["class"]:
            section = {}
            division: list | None = None
            office: dict | None = None
            label = item.text.lower()
            if label in data:
                log.warn(f"Duplicate section on ballot: {label}")
                section = data[label]
            else:
                data[label] = section

        elif "division" in item["class"]:
            office = None
            label = (
                titleize(item.text).replace(" - Continued", "").replace(" District", "")
            )
            if section is None:
                log.warn(f"Section missing for division: {label}")
                assert list(data.keys()) == ["primary section"]
                section = {}
                data["nonpartisan section"] = section
            try:
                division = section[label]
            except KeyError:
                division = []
            section[label] = division
            office = None

        elif "office" in item["class"]:
            label = normalize_position(item.text)
            if division is None:
                assert (
                    label == "Library Board Director"
                ), f"Division missing for office: {label}"
                division = []
                assert isinstance(section, dict), f"Section missing for office: {label}"
                section["Library"] = division
            office = {
                "name": label,
                "district": None,
                "type": None,
                "term": None,
                "seats": None,
                "candidates": [],
            }
            division.append(office)

        elif "term" in item["class"]:
            label = item.text
            assert office is not None, f"Office missing for term: {label}"
            if "Incumbent " in label or "New " in label:
                office["type"] = label
            elif "Term" in label:
                office["term"] = label
            elif seats := parse_seats(label):
                office["seats"] = seats
            else:
                office["district"] = titleize(label)
            count += 1

        elif "candidate" in item["class"]:
            label = normalize_candidate(item.get_text("\n"))
            assert office is not None, f"Office missing for candidate: {label}"
            if label == "No candidates on ballot":
                continue
            candidate = {"name": label, "finance_link": None, "party": None}
            office["candidates"].append(candidate)
            count += 1

        elif "financeLink" in item["class"]:
            if item.a:
                candidate["finance_link"] = item.a["href"]

        elif "party" in item["class"]:
            label = titleize(item.text)
            assert candidate is not None, f"Candidate missing for party: {label}"
            candidate["party"] = label or None

    return count


def parse_proposals(ballot: BeautifulSoup, data: dict) -> int:
    """Inserts proposal data into the provided dictionary."""
    count = 0

    proposals = ballot.find(id="proposals")
    if not proposals:
        return count

    for index, item in enumerate(
        proposals.find_all(
            "div", {"class": ["section", "division", "proposalTitle", "proposalText"]}
        ),
        start=1,
    ):
        log.debug(f"Parsing proposal element {index}: {item}")

        if "section" in item["class"]:
            section: dict[str, Any] = {}
            division: list | None = None
            proposal = None
            label = item.text.lower()
            data[label] = section

        elif "division" in item["class"]:
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

        elif "proposalTitle" in item["class"]:
            label = _html_to_text(item)
            if "\n" in label and "?" in label and len(label) > 200:
                log.debug("Parsing proposal text as part of proposal title")
                label, text = label.split("\n", 1)
            else:
                text = None
            if label.isupper() or label[-20:].islower():
                label = titleize(label)
            assert division is not None, f"Division missing for proposal: {label}"
            proposal = {"title": label, "text": text}
            division.append(proposal)

            if proposal["text"]:
                count += 1
            else:
                # Handle proposal text missing a class
                if str(item.parent.parent).count("mce") > 100:
                    log.debug("Parsing proposal text from parent with MCE formatting")
                    heading = item.text
                    body = item.parent.parent.text.replace("\xa0", "")
                    label = body.split(heading, maxsplit=1)[1]
                    log.debug(f"Original text: {label!r}")
                    label = re.sub(r",([^ 0-9])", r", \1", label)  # fix commas
                    label = re.sub(r":([^ 0-9])", r":\n\n\1", label)  # fix colons
                    label = re.sub(
                        r"([.?])([A-Z])", r"\1\n\n\2", label
                    )  # fix paragraphs
                    label = re.sub(r"[.][(]", r".\n\n(", label)  # fix paragraphs
                    proposal["text"] = label
                    log.debug(f"Cleaned text: {proposal['text']!r}")
                    count += 1
                    continue

                label = ""
                element = item.parent.next_sibling
                while element is not None:
                    label += _html_to_text(element)
                    element = element.next_sibling
                    if isinstance(element, Tag):
                        if element.find("div", {"class": "proposalTitle"}):
                            break
                        if element.find("div", {"class": "division"}):
                            break
                if label:
                    log.debug("Parsing proposal text as sibling of proposal title")
                    assert proposal is not None, f"Proposal missing for text: {label}"
                    log.debug(f"Original text: {label!r}")
                    label = re.sub(r"\n([a-z])", r"\1", label)  # remove extra breaks
                    label = re.sub(r":([^ 0-9])", r":\n\n\1", label)  # fix colons
                    label = re.sub(
                        r"([.?])([A-Z])", r"\1\n\n\2", label
                    )  # fix paragraphs
                    proposal["text"] = label.strip().replace("\xa0", "")
                    log.debug(f"Cleaned text: {proposal['text']!r}")
                    count += 1

        elif "proposalText" in item["class"]:
            label = _html_to_text(item)
            assert proposal is not None, f"Proposal missing for text: {label}"
            proposal["text"] = label
            count += 1

        if proposal and proposal["text"]:
            proposal["text"] = proposal["text"].replace("\xa0", "")
            proposal["text"] = proposal["text"].replace("\n\n\n\n\n\n", "\n\n")
            proposal["text"] = proposal["text"].replace("\n\n\n\n\n", "\n\n")
            proposal["text"] = proposal["text"].replace("\n\n\n\n", "\n\n")
            proposal["text"] = proposal["text"].replace("\n\n\n", "\n\n")

    return count


def _html_to_text(element) -> str:
    try:
        if items := element.find_all("li"):
            lines = ["- " + item.text.strip(".; ") for item in items]
            return "\n\n" + "\n".join(lines) + "\n\n"
        return element.text
    except AttributeError:
        return element.strip()
