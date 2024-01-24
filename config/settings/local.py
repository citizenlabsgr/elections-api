import bugsnag
import dj_database_url

from .default import *

BASE_NAME = "localhost"
BASE_DOMAIN = f"{BASE_NAME}:8000"
BASE_URL = f"http://{BASE_DOMAIN}"

API_CACHE_SECONDS = 5

###############################################################################
# Core

DEBUG = True
SECRET_KEY = "dev"

ALLOWED_HOSTS = ["127.0.0.1", "localhost", ".ngrok.io"]

INSTALLED_APPS += ["django_extensions", "django_browser_reload", "debug_toolbar"]

MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

LOGGING["loggers"]["elections"]["level"] = "DEBUG"  # type: ignore

###############################################################################
# Databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "elections_dev",
        "HOST": "127.0.0.1",
    },
    "remote": dj_database_url.config(),
}

###############################################################################
# Django Debug Toolbar

INTERNAL_IPS = ["127.0.0.1"]

DEBUG_TOOLBAR_CONFIG = {"SHOW_COLLAPSED": True}

###############################################################################
# Bugsnag

bugsnag.configure(release_stage="local")
