"""Local HTTP development settings; production settings remain the default."""

from .settings import *  # noqa: F403

DEBUG = True
SECRET_KEY = 'local-development-only-not-for-production'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.dev.sqlite3',  # noqa: F405
    },
}
MAILERS = {
    'default': {'BACKEND': 'django.core.mail.backends.console.EmailBackend'},
}

MEDIA_ROOT = BASE_DIR / "media-dev"
