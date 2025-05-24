# discourse_integration/models.py

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class DiscourseProfile(models.Model):
    """
    Links a Django user to their Discourse representation.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='discourse_profile')
    discourse_user_id = models.IntegerField(unique=True, null=True, blank=True, help_text="Discourse user ID")
    last_synced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Discourse Profile for {self.user.username}"

# Signal to create a DiscourseProfile when a new user is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_discourse_profile(sender, instance, created, **kwargs):
    if created and not (instance.is_staff or instance.is_superuser): # Do not create profiles for admins
        DiscourseProfile.objects.get_or_create(user=instance)

# Signal to potentially handle Discourse user deletion when a Django user is deleted
# For a basic setup without Celery, this will just print a message.
# In a production setup, this would trigger an async task to delete the user in Discourse.
@receiver(post_delete, sender=settings.AUTH_USER_MODEL)
def delete_discourse_user_signal(sender, instance, **kwargs):
    if not (instance.is_staff or instance.is_superuser): # Do not attempt to delete admins from Discourse
        try:
            profile = instance.discourse_profile
            if profile.discourse_user_id:
                print(f"Django user {instance.username} (Discourse ID: {profile.discourse_user_id}) deleted. "
                      f"Manual deletion in Discourse might be required if not handled by a background task.")
                # In a production system, you would trigger an async task here:
                # from .tasks import delete_discourse_user_task
                # delete_discourse_user_task.delay(profile.discourse_user_id)
        except DiscourseProfile.DoesNotExist:
            pass # No Discourse profile to delete


