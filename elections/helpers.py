import re
import string

import log
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from rest_framework.exceptions import APIException


MI_SOS_URL = "https://mvic.sos.state.mi.us"

useragent = UserAgent()


class ServiceUnavailable(APIException):
    status_code = 503
    default_code = 'service_unavailable'
    default_detail = f'The Michigan Secretary of State website ({MI_SOS_URL}) is temporarily unavailable, please try again later.'


def fetch_registration_status_data(voter):
    response = requests.post(
        f'{MI_SOS_URL}/Voter/SearchByName',
        headers={
            'Content-Type': "application/x-www-form-urlencoded",
            'User-Agent': useragent.random,
        },
        data={
            'FirstName': voter.first_name,
            'LastName': voter.last_name,
            'NameBirthMonth': voter.birth_month,
            'NameBirthYear': voter.birth_year,
            'ZipCode': voter.zip_code,
        },
        verify=False,
    )
    check_availability(response)

    # Handle recently moved voters
    if "you have recently moved" in response.text:
        #######################################################################
        # TODO: Figure out what a moved voter looks like
        import bugsnag

        bugsnag.notify(f'Moved {voter}')
        #######################################################################
        log.warn(f"Handling recently moved voter: {voter}")
        page = find_or_abort(
            r"<a href='(registeredvoter\.aspx\?vid=\d+)' class=VITlinks>Begin",
            response.text,
        )
        url = MI_SOS_URL + page
        response = requests.get(url, headers={'User-Agent': useragent.random})
        log.debug(f"Response from MI SOS:\n{response.text}")
        check_availability(response)

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
        category = clean_district_category(match[0])
        if category not in {'Phone'}:
            districs[category] = clean_district_name(match[1])

    return {"registered": registered, "districts": districs}


def check_availability(response):
    if response.status_code >= 400:
        log.error(f'MI SOS status code: {response.status_code}')
        raise ServiceUnavailable()

    html = BeautifulSoup(response.text, 'html.parser')
    div = html.find(id='pollingLocationError')
    if div:
        if div['style'] != 'display:none;':
            raise ServiceUnavailable()


def find_or_abort(pattern: str, text: str):
    match = re.search(pattern, text)
    assert match, f"Unable to match {pattern!r} to {text!r}"
    return match[1]


def clean_district_category(text: str):
    words = text.replace("Judge of ", "").split()
    while words and words[-1] == "District":
        words.pop()
    return " ".join(words)


def clean_district_name(text: str):
    return text.replace("District District", "District").strip()


def titleize(text: str) -> str:
    return (
        string.capwords(text)
        .replace(" Of ", " of ")
        .replace(" To ", " to ")
        .replace(" And ", " and ")
    )


def build_mi_sos_url(election_id: int, precinct_id: int) -> str:
    assert election_id, "MI SOS election ID is missing"
    assert precinct_id, "MI SOS precinct ID is missing"
    return f'{MI_SOS_URL}/Voter/GetMvicBallot/{precinct_id}/{election_id}/'
