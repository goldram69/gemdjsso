# discourse_integration/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
#from .api import sync_user_to_discourse_directly # Import the direct sync function
from .api import DiscourseAPI # Import your API wrapper

print(f"DEBUG: Loading signals.py from: {__file__}") # ADD THIS LINE

# Import your Discourse API wrapper (we'll assume one exists or will be created)
# For now, we'll just log, but this is where your API calls would go.
# from .api import DiscourseAPI

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(post_save, sender=User)
def user_post_save_handler(sender, instance, created, **kwargs):
    print(f"DEBUG: user_post_save_handler triggered for user: {instance.username}") # ADD THIS LINE
    # Prevent synchronization for Django superusers
    if instance.is_staff or instance.is_superuser:
        logger.info(f"Skipping Discourse sync for superuser or staff: {instance.username}")
        return

    # Optional: Skip if not an active user (e.g., if you have other custom user types that shouldn't sync)
    if not instance.is_active:
        logger.info(f"Skipping Discourse sync for inactive user: {instance.username}")
        return

    try:
        print(f"DEBUG: Attempting to instantiate DiscourseAPI for user: {instance.username}") # ADD THIS LINE
        discourse_api = DiscourseAPI()
        if created:
            logger.info(f"Attempting to create Discourse user for Django user {instance.username}")
            discourse_api.create_user(instance)
            logger.info(f"Successfully created user {instance.username} in Discourse.")
        else:
            logger.info(f"Attempting to update Discourse user for Django user {instance.username}")
            discourse_api.update_user(instance)
            logger.info(f"Successfully updated user {instance.username} in Discourse.")

    except Exception as e:
        logger.error(f"An unexpected error occurred during direct sync for user ID {instance.id}: {e}")
        print(f"DEBUG: Error caught in signal handler: {e}") # ADD THIS LINE
