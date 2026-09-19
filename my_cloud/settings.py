"""
Django settings for the my_cloud project.

Configuration is driven by environment variables via django-environ. A local
`.env` file at the project root is read automatically if present; see
`.env.example` for the supported variables. Sensible defaults are provided so
the project runs locally with zero configuration against the Postgres container
started by `docker-compose-dev.yaml`.
"""

from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / ...
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)

# Read a .env file at the project root if it exists.
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-key-change-me")

DEBUG = env.bool("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Media files path. MEDIA_ROOT is kept as a trailing-slashed string because the
# app relies on string path operations (concatenation and prefix slicing) in
# file_handler/models.py and shared_secret/models.py.
MEDIA_URL = "/media/"
MEDIA_ROOT = str(BASE_DIR / "media") + "/"

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "file_handler.apps.FileHandlerConfig",
    "shared_secret.apps.SharedSecretConfig",
    "rest_framework",
    "oauth2_provider",
    "api",
    "mptt",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "my_cloud.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = "my_cloud.wsgi.application"

# Database
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://postgres:postgres@localhost:5432/postgres",
    )
}

# Default primary key field type. Kept as AutoField to match the existing
# migrations and avoid generating spurious primary-key alterations.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Password validation
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

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_URL = "/logout"
LOGOUT_REDIRECT_URL = "/"

# Internationalization
LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Rome"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
# Source assets served directly by runserver in development (finders look here).
STATICFILES_DIRS = [BASE_DIR / "static"]
# Destination for `collectstatic` (served by nginx in the production stack).
STATIC_ROOT = BASE_DIR / "staticfiles"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

OAUTH2_PROVIDER = {
    "SCOPES": {"read": "Read scope", "write": "Write scope"},
}

AUTHENTICATION_BACKENDS = [
    # username/email + password (used by the Django admin for staff/superusers)
    "my_cloud.authentication.CustomAuthentication",
    # social login (Google) via allauth
    "allauth.account.auth_backends.AuthenticationBackend",
]

# ---- allauth (Google sign-in as the only registration path) ------------------
# Local (password) self-registration is closed; new users are created only by
# signing in with Google. Staff/superusers still log in with a password via /admin/.
ACCOUNT_ADAPTER = "my_cloud.adapters.NoNewUsersAccountAdapter"
SOCIALACCOUNT_ADAPTER = "my_cloud.adapters.GoogleSignupAdapter"
SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# Google verifies email ownership, so a Google login whose verified email matches
# an existing account logs into that account and links to it (seamless sign-in for
# accounts pre-created via the admin, e.g. the superuser). Safe ONLY because every
# provider here is fully trusted — do not enable this if adding an untrusted provider.
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": env("GOOGLE_OAUTH_CLIENT_ID", default=""),
            "secret": env("GOOGLE_OAUTH_CLIENT_SECRET", default=""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        # prompt=select_account -> always show the Google account chooser
        # instead of silently reusing the last account.
        "AUTH_PARAMS": {"access_type": "online", "prompt": "select_account"},
    }
}
