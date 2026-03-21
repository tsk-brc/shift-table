"""
Test settings for shift_table project.
"""

from .settings import *

# Use in-memory SQLite database for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {
            "NAME": ":memory:",
        },
    }
}

# Disable debug mode for testing
DEBUG = False

# Use a fast password hasher for testing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}

# Test secret key
SECRET_KEY = "test-secret-key-for-testing-only"

# Disable CSRF for testing
MIDDLEWARE = [m for m in MIDDLEWARE if "csrf" not in m.lower()]

# Static files settings for testing
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files settings for testing
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Disable apps that might interfere with testing
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "shift.tests"]

# Test database isolation
TEST_RUNNER = "django.test.runner.DiscoverRunner"
