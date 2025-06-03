# discourse_integration/tests.py
import json
import requests
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.utils import timezone # Import timezone for datetime comparisons
from unittest.mock import patch, MagicMock

# Import the API class and custom exception
from discourse_integration.api import DiscourseAPI, generate_random_password, DiscourseAPIError
# Import the signal handler
from discourse_integration.signals import user_post_save_handler
# Import the DiscourseProfile model
from discourse_integration.models import DiscourseProfile # Import DiscourseProfile

# Get the Django User model
User = get_user_model()

@override_settings(
    DISCOURSE_BASE_URL='https://testdiscourse.com/',
    DISCOURSE_API_KEY='test_api_key',
    DISCOURSE_API_USERNAME='test_api_username',
    DEBUG=True
)
class DiscourseAPITests(TestCase):
    """
    Unit tests for the DiscourseAPI class.
    Mocks external HTTP requests to Discourse.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disconnect the signal handler during the entire test class execution
        # to prevent it from making real Discourse API calls during setUp or test execution.
        post_save.disconnect(user_post_save_handler, sender=User)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Reconnect the signal handler after the test class execution is complete.
        post_save.connect(user_post_save_handler, sender=User)

    def setUp(self):
        """
        Set up common test data before each test method runs.
        The post_save signal for User is disconnected for this test class.
        """
        # Create a unique suffix for usernames and emails for each test method
        # This ensures that even if IDs reset, the user and profile are truly unique per test.
        unique_suffix = self._testMethodName # Uses the name of the test method currently running

        self.test_user = User.objects.create_user(
            username=f'testuser_{unique_suffix}',
            email=f'test_{unique_suffix}@example.com',
            password='securepassword123',
            first_name='Test',
            last_name='User'
        )
        
        # Use get_or_create to ensure a DiscourseProfile exists for this specific test_user
        # This handles cases where a profile might already exist due to signals (if not fully disconnected)
        # or other setup quirks, preventing unique constraint violations.
        self.discourse_profile, created = DiscourseProfile.objects.get_or_create(
            user=self.test_user,
            defaults={
                'discourse_user_id': 12345, # A dummy Discourse ID for this user
                'last_synced_at': timezone.now() - timezone.timedelta(days=1)
            }
        )
        # If the profile already existed (e.g., from an undisconnected signal during user creation in setUp),
        # ensure its discourse_user_id and last_synced_at are set for the test context.
        if not created:
            self.discourse_profile.discourse_user_id = 12345
            self.discourse_profile.last_synced_at = timezone.now() - timezone.timedelta(days=1)
            self.discourse_profile.save() # Save to apply changes if it wasn't created

        self.user_no_email = User.objects.create_user(
            username=f'noemailuser_{unique_suffix}',
            email='',
            password='anotherpassword',
            first_name='No',
            last_name='Email'
        )
        # This user does not need a DiscourseProfile for its specific test case.
        
        self.superuser = User.objects.create_superuser(
            username=f'adminuser_{unique_suffix}',
            email=f'admin_{unique_suffix}@example.com',
            password='adminpassword'
        )

    # --- Existing create_user tests (unchanged) ---
    @patch('discourse_integration.api.requests.request')
    def test_create_user_success(self, mock_requests_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True, "active": True, "user_id": 123, "id": 123,
            "username": "testuser", "email": "test@example.com", "message": "User created successfully."
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_request.return_value = mock_response

        api = DiscourseAPI()
        result = api.create_user(self.test_user)

        call_args, call_kwargs = mock_requests_request.call_args
        self.assertEqual(call_args[0], 'POST')
        self.assertEqual(call_args[1], 'https://testdiscourse.com/users.json')
        
        sent_json = call_kwargs['json']
        self.assertEqual(sent_json['username'], self.test_user.username)
        self.assertEqual(sent_json['email'], self.test_user.email)
        self.assertEqual(sent_json['name'], self.test_user.get_full_name())
        self.assertIsInstance(sent_json['password'], str)
        self.assertTrue(sent_json['active'])

        self.assertEqual(result, 123)

    @patch('discourse_integration.api.requests.request')
    def test_create_user_success_no_id_in_response(self, mock_requests_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True, "active": True, "message": "Your account is activated and ready to use."
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_request.return_value = mock_response

        api = DiscourseAPI()
        result = api.create_user(self.test_user)

        call_args, call_kwargs = mock_requests_request.call_args
        self.assertEqual(call_args[0], 'POST')
        self.assertEqual(call_kwargs['json']['username'], self.test_user.username)
        
        self.assertTrue(result)

    @patch('discourse_integration.api.requests.request')
    def test_create_user_email_fallback(self, mock_requests_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "active": True, "id": 124}
        mock_response.raise_for_status.return_value = None
        mock_requests_request.return_value = mock_response

        api = DiscourseAPI()
        api.create_user(self.user_no_email)

        call_kwargs = mock_requests_request.call_args[1]
        sent_json = call_kwargs['json']
        self.assertEqual(sent_json['email'], 'noemailuser@example.com')
        self.assertEqual(sent_json['username'], 'noemailuser')

    @patch('discourse_integration.api.requests.request')
    def test_create_user_api_failure(self, mock_requests_request):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"errors": ["Username already taken"]}
        mock_requests_request.return_value = mock_response
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("400 Client Error: Bad Request")

        api = DiscourseAPI()
        
        with self.assertRaises(DiscourseAPIError) as cm:
            api.create_user(self.test_user)
        
        self.assertIsInstance(cm.exception, DiscourseAPIError)
        self.assertIn("Discourse API communication error", str(cm.exception))

    def test_generate_random_password(self):
        password = generate_random_password()
        self.assertIsInstance(password, str)
        self.assertEqual(len(password), 12)
        self.assertNotEqual(generate_random_password(), generate_random_password())
    # --- End existing create_user tests ---


    # --- New update_user tests ---
    @patch('discourse_integration.api.requests.request')
    def test_update_user_success(self, mock_requests_request):
        """
        Tests successful user update in Discourse.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": "OK", "user": {"id": self.discourse_profile.discourse_user_id, "username": "updateduser"}
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_request.return_value = mock_response

        api = DiscourseAPI()

        # Simulate updating the Django user's name and email
        self.test_user.first_name = 'Updated'
        self.test_user.last_name = 'Name'
        self.test_user.email = 'updated@example.com'
        self.test_user.save() # This save won't trigger signal due to disconnect

        # Ensure last_synced_at is older before calling update
        old_sync_time = self.discourse_profile.last_synced_at
        
        # Call the method we are testing
        result = api.update_user(self.test_user)

        # Assert that requests.request was called correctly
        expected_url = f'https://testdiscourse.com/admin/users/{self.discourse_profile.discourse_user_id}.json'
        call_args, call_kwargs = mock_requests_request.call_args
        self.assertEqual(call_args[0], 'PUT') # Method
        self.assertEqual(call_args[1], expected_url) # URL
        
        # Check the JSON payload sent to Discourse
        sent_json = call_kwargs['json']
        self.assertEqual(sent_json['name'], self.test_user.get_full_name())
        self.assertEqual(sent_json['email'], self.test_user.email)

        # Assert the return value from update_user
        self.assertEqual(result, mock_response.json.return_value)

        # Refresh the profile from DB and check last_synced_at was updated
        self.discourse_profile.refresh_from_db()
        self.assertGreater(self.discourse_profile.last_synced_at, old_sync_time)
        self.assertLessEqual(self.discourse_profile.last_synced_at, timezone.now())

    @patch('discourse_integration.api.requests.request')
    def test_update_user_no_discourse_profile(self, mock_requests_request):
        """
        Tests that update_user returns False if no DiscourseProfile is found.
        """
        # Create a user WITHOUT a DiscourseProfile
        # Use a unique suffix for this user too
        user_without_profile = User.objects.create_user(username=f'noprofile_{self._testMethodName}', password='pw')
        
        api = DiscourseAPI()
        result = api.update_user(user_without_profile)

        # Assert that no API request was made
        mock_requests_request.assert_not_called()
        # Assert that it returns False as per api.py logic
        self.assertFalse(result)

    @patch('discourse_integration.api.requests.request')
    def test_update_user_null_discourse_id(self, mock_requests_request):
        """
        Tests that update_user returns False if DiscourseProfile has a null ID.
        """
        # Set the existing test user's discourse_user_id to None
        self.discourse_profile.discourse_user_id = None
        self.discourse_profile.save()

        api = DiscourseAPI()
        result = api.update_user(self.test_user)

        # Assert that no API request was made
        mock_requests_request.assert_not_called()
        # Assert that it returns False as per api.py logic
        self.assertFalse(result)

    @patch('discourse_integration.api.requests.request')
    def test_update_user_api_failure(self, mock_requests_request):
        """
        Tests that DiscourseAPIError is raised on HTTP error during update.
        """
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"errors": ["Internal Server Error"]}
        mock_requests_request.return_value = mock_response
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("500 Server Error")

        api = DiscourseAPI()
        
        with self.assertRaises(DiscourseAPIError) as cm:
            api.update_user(self.test_user)
        
        self.assertIsInstance(cm.exception, DiscourseAPIError)
        self.assertIn("Discourse API communication error", str(cm.exception))

    # --- New delete_user tests ---
    @patch('discourse_integration.api.requests.request')
    def test_delete_user_success(self, mock_requests_request):
        """
        Tests successful user deletion in Discourse.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": "OK"}
        mock_response.raise_for_status.return_value = None
        mock_requests_request.return_value = mock_response

        api = DiscourseAPI()
        
        # Call the method we are testing
        result = api.delete_user(self.discourse_profile.discourse_user_id)

        # Assert that requests.request was called correctly
        expected_url = f'https://testdiscourse.com/admin/users/{self.discourse_profile.discourse_user_id}.json'
        call_args, call_kwargs = mock_requests_request.call_args
        self.assertEqual(call_args[0], 'DELETE') # Method
        self.assertEqual(call_args[1], expected_url) # URL
        
        # Check default parameters sent
        self.assertTrue(call_kwargs['params']['block_email'])
        self.assertTrue(call_kwargs['params']['block_urls'])
        self.assertFalse(call_kwargs['params']['delete_posts'])

        # Assert the return value
        self.assertEqual(result, mock_response.json.return_value)

    @patch('discourse_integration.api.requests.request')
    def test_delete_user_api_failure(self, mock_requests_request):
        """
        Tests that DiscourseAPIError is raised on HTTP error during delete.
        """
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"errors": ["User not found"]}
        mock_requests_request.return_value = mock_response
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("404 Not Found")

        api = DiscourseAPI()
        
        with self.assertRaises(DiscourseAPIError) as cm:
            api.delete_user(self.discourse_profile.discourse_user_id)
        
        self.assertIsInstance(cm.exception, DiscourseAPIError)
        self.assertIn("Discourse API error during user deletion", str(cm.exception))


