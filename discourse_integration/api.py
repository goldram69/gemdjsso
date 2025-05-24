# discourse_integration/api.py

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class DiscourseAPIError(Exception):
    """Custom exception for Discourse API errors."""
    pass

class DiscourseAPI:
    def __init__(self):
        self.base_url = settings.DISCOURSE_BASE_URL
        self.api_key = settings.DISCOURSE_API_KEY
        self.api_username = settings.DISCOURSE_API_USERNAME
        self.headers = {
            'Api-Key': self.api_key,
            'Api-Username': self.api_username,
            'Content-Type': 'application/json', # Most API calls expect JSON
            'Accept': 'application/json',
        }

    def _request(self, method, endpoint, data=None, params=None):
        url = f'{self.base_url}{endpoint}'
        try:
            response = requests.request(method, url, json=data, params=params, headers=self.headers)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise DiscourseAPIError(f"Discourse API request failed: {e}")
        except Exception as e:
            raise DiscourseAPIError(f"An unexpected error occurred during Discourse API call: {e}")

    def create_user(self, email, username, external_id, name=None, password=None, active=True, **kwargs):
        """Creates a user in Discourse."""
        endpoint = '/users'
        payload = {
            'email': email,
            'username': username,
            'external_id': str(external_id), # Ensure external_id is a string
            'name': name or username,
            'password': password, # Consider implications of setting passwords this way
            'active': active,
            'suppress_welcome_message': True, # Avoid welcome email from Discourse
            **kwargs
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._request('POST', endpoint, data=payload)

    def update_user(self, discourse_user_id, **kwargs):
        """Updates a user in Discourse."""
        endpoint = f'/users/{discourse_user_id}'
        payload = {
            # Add fields to update, e.g.:
            # 'email': email,
            # 'username': username,
            # 'name': name,
            # 'user_fields': { 'field_id': 'value' },
            **kwargs
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._request('PUT', endpoint, data=payload)

    def get_user_by_external_id(self, external_id):
        """Gets a user from Discourse by external_id."""
        endpoint = f'/users/by-external/{external_id}.json'
        try:
            return self._request('GET', endpoint)
        except DiscourseAPIError as e:
            # Handle 404 specifically if the user is not found
            if '404 Client Error: Not Found' in str(e): # Check for specific 404 message
                return None
            raise # Re-raise other API errors

    def delete_user(self, discourse_user_id, **kwargs):
        """Deletes a user in Discourse."""
        endpoint = f'/admin/users/{discourse_user_id}.json'
        payload = {
            # 'block_email': True,
            # 'block_urls': True,
            # 'delete_posts': True,
            **kwargs
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._request('DELETE', endpoint, data=payload)


discourse_api = DiscourseAPI() # Initialize the API client

def sync_user_to_discourse_directly(user_id):
    """
    Synchronizes a Django user's data to Discourse directly (blocking operation).
    Creates the user in Discourse if they don't exist, or updates them.
    """
    from .models import DiscourseProfile # Import here to avoid circular dependency

    try:
        user = User.objects.get(id=user_id)
        # Do not sync admin users
        if user.is_staff or user.is_superuser:
            print(f"Skipping direct sync for admin user: {user.username}")
            return

        profile, created = DiscourseProfile.objects.get_or_create(user=user)

        # Use Django user ID as the external_id
        external_id = str(user.id)

        discourse_user_id = profile.discourse_user_id

        if discourse_user_id:
            # User exists in Discourse, attempt to update
            print(f"Attempting to update Discourse user ID {discourse_user_id} for Django user {user.username}")
            try:
                # Fetch the Discourse user by external_id to confirm existence and get latest data
                discourse_user_data = discourse_api.get_user_by_external_id(external_id)

                if discourse_user_data:
                     # Update the user in Discourse
                     update_payload = {
                         'email': user.email,
                         'username': user.username,
                         'name': user.get_full_name() or user.username,
                         'active': user.is_active, # Sync active status
                     }
                     discourse_api.update_user(discourse_user_id, **update_payload)
                     print(f"Successfully updated Discourse user ID {discourse_user_id}.")
                else:
                    # User not found in Discourse despite having a discourse_user_id in profile
                    # This might happen if the user was deleted in Discourse directly.
                    # Attempt to re-create the user in Discourse.
                    print(f"Discourse user with external_id {external_id} not found. Attempting to re-create.")
                    profile.discourse_user_id = None # Reset discourse_user_id
                    profile.save()
                    # Recursively call to trigger creation logic
                    sync_user_to_discourse_directly(user.id)
                    return


            except DiscourseAPIError as e:
                print(f"Error updating Discourse user {user.username} (ID: {discourse_user_id}): {e}")
                # For direct sync, you might want more robust error handling or logging here
                # as there's no retry mechanism like Celery.
                pass # Continue execution, but error is logged

        else:
            # User does not exist in Discourse, attempt to create
            print(f"Attempting to create Discourse user for Django user {user.username}")
            try:
                # Check if a user with this external_id already exists in Discourse
                existing_discourse_user = discourse_api.get_user_by_external_id(external_id)

                if existing_discourse_user:
                    # User exists in Discourse with this external_id, link the profile
                    discourse_user_id = existing_discourse_user.get('id')
                    profile.discourse_user_id = discourse_user_id
                    profile.save()
                    print(f"Linked existing Discourse user ID {discourse_user_id} to Django user {user.username}.")
                    # Optionally trigger an update to sync latest data
                    sync_user_to_discourse_directly(user.id) # Call again to sync latest data
                    return
                else:
                    # Create the user in Discourse
                    create_payload = {
                        'email': user.email,
                        'username': user.username,
                        'external_id': external_id,
                        'name': user.get_full_name() or user.username,
                        'active': user.is_active, # Sync active status
                        'password': User.objects.make_random_password(), # Set a random password
                        'suppress_welcome_message': True, # Avoid welcome email from Discourse
                    }
                    discourse_user_data = discourse_api.create_user(**create_payload)
                    discourse_user_id = discourse_user_data.get('id')

                    if discourse_user_id:
                        profile.discourse_user_id = discourse_user_id
                        profile.save()
                        print(f"Successfully created Discourse user ID {discourse_user_id} for Django user {user.username}.")
                    else:
                        # Creation failed, log the response
                        print(f"Discourse user creation failed for {user.username}. Response: {discourse_user_data}")
                        pass # Continue execution, but error is logged

            except DiscourseAPIError as e:
                print(f"Error creating Discourse user for {user.username}: {e}")
                pass # Continue execution, but error is logged

        # Update last synced timestamp
        profile.last_synced_at = timezone.now()
        profile.save()

    except User.DoesNotExist:
        print(f"Django user with ID {user_id} not found for direct sync.")
    except Exception as e:
        print(f"An unexpected error occurred during direct sync for user ID {user_id}: {e}")
        pass # Continue execution, but error is logged
