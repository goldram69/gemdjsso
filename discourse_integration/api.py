# discourse_integration/api.py
import requests
import logging
from django.conf import settings
from django.contrib.auth import get_user_model # Import get_user_model to access its manager
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class DiscourseAPI:
    def __init__(self):
        self.base_url = settings.DISCOURSE_BASE_URL.rstrip('/')
        self.api_key = settings.DISCOURSE_API_KEY
        self.api_username = settings.DISCOURSE_API_USERNAME
        self.headers = {
            'Api-Key': self.api_key,
            'Api-Username': self.api_username,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        # Use verify_ssl based on DEBUG setting, allowing for self-signed certs in dev
        self.verify_ssl = not settings.DEBUG

    def _make_request(self, method, path, data=None, params=None):
        url = f"{self.base_url}/{path}"
        try:
            response = requests.request(
                method,
                url,
                json=data,
                params=params,
                headers=self.headers,
                verify=self.verify_ssl # Use the setting for verification
            )
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Discourse API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Discourse API response content: {e.response.text}")
            raise

    def create_user(self, user):
        """
        Creates a user in Discourse.
        Requires username, email, and a password (even if random for SSO-managed users).
        """
        # Correctly generate a random password using the User model's default manager
        random_password = get_user_model().objects.make_random_password()

        data = {
            'username': user.username,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'password': random_password, # Provide a random password for Discourse
            'active': True, # Mark user as active
            'approved': True, # Mark user as approved
            # 'external_id': user.id, # Highly recommended for linking Django user to Discourse
            # 'sso_true': True # Some APIs might need this to indicate SSO-managed, but usually implied by SSO
        }
        return self._make_request('POST', 'users', data=data)

    def update_user(self, user):
        """
        Updates an existing user in Discourse by username or external_id.
        """
        # For updates, it's best to use an external_id if you store it.
        # If not, you might need to query Discourse by email/username first to get their ID.
        # For simplicity here, we assume username is unique and directly usable for update endpoint.
        user_id_or_username = user.username

        data = {
            'email': user.email,
            'name': user.get_full_name() or user.username,
            # Passwords are not typically updated via general user update API for SSO users.
        }
        # Discourse's update user endpoint typically looks like PUT /u/{username} or /admin/users/{id}
        # If the direct /users/{username} PUT endpoint exists and works for your Discourse version:
        return self._make_request('PUT', f'users/{user_id_or_username}', data=data)


    def get_sso_login_url(self, return_path='/'):
        """
        Generates the Discourse SSO login URL.
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
