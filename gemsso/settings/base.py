# your_project/settings/base.py

import os
from pathlib import Path
import environ # Using django-environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Determine the environment type from DJANGO_SETTINGS_MODULE
# This needs to happen *before* initializing env if we want to load specific .env files
# Default to 'development' if DJANGO_SETTINGS_MODULE is not explicitly set
settings_module_name = os.environ.get('DJANGO_SETTINGS_MODULE', 'your_project.settings.development')
ENV_TYPE = settings_module_name.split('.')[-1] # Extracts 'development' or 'production'

# Initialize django-environ
env = environ.Env(
    # Define type conversion and default values
    DEBUG=(bool, False),
    SECRET_KEY=(str), # SECRET_KEY must be provided
    ALLOWED_HOSTS=(list, []), # ALLOWED_HOSTS is a list

    # Database URL definition - django-environ will parse this
    DATABASE_URL=(str, 'sqlite:///db.sqlite3'), # Default to SQLite for simplicity if not provided

    # Email settings
    EMAIL_BACKEND=(str, 'django.core.mail.backends.console.EmailBackend'), # Default to console backend
    EMAIL_HOST=(str, 'localhost'),
    EMAIL_PORT=(int, 25),
    EMAIL_USE_TLS=(bool, False),
    EMAIL_USE_SSL=(bool, False),
    EMAIL_HOST_USER=(str, ''),
    EMAIL_HOST_PASSWORD=(str, ''),
    DEFAULT_FROM_EMAIL=(str, 'webmaster@localhost'),


    # Discourse Integration Settings
    DISCOURSE_SSO_SECRET=(str), # Required for SSO
    DISCOURSE_BASE_URL=(str),   # Required for API and SSO URLs
    DISCOURSE_API_KEY=(str),    # Required for API sync
    DISCOURSE_API_USERNAME=(str, 'system'), # Default API username
    # Corrected: DISCOURSE_SSO_LOGIN_URL is derived, not an env var directly
    # DISCOURSE_SSO_CALLBACK_URL is derived from DISCOURSE_BASE_URL and URL patterns,
    # but defining it explicitly via env var is safer if your external URL differs
    DISCOURSE_SSO_CALLBACK_URL=(str), # Required, must be externally accessible by Discourse

    # Add other settings you might need
)

# Read environment variables from the appropriate .env file
# This is the crucial part: load the .env file based on the environment type
if ENV_TYPE == 'development':
    environ.Env.read_env(os.path.join(BASE_DIR, '.env.development'))
elif ENV_TYPE == 'production':
    environ.Env.read_env(os.path.join(BASE_DIR, '.env.production'))
# If ENV_TYPE is neither 'development' nor 'production', no .env file is loaded here.
# This relies on environment variables being set directly in the shell or by a deployment system.


# --- Django Base Settings ---

# SECRET_KEY is required. django-environ reads it from the environment.
SECRET_KEY = env('SECRET_KEY')

# DEBUG is usually controlled by environment variable
DEBUG = env('DEBUG')

# ALLOWED_HOSTS is a list of strings
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'discourse_integration', # Your reusable app
    'django_extensions', # For runserver_plus etc.
    # 'django_celery_beat', # Commented out for basic setup
    # 'django_celery_results', # Commented out for basic setup
    # ... other apps
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gemsso.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Project-level templates
        'APP_DIRS': True, # Allow apps to provide templates
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gemsso.wsgi.application'

# Database Configuration using DATABASE_URL
# env.db() parses the DATABASE_URL string and returns the dictionary Django needs
DATABASES = {
    'default': env.db('DATABASE_URL')
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Collect static files here

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Discourse Integration Settings ---
DISCOURSE_SSO_SECRET = env('DISCOURSE_SSO_SECRET')
DISCOURSE_BASE_URL = env('DISCOURSE_BASE_URL')
DISCOURSE_API_KEY = env('DISCOURSE_API_KEY')
DISCOURSE_API_USERNAME = env('DISCOURSE_API_USERNAME')
DISCOURSE_SSO_LOGIN_URL = f'{DISCOURSE_BASE_URL}/session/sso_provider'
DISCOURSE_SSO_CALLBACK_URL = env('DISCOURSE_SSO_CALLBACK_URL') # Must be accessible by Discourse

# --- Email settings (for Mailpit/SMTP) ---
EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
EMAIL_USE_SSL = env('EMAIL_USE_SSL')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
