import bugsnag

from .default import *


# BASE_NAME and BASE_DOMAIN are intentionally unset
# None of the commands that rely on these values should run during tests
BASE_URL = 'http://example.com'

DEFAULT_API_CACHE_SECONDS = 0
REGISTRATION_API_CACHE_SECONDS = 0

###############################################################################
# Core

TEST = True
DEBUG = True
SECRET_KEY = 'test'

INSTALLED_APPS += ['django_extensions']

###############################################################################
# Databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'elections_test',
        'HOST': '127.0.0.1',
    }
}

###############################################################################
# Caches

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '.cache/django',
    }
}

###############################################################################
# Bugsnag

bugsnag.configure(release_stage='test')
