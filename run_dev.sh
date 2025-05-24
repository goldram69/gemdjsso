#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Set the Django settings module for development
export DJANGO_SETTINGS_MODULE='gemsso.settings.development'

# Run your Django command (e.g., runserver)
#python manage.py runserver 0.0.0.0:8000

# Or for migrations:
# python manage.py migrate

# Or for creating superuser:
# python manage.py createsuperuser
