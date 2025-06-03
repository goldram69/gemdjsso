# discourse_integration/api.py
import requests # Keep this import if you're suppressing warnings, but it's not used directly for client init
import logging
import secrets
import string
from django.conf import settings
from django.contrib.auth import get_user_model # Import get_user_model
from django.utils import timezone # Import timezone for last_synced_at

logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model() # Define User here

def generate_random_password(length=12):
    """
    Generates a cryptographically secure random password.
    Replaces deprecated BaseUserManager.make_random_password().
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class DiscourseAPIError(Exception):
    """Custom exception for Discourse API errors."""
    pass

class DiscourseAPI:
    def __init__(self):
        print(f"DEBUG: Loading api.py from: {__file__}")
        print("DEBUG: DiscourseAPI __init__ called.")
        print(f"DEBUG: DiscourseAPI instance created from: {__file__}")

        self.base_url = settings.DISCOURSE_BASE_URL.rstrip('/')

        # --- ADD THESE DEBUG LINES ---
        print(f"DEBUG: DISCOURSE_BASE_URL (raw from settings): '{settings.DISCOURSE_BASE_URL}'")
        print(f"DEBUG: self.base_url (after rstrip): '{self.base_url}'")
        print(f"DEBUG: Length of self.base_url: {len(self.base_url)}")
        print(f"DEBUG: Hex representation of self.base_url: {[hex(ord(c)) for c in self.base_url]}")
        # -----------------------------

        self.api_key = settings.DISCOURSE_API_KEY
        self.api_username = settings.DISCOURSE_API_USERNAME
        self.headers = {
            'Api-Key': self.api_key,
            'Api-Username': self.api_username,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.verify_ssl = not settings.DEBUG

    def _make_request(self, method, path, data=None, params=None):
        # ... (your existing _make_request method content) ...
        url = f"{self.base_url}/{path}"
        try:
            response = requests.request(
                method,
                url,
                json=data,
                params=params,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Discourse API request failed: %s", e) # Use lazy formatting for logging
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Discourse API error response: %s", e.response.text) # Use lazy formatting for logging
            # Ensure this raises DiscourseAPIError
            raise DiscourseAPIError(f"Discourse API communication error: {e}")

    def create_user(self, user):
        """
        Creates a user in Discourse.
        Handles the case where Discourse API might not return user ID in the initial success response.
        """
        # IMPORTANT: This 'password' field must be the plaintext password.
        # Use the generate_random_password function defined above.
        generated_password = generate_random_password() # Correctly call the function
        active_user = True

        # Provide a placeholder email if the Django user's email is empty
        user_email = user.email if user.email else f"{user.username}@example.com"
        # --- MODIFICATION ENDS HERE ---

        data = {
            'username': user.username,
            'email': user_email,
            'name': user.get_full_name() or user.username,
            'password': generated_password, # <<< YOU MUST ENSURE THIS IS A REAL PLAINTEXT PASSWORD
            'active':active_user,
        }

        # Corrected endpoint based on your documentation
        endpoint = 'users.json'

        try:
            response = self._make_request('POST', endpoint, data=data)

            # Check if Discourse API reported overall success
            if response.get('success') is True:
                if 'id' in response:
                    discourse_user_id = response['id']
                    logger.info("Discourse user %s created with ID: %s", user.username, response['id']) # Use lazy formatting
                    return discourse_user_id 
                else:
                    logger.warning("Discourse user creation successful for %s but no ID returned in direct response. Full response: %s", user.username, response) # Use lazy formatting
                    return True 
            else:
                error_message = response.get('message', 'Discourse API reported an unknown error during user creation.')
                logger.error("Discourse user creation failed for %s: %s. Full response: %s", user.username, error_message, response) # Use lazy formatting
                raise DiscourseAPIError(f"Discourse user creation failed: {error_message}")

        except requests.exceptions.RequestException as e:
            logger.error("Discourse API request failed during creation for %s: %s", user.username, e)
            # Ensure this re-raises DiscourseAPIError
            raise DiscourseAPIError(f"Discourse API communication error during user creation: {e}")
        except Exception as e:
            logger.error("An unexpected error occurred during Discourse create_user for %s: %s", user.username, e)
            # Ensure this re-raises DiscourseAPIError
            raise DiscourseAPIError(f"Unexpected error during user creation: {e}")        

    def update_user(self, user):
        """
        Updates an existing user in Discourse.
        Requires the Django user to have a linked DiscourseProfile with a discourse_user_id.
        """
        try:
            # Attempt to get the DiscourseProfile and user ID
            profile = user.discourse_profile
            discourse_user_id = profile.discourse_user_id

            if not discourse_user_id:
                logger.warning("Discourse user ID is null for Django user %s. Cannot update.", user.username)
                return False # Indicate failure without erroring out

            data = {
                'email': user.email,
                'name': user.get_full_name() or user.username,
                # Passwords are not typically updated via general user update API for SSO users.
            }
            # Endpoint for updating a user by ID (based on your previous use)
            endpoint = f'admin/users/{discourse_user_id}.json' 
            
            # Make the API request
            response = self._make_request('PUT', endpoint, data=data)
            logger.info("Successfully updated Discourse user ID %s.", discourse_user_id)
            
            # Update last_synced_at timestamp if successful
            profile.last_synced_at = timezone.now()
            profile.save()
            
            return response # Return the API response on success

        except user._meta.model.discourse_profile.RelatedObjectDoesNotExist: # More specific exception for missing profile
            logger.warning("No DiscourseProfile found for Django user %s. Cannot update.", user.username)
            return False
        except requests.exceptions.RequestException as e: # Catch API request errors (e.g., 404, 500)
            logger.error("Discourse API request failed during update for %s (ID: %s): %s", user.username, discourse_user_id, e)
            raise # Re-raise for higher-level handling
        except Exception as e: # Catch any other unexpected errors
            logger.error("An unexpected error occurred during Discourse update_user for %s: %s", user.username, e)
            raise # Re-raise for higher-level handling

    def get_user_by_external_id(self, external_id):
        pass

    def delete_user(self, discourse_user_id, **kwargs):
        try:
            response = self.client.delete_user(
                discourse_user_id,
                block_email=kwargs.get('block_email', True),
                block_urls=kwargs.get('block_urls', True),
                delete_posts=kwargs.get('delete_posts', False)
            )
            logger.info(f"Successfully deleted Discourse user ID {discourse_user_id}.")
            return response
        except DiscourseClientError as e:
            logger.error(f"pydiscourse delete_user failed for ID {discourse_user_id}: {e.response.text if hasattr(e, 'response') else e}")
            raise DiscourseAPIError(f"Discourse API error during user deletion: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during pydiscourse delete_user for ID {discourse_user_id}: {e}")
            raise DiscourseAPIError(f"Unexpected error during user deletion: {e}")

    def get_sso_login_url(self, return_path='/'):
        """
        Generates the DiscourseConnect SSO login URL.
        NOTE: This is a simplified placeholder. Actual SSO payload generation
        is complex, involving nonce, external_id, email, username, etc.,
        base64 encoding, and HMAC-SHA256 signature.
        You would typically use a library like `discourse_sso` for this.
        """
        sso_secret = settings.DISCOURSE_SSO_SECRET
        # Placeholder for actual SSO payload and signature logic
        sso_payload_base64 = "YOUR_SSO_PAYLOAD_BASE64_ENCODED"
        signature = "YOUR_HMAC_SHA256_SIGNATURE"
        return f"{settings.DISCOURSE_SSO_LOGIN_URL}?sso={sso_payload_base64}&sig={signature}"
