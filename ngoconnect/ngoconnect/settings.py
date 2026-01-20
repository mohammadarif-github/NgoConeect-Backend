import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
import structlog
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'changeme-this-in-production')

DEBUG = os.environ.get('DEBUG', '0') == '1'

ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

DJANGO_ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if DJANGO_ALLOWED_HOSTS:
    ALLOWED_HOSTS.extend(DJANGO_ALLOWED_HOSTS.split(','))

if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1', '*'])

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only allow all in development
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

AUTH_USER_MODEL = 'user.User'

INSTALLED_APPS = [
    'user',
    'core',
    'volunteers',
    'projects',
    'donations',
    'notifications',
    'rest_framework',
    'drf_spectacular',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_celery_beat',
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ngoconnect.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "ngoconnect.wsgi.application"


DATABASE_URL = os.environ.get('DATABASE_URL')
# print('secret key:', SECRET_KEY)

# print("DATABASE_URL:", DATABASE_URL)
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': os.environ.get('DB_HOST'),
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASS'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': 300,
        }
    }


REDIS_URL = os.environ.get('REDIS_URL', os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'get_apis': '100/hour',
        'post_apis': '100/hour',
        'email_apis': '5/minute',
    }
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'BLACKLIST_AFTER_ACCESS_TOKEN_EXPIRE': True,
    'INCLUDE_JTI_CLAIM': True,
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', #nosec
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
]

SPECTACULAR_SETTINGS = {
    'TITLE': 'NgoConnect API',
    'DESCRIPTION': 'API Documentation for NgoConnect Backend',
    'VERSION': '1.0.0',
    "COMPONENT_SPLIT_REQUEST": True,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Enter: Bearer <your-token>'
        }
    },
    'SECURITY': [{'Bearer': []}],
    'AUTHENTICATION_WHITELIST': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email Configuration (Brevo)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'ngoconnect.bd@gmail.com')

# Frontend URL for email links
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
# SSLCommerz Configuration
SSLCOMMERZ_STORE_ID = os.environ.get('SSLCOMMERZ_STORE_ID', 'ngoco6969db2ca5da7')
SSLCOMMERZ_STORE_PASS = os.environ.get('SSLCOMMERZ_STORE_PASS', 'ngoco6969db2ca5da7@ssl')
SSLCOMMERZ_IS_SANDBOX = os.environ.get('SSLCOMMERZ_IS_SANDBOX', 'True') == 'True'