# discourse_integration/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from .api import sync_user_to_discourse_directly # Import the direct sync function

# Import your Discourse API wrapper (we'll assume one exists or will be created)
# For now, we'll just log, but this is where your API calls would go.
# from .api import DiscourseAPI

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(post_save, sender=User)
def user_saved(sender, instance, created, **kwargs):
    """
    Signal handler to sync user to Discourse when a Django user is created or updated.
    WARNING: This calls the sync function directly, which is a blocking operation.
    This is NOT recommended for production environments. Use Celery for async processing.
    """
    # Objective: Do not synchronize Django superusers or staff users.
    # is_superuser implies is_staff, but checking is_superuser directly aligns
    # with the "admin separation" goal more strictly. If you also want to exclude
    # users who can merely access the Django admin (but aren't superusers), use 'is_staff'.
    # Do not sync admin users
    if instance.is_staff or instance.is_superuser:
        logger.info(f"Skipping Discourse sync for superuser or staff: {instance.username}")
        return

    # Trigger the direct sync function
    print(f"Triggering direct sync for user: {instance.username} (ID: {instance.id})")
    sync_user_to_discourse_directly(instance.id)


