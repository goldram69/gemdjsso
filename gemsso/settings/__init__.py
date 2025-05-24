# your_project/settings/__init__.py

import os

# Determine which settings file to load based on the DJANGO_SETTINGS_MODULE environment variable
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'gemsso.settings.development')

# Import the settings from the determined module
if settings_module == 'gemsso.settings.production':
    from .production import *
else:
    from .development import *
