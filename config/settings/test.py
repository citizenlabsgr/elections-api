from .default import *

# BASE_NAME and BASE_DOMAIN are intentionally unset
# None of the commands that rely on these values should run during tests
BASE_URL = "http://example.com"

API_CACHE_SECONDS = 0

###############################################################################
# Core

TEST = True
DEBUG = True
SECRET_KEY = "test"

INSTALLED_APPS += ["django_extensions"]

###############################################################################
# Databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "elections_test",
        "HOST": "127.0.0.1",
    }
}

###############################################################################
# Caches

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(PROJECT_ROOT, ".cache/django"),
    }
}

###############################################################################
# Bugsnag

MIDDLEWARE.remove("bugsnag.django.middleware.BugsnagMiddleware")

LOGGING["root"]["handlers"].remove("bugsnag")  # type: ignore[index]
