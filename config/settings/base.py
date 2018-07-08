import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(CONFIG_ROOT)

###############################################################################
# Core

INSTALLED_APPS = [
    # Overrides
    'grappelli',
    # Standard
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.postgres',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    # Third party
    'memoize',
    'rest_framework',
    'drf_yasg',
    'django_filters',
    # First party
    'elections',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ]
        },
    }
]

WSGI_APPLICATION = 'config.wsgi.application'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'simple': {'format': '%(levelname)s: %(message)s'}},
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        }
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO'},
        'elections': {'handlers': ['console'], 'level': 'DEBUG'},
    },
}

SITE_ID = 1

###############################################################################
# Sessions

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

###############################################################################
# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'US/Michigan'

USE_I18N = True

USE_L10N = True

USE_TZ = True

###############################################################################
# Static files

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')

###############################################################################
# CORS

CORS_ORIGIN_ALLOW_ALL = True

###############################################################################
# Grappelli

GRAPPELLI_ADMIN_TITLE = "Michigan Elections Admin"

###############################################################################
# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_VERSION': '0',
    'ALLOWED_VERSIONS': ['0'],
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
}

###############################################################################
# Swagger

SWAGGER_SETTINGS = {'USE_SESSION_AUTH': False, 'SECURITY_DEFINITIONS': {}}

###############################################################################
# Requests cache

REQUESTS_CACHE_EXPIRE_AFTER = None
