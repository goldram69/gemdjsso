# your_project/settings/development.py

from .base import *
# No need to re-initialize env or call read_env() here.
# base.py handles loading the .env file based on DJANGO_SETTINGS_MODULE.

# Override base settings for development
DEBUG = True # Explicitly set DEBUG to True for development

# ALLOWED_HOSTS for local development
# Use env.list with a default if you want to allow overriding from .env.development
# ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', 'discourse.localhost'])
# Or simply extend the list if you want to ensure these are always allowed in dev:
ALLOWED_HOSTS += ['localhost', '127.0.0.1', 'discourse.localhost']

# Database URL for development
# This will be read from .env.development by base.py
# DATABASES = {'default': env.db('DATABASE_URL')} # This line is no longer needed here

# Email settings for local development (e.g., Mailpit)
# These will be read from .env.development by base.py
# EMAIL_BACKEND = env('EMAIL_BACKEND')
# EMAIL_HOST = env('EMAIL_HOST')
# EMAIL_PORT = env('EMAIL_PORT')
# EMAIL_USE_TLS = env('EMAIL_USE_TLS')
# EMAIL_USE_SSL = env('EMAIL_USE_SSL')
# EMAIL_HOST_USER = env('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
# DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')


# Discourse Integration Settings for development
# These will be read from .env.development by base.py
# DISCOURSE_SSO_SECRET = env('DISCOURSE_SSO_SECRET')
# DISCOURSE_BASE_URL = env('DISCOURSE_BASE_URL')
# DISCOURSE_API_KEY = env('DISCOURSE_API_KEY')
# DISCOURSE_API_USERNAME = env('DISCOURSE_API_USERNAME')
# DISCOURSE_SSO_CALLBACK_URL = env('DISCOURSE_SSO_CALLBACK_URL') # Should match your local setup URL
