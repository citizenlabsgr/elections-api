import re

import log
import requests


MI_SOS_URL = "https://webapps.sos.state.mi.us/MVIC/"


def fetch_registration_status_data(voter):
    response = requests.get(MI_SOS_URL)
    log.debug(response.text)
    response.raise_for_status()

    form_data = {
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
    log.debug(form_data)

    response = requests.post(
        MI_SOS_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=form_data,
    )
    log.debug(response.text)
    response.raise_for_status()

    registered = bool(re.search("Yes, You Are Registered", response.text))

    # const registered = !!body.match(/Yes\, You Are Registered/);
    #     if (!registered) return { registered: false };
    #     const ret = { registered: !!body.match(/Yes\, You Are Registered/) };
    #     const rex = /districtCell">[\s\S]*?<b>(.*?): <\/b>[\s\S]*?districtCell">[\s\S]*?">(.*?)<\/span>/g
    #     do {
    #         var m = rex.exec(body);
    #         if (m) {
    #             ret[m[1].toLowerCase().replace(/\s/g, '_')] = m[2];
    #         }
    #     } while (m);
    #     return ret;

    return {"registered": registered}


def find_or_abort(pattern, text):
    match = re.search(pattern, text)
    assert match, f"Unable for match {pattern!r} to {text!r}"
    return match[1]
