import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "d*nm^^af$a-we$u1wg4ot244!jzkp!mx5(0g8fbd5rp17$z9!!"

DEBUG = True

ALLOWED_HOSTS = [
    "0.0.0.0",
    "127.0.0.1",
    "localhost",
    "flock.archive.house",
    "157.245.238.241",
    "archive-flock.auth0.com",
    "village.archive.house",
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "flock",
    "social_django",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

SILENCED_SYSTEM_CHECKS = ["admin.E408"]

ROOT_URLCONF = "server.urls"

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
            ]
        },
    }
]

WSGI_APPLICATION = "server.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "psqlextra.backend",
        "NAME": "flock",
        "USER": "flock",
        "PASSWORD": "flock",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/static/"


# Auth0 stuff

SOCIAL_AUTH_TRAILING_SLASH = False  # Remove trailing slash from routes
SOCIAL_AUTH_AUTH0_DOMAIN = "archive-flock.auth0.com"
SOCIAL_AUTH_AUTH0_KEY = "UGu6gdsS56FqhYvAaNdeYgjbe7n9IqNL"
SOCIAL_AUTH_AUTH0_SECRET = os.getenv("SOCIAL_AUTH_AUTH0_SECRET")

EMAIL_WHITELIST = set(os.getenv("EMAIL_WHITELIST").split(","))

SOCIAL_AUTH_AUTH0_SCOPE = ["openid", "profile", "email"]

AUTHENTICATION_BACKENDS = {"flock.auth0backend.Auth0", "django.contrib.auth.backends.ModelBackend"}

LOGIN_URL = "/login/auth0"
LOGIN_REDIRECT_URL = "/"


# Sentry

if os.getenv("PRODUCTION") and int(os.getenv("PRODUCTION")):
    sentry_sdk.init(
        dsn="https://c3f1f286f7964d6b8761fee94f1fc73d@sentry.io/1758125",
        integrations=[DjangoIntegration()],
        environment=f"server",
    )
