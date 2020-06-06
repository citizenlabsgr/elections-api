from django.conf import settings

from pendulum import datetime


MI_SOS_URL = "https://mvic.sos.state.mi.us"

SCRAPER_LAST_UPDATED = datetime(2020, 6, 6, tz=settings.TIME_ZONE)
PARSER_LAST_UPDATED = datetime(2020, 6, 6, tz=settings.TIME_ZONE)
