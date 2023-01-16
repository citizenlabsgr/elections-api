import os

import pytest
import requests


@pytest.fixture
def url():
    site = os.getenv("SITE")
    if not site:
        pytest.skip("$SITE not set")
    return site


def test_index(expect, url):
    response = requests.get(url, timeout=20)
    expect(response.text).contains(url + "/docs/")


def test_registrations_api(expect, url):
    params = (
        "?first_name=Rosalynn"
        "&last_name=Bliss"
        "&birth_date=1975-08-03"
        "&zip_code=49503"
    )
    response = requests.get(url + "/api/registrations/" + params, timeout=20)
    expect(response.json()["registered"]) == True
