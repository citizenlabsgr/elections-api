import os

import dj_database_url

from .default import *

BASE_NAME = os.environ["HEROKU_APP_NAME"]
BASE_DOMAIN = f"{BASE_NAME}.io"
BASE_URL = f"https://{BASE_DOMAIN}"

###############################################################################
# Core

MIDDLEWARE.insert(0, "bugsnag.django.middleware.BugsnagMiddleware")

SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = ["localhost", ".michiganelections.io"]

CSRF_TRUSTED_ORIGINS = ["https://*.michiganelections.io"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

###############################################################################
# Databases

DATABASES = {}
DATABASES["default"] = dj_database_url.config()

###############################################################################
# Caches

CACHES: dict = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ["REDIS_URL"],
    }
}

###############################################################################
# Authentication

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

###############################################################################
# Static files

STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
