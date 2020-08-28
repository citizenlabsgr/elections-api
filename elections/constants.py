from django.conf import settings

from pendulum import datetime


MI_SOS_URL = "https://mvic.sos.state.mi.us"

SCRAPER_LAST_UPDATED = datetime(2020, 8, 28, hour=19, tz=settings.TIME_ZONE)
PARSER_LAST_UPDATED = datetime(2020, 8, 23, tz=settings.TIME_ZONE)
