import re
import string
from pprint import pformat
from typing import Optional

import log
import requests
from fake_useragent import UserAgent
from rest_framework.exceptions import APIException


MI_SOS_URL = "https://webapps.sos.state.mi.us/MVIC/"

useragent = UserAgent()


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Service temporarily unavailable, try again later."
    default_code = 'service_unavailable'


def fetch_registration_status_data(voter):
    # GET form tokens
    url = MI_SOS_URL
    response = requests.get(url, headers={'User-Agent': useragent.random})
    check_availability(response)

    # Build form data
    form = {
        "__EVENTVALIDATION": find_or_abort(
            'id="__EVENTVALIDATION" value="(.*?)"', response.text
        ),
        "__VIEWSTATE": find_or_abort(
            'id="__VIEWSTATE" value="(.*?)"', response.text
        ),
        "__VIEWSTATEGENERATOR": find_or_abort(
            'id="__VIEWSTATEGENERATOR" value="(.*?)"', response.text
        ),
        "__VIEWSTATEENCRYPTED": "",
        "ctl00$ContentPlaceHolder1$vsFname": voter.first_name,
        "ctl00$ContentPlaceHolder1$vsLname": voter.last_name,
        "ctl00$ContentPlaceHolder1$vsMOB2": voter.birth_month,
        "ctl00$ContentPlaceHolder1$vsMOB1": voter.birth_month,
        "ctl00$ContentPlaceHolder1$vsYOB2": voter.birth_year,
        "ctl00$ContentPlaceHolder1$vsZip": voter.zip_code,
        "ctl00$ContentPlaceHolder1$btnSearchByName": "Search",
    }
    log.debug(f"Submitting data to MI SOS:\n{pformat(form)}")

    # POST form data
    response = requests.post(
        MI_SOS_URL,
        headers={
            'Content-Type': "application/x-www-form-urlencoded",
            'User-Agent': useragent.random,
        },
        data=form,
    )
    check_availability(response)

    # Handle recently moved voters
    if "you have recently moved" in response.text:
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
    registered: Optional[bool] = bool(
        re.search("My Voting District Information", response.text)
    )
    if not registered and bool(
        re.search("not available at this time", response.text)
    ):
        registered = None

    # Parse districts
    districs = {}
    for match in re.findall(
        r'districtCell">[\s\S]*?<b>(.*?): <\/b>[\s\S]*?districtCell">[\s\S]*?">(.*?)<\/span>',
        response.text,
    ):
        category = clean_district_category(match[0])
        districs[category] = clean_district_name(match[1])

    return {"registered": registered, "districts": districs}


def check_availability(response):
    html = response.text.lower()
    if response.status_code >= 400 or "not available" in html:
        raise ServiceUnavailable()


def find_or_abort(pattern: str, text: str):
    match = re.search(pattern, text)
    assert match, f"Unable for match {pattern!r} to {text!r}"
    return match[1]


def clean_district_category(text: str):
    words = text.replace("Judge of ", "").split()
    while words and words[-1] == "District":
        words.pop()
    return " ".join(words)


def clean_district_name(text: str):
    return text.replace("District District", "District")


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
    base = MI_SOS_URL + 'SampleBallot.aspx'
    params = f'd={precinct_id}&ed={election_id}'
    return f'{base}?{params}'
