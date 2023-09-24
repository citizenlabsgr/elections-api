from datetime import timedelta

from django.conf import settings
from pendulum import datetime

MVIC_URL = "https://mvic.sos.state.mi.us"

TERMS = {
    "United States Senator": "6 Year Term",
    "Representative in Congress": "2 Year Term",
    "Representative in State Legislature": "2 Year Term",
}

_SHIFT = timedelta(hours=12)
SCRAPER_LAST_UPDATED = datetime(2023, 9, 24, tz=settings.TIME_ZONE) + _SHIFT
PARSER_LAST_UPDATED = datetime(2023, 9, 23, tz=settings.TIME_ZONE) + _SHIFT
