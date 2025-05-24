# discourse_integration/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from .api import sync_user_to_discourse_directly # Import the direct sync function

User = get_user_model()

@receiver(post_save, sender=User)
def user_saved(sender, instance, created, **kwargs):
    """
    Signal handler to sync user to Discourse when a Django user is created or updated.
    WARNING: This calls the sync function directly, which is a blocking operation.
    This is NOT recommended for production environments. Use Celery for async processing.
    """
    # Do not sync admin users
    if instance.is_staff or instance.is_superuser:
        return

    # Trigger the direct sync function
    print(f"Triggering direct sync for user: {instance.username} (ID: {instance.id})")
    sync_user_to_discourse_directly(instance.id)


