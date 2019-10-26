from datetime import timedelta

import bugsnag
import dj_database_url
import redis

from .default import *


BASE_NAME = 'localhost'
BASE_DOMAIN = f"{BASE_NAME}:8000"
BASE_URL = f"http://{BASE_DOMAIN}"

DEFAULT_API_CACHE_SECONDS = 60
REGISTRATION_API_CACHE_SECONDS = 60

###############################################################################
# Core

DEBUG = True
SECRET_KEY = 'dev'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.ngrok.io']

INSTALLED_APPS += ['django_extensions', 'livereload', 'debug_toolbar']

MIDDLEWARE += ['livereload.middleware.LiveReloadScript']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

LOGGING['loggers']['elections']['level'] = 'DEBUG'

###############################################################################
# Databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'elections_dev',
        'HOST': '127.0.0.1',
    },
    'remote': dj_database_url.config(),
}

###############################################################################
# Django Debug Toolbar

INTERNAL_IPS = ['127.0.0.1']

DEBUG_TOOLBAR_CONFIG = {'SHOW_COLLAPSED': True}

###############################################################################
# Bugsnag

bugsnag.configure(release_stage='local')

###############################################################################
# Swagger

SWAGGER_SETTINGS['DOC_EXPANSION'] = 'full'
