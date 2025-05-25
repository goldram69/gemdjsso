# your_project/settings/development.py

from .base import *
# All environment variables and base settings are already loaded by base.py

# Override or extend base settings for development
# DEBUG is already set by base.py from .env.development. We can explicitly set it
# to True here if we want to ensure it's always True for this file, regardless of .env.
DEBUG = True

# ALLOWED_HOSTS for local development
# Add specific hosts for development. Base.py already loaded from .env.development.
ALLOWED_HOSTS += ['localhost', '127.0.0.1', '192.168.1.80', 'discourse.localhost']

# No need to re-define DATABASES, EMAIL_*, DISCOURSE_* here
# unless you want to hardcode values that *override* what's in .env.development,
# which is generally not the intent. All these are correctly loaded via base.py.
