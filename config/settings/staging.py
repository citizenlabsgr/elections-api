from .production import *


BASE_NAME = os.environ["HEROKU_APP_NAME"]
if "-pr" in BASE_NAME:
    BASE_DOMAIN = f"{BASE_NAME}.herokuapp.com"
else:
    BASE_NAME, SUBDOMAIN = BASE_NAME.rsplit("-", 1)
    BASE_DOMAIN = f"{SUBDOMAIN}.{BASE_NAME}.com"
BASE_URL = f"https://{BASE_DOMAIN}"

###############################################################################
# Core

ALLOWED_HOSTS += [
    ".herokuapp.com",
    # TODO: Add your custom domain
]
