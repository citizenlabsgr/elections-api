from datetime import timedelta

import bugsnag
import dj_database_url
import redis
import requests_cache

from .base import *


BASE_NAME = 'localhost'
BASE_DOMAIN = f"{BASE_NAME}:8000"
BASE_URL = f"http://{BASE_DOMAIN}"

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
# Caches

REQUESTS_CACHE_EXPIRE_AFTER = timedelta(minutes=5)

###############################################################################
# Django Debug Toolbar

INTERNAL_IPS = ['127.0.0.1']

DEBUG_TOOLBAR_CONFIG = {'SHOW_COLLAPSED': True}

###############################################################################
# Bugsnag

bugsnag.configure(release_stage='local')
