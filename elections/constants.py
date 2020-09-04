from django.conf import settings

from pendulum import datetime


MI_SOS_URL = "https://mvic.sos.state.mi.us"

TERMS = {
    "United States Senator": "6 Year Term",
    "Representative in Congress": "2 Year Term",
    "Representative in State Legislature": "2 Year Term",
}

SCRAPER_LAST_UPDATED = datetime(2020, 9, 3, tz=settings.TIME_ZONE)
PARSER_LAST_UPDATED = datetime(2020, 9, 3, tz=settings.TIME_ZONE)
