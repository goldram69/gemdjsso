# discourse_integration/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings # noqa: F401 (Suppress unused-import warning)
from django.contrib.auth import get_user_model
from .api import DiscourseAPI

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(post_save, sender=User)
def user_post_save_handler(sender, instance, created, **kwargs):
    """
    Handles post_save signal for Django User model.
    Synchronizes user to Discourse, but skips superusers.
    """
    # Prevent synchronization for Django superusers or staff
    if instance.is_staff or instance.is_superuser:
        logger.info(f"Skipping Discourse sync for superuser or staff: {instance.username}")
        return

    # Optional: Skip if not an active user (e.g., if you have other custom user types that shouldn't sync)
    if not instance.is_active:
        logger.info(f"Skipping Discourse sync for inactive user: {instance.username}")
        return

    try:
        discourse_api = DiscourseAPI()
        if created:
            logger.info(f"Attempting to create Discourse user for Django user {instance.username}")
            discourse_api.create_user(instance) # This will now also update DiscourseProfile
            logger.info(f"Successfully created user {instance.username} in Discourse.")
        else:
            logger.info(f"Attempting to update Discourse user for Django user {instance.username}")
            discourse_api.update_user(instance) # This will now use DiscourseProfile's ID
            logger.info(f"Successfully updated user {instance.username} in Discourse.")

    except Exception as e:
        logger.error(f"An unexpected error occurred during direct sync for user ID {instance.id}: {e}")
