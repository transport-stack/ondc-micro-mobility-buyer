import logging

import corsheaders
from corsheaders.defaults import default_headers

from modules.env_main import DEBUG, SECRET_KEY, REDIS_HOST
import os
import warnings
from datetime import timedelta
from pathlib import Path
import redis
from urllib.parse import urlparse

warnings.filterwarnings("ignore")
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")
CSRF_TRUSTED_ORIGINS = ["http://", "https://"]
CORS_ALLOW_ALL_ORIGINS = True

# Application definition


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "corsheaders",
    "custom_cities",
    "common",
    "accounts",
    "transit",
    "tickets",
    "payments",
    "journey",
    "drf_spectacular",
    "coupons",
    "taskschedule",
    "import_export",
    "django_celery_beat",
    "rangefilter",
    "ondc_buyer_backend",
    "ondc_micromobility_api",
    "nammayatri",
    "subscribe_app",
]

if DEBUG:
    INSTALLED_APPS.append("django_extensions")

SITE_ID = 1

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 5,
    "DATETIME_FORMAT": "iso-8601",
    "EXCEPTION_HANDLER": "modules.views.custom_exception_handler",
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '50000/min',
        'user': '10000/min'
    }
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SOCIALACCOUNT_LOGIN_ON_GET = True

AUTHENTICATION_BACKENDS = ["allauth.account.auth_backends.AuthenticationBackend"]

AUTH_USER_MODEL = "accounts.MyUser"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=365),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ONDC Micro-mobility APIs",
    "DESCRIPTION": "Transit, Payments, Tickets and Users API for Transit Bus Ticketing API for Chartr app. This API "
                   "uses the "
                   "CustomJSONRenderer to format responses.",
    "VERSION": "1.0.0",
    "ENUM_NAME_OVERRIDES": {"TransactionStatus": "modules.models.TransactionStatus"},
    "COMPONENT_SPLIT_REQUEST": False,
    "COMPONENT_SPLIT_RESPONSE": False,
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "modules.middlewares.log_post_request_middleware.LogPostRequestsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    'X-Ticket-Token',
]

ROOT_URLCONF = "ptx_core_backend.urls"
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 10 MB

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ptx_core_backend.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.getenv("PROD_DB_NAME"),
            "USER": os.getenv("PROD_DB_USER"),
            "PASSWORD": os.getenv("PROD_DB_PASS"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT"),
        }
    }


def is_redis_available(host, port, password=None):
    try:
        client = redis.StrictRedis(host=host, port=port, password=password)
        client.ping()
        return True
    except redis.ConnectionError:
        return False
    except Exception as e:
        logging.error(e)
        return False


REDIS_DB = "1"
# Fallback to in-memory cache
FALLBACK_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

parsed_url = urlparse(REDIS_HOST)
REDIS_BASE_URL = parsed_url.hostname
REDIS_PORT = parsed_url.port
REDIS_PASSWORD = parsed_url.password

# IS_REDIS_AVAILABLE = is_redis_available(REDIS_BASE_URL, REDIS_PORT, REDIS_PASSWORD)

try:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"{REDIS_HOST}/{REDIS_DB}",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }
except Exception as e:
    logging.error("Redis is not available. Falling back to in-memory cache.")
    raise

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
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

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_URL = "https://cdn-001.chartr.in/ptx-api.chartr.in/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_HOST = os.getenv("REDIS_HOST", "redis://redis:6379/1")

CELERY_BROKER_URL = REDIS_HOST
CELERY_RESULT_BACKEND = REDIS_HOST
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kolkata"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ELK CREDENTIALS
ELK_SECRET_TOKEN = str(os.getenv("ELK_SECRET_TOKEN"))
ELK_SERVER_URL = str(os.getenv("ELK_SERVER_URL"))
ELASTIC_APM_ENABLED = False
try:
    ELASTIC_APM_ENABLED = os.getenv("ELASTIC_APM_ENABLED")
    if ELASTIC_APM_ENABLED.lower() == "true":
        ELASTIC_APM_ENABLED = True
    else:
        ELASTIC_APM_ENABLED = False
except Exception:
    logging.info("ELASTIC_APM_ENABLED .env read error")
if ELASTIC_APM_ENABLED:
    INSTALLED_APPS.append("elasticapm.contrib.django")

ELASTIC_APM = {
    "SERVICE_NAME": "OD-MM-buyer-api-service",
    "SERVER_URL": f"{ELK_SERVER_URL}",
    # "SERVER_CERT": f"{BASE_DIR}/elk.chartr.in.crt",
    "SECRET_TOKEN": f"{ELK_SECRET_TOKEN}",
    "SERVER_TIMEOUT": "5s",
    "LOG_LEVEL": "critical",
    "CLOUD_PROVIDER": False,
    "DEBUG": DEBUG,
    "ELASTIC_APM_ENABLED": ELASTIC_APM_ENABLED,
}
