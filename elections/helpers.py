import os
import re
import string
from pprint import pformat
from typing import Optional

import log
import redis
import requests
import requests_cache
from rest_framework.exceptions import APIException


MI_SOS_URL = "https://webapps.sos.state.mi.us/MVIC/"
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Geck o/20100101 Firefox/40.1'
)


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Service temporarily unavailable, try again later."
    default_code = 'service_unavailable'


def enable_requests_cache(expire_after):  # pragma: no cover
    connection = redis.from_url(os.environ['REDIS_URL'])
    requests_cache.install_cache(
        backend='redis', connection=connection, expire_after=expire_after
    )


def fetch_registration_status_data(voter):

    # GET form tokens
    with requests_cache.disabled():
        try:
            url = MI_SOS_URL
            response = requests.get(url, headers={'User-Agent': USER_AGENT})
        except OSError as exc:
            log.error(f'Unable to GET {url}: {exc}')
            raise ServiceUnavailable()
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
        headers={
            'Content-Type': "application/x-www-form-urlencoded",
            'User-Agent': USER_AGENT,
        },
        data=form,
    )
    log.debug(f"Response from MI SOS:\n{response.text}")
    response.raise_for_status()

    # Handle recently moved voters
    if "you have recently moved" in response.text:
        log.warn(f"Handling recently moved voter: {voter}")
        page = find_or_abort(
            r"<a href='(registeredvoter\.aspx\?vid=\d+)' class=VITlinks>Begin",
            response.text,
        )
        with requests_cache.disabled():
            response = requests.get(
                MI_SOS_URL + page, headers={'User-Agent': USER_AGENT}
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


def titleize(text: str) -> str:
    return string.capwords(text).replace("Of", "of")
