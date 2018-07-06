import re
from pprint import pformat
from typing import Optional

import log
import requests
from memoize import memoize


MI_SOS_URL = "https://webapps.sos.state.mi.us/MVIC/"


@memoize(timeout=60)
def fetch_registration_status_data(voter):

    # GET form tokens
    response = requests.get(MI_SOS_URL)
    log.debug(f"Fetched MI SOS form:\n{response.text}")
    response.raise_for_status()

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
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=form,
    )
    log.debug(f"Response from MI SOS:\n{response.text}")
    response.raise_for_status()

    # Parse registration
    registered: Optional[bool] = bool(
        re.search("Yes, You Are Registered", response.text)
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
        districs[match[0]] = clean_district_name(match[1])

    return {"registered": registered, "districts": districs}


def find_or_abort(pattern: str, text: str):
    match = re.search(pattern, text)
    assert match, f"Unable for match {pattern!r} to {text!r}"
    return match[1]


def clean_district_name(text: str):
    return text.replace("District District", "District")
