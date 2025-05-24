# discourse_integration/views.py

import base64
import hashlib
import hmac
import urllib.parse
import os
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required # Require login to initiate SSO

User = get_user_model()

@login_required # Only logged-in Django users can initiate SSO
def discourse_sso_login(request):
    """
    Initiates the DiscourseConnect SSO process for a logged-in Django user.
    """
    # Ensure the user is not a Django admin
    if request.user.is_staff or request.user.is_superuser:
        # Optionally redirect admins to a different page or show an error
        return HttpResponseBadRequest("Admin users cannot use this SSO flow.")

    nonce = get_random_string(32)
    # Store the nonce and the user ID in the session to verify the callback
    request.session['discourse_sso_nonce'] = nonce
    request.session['discourse_sso_user_id'] = request.user.id

    # Construct the payload with user information from Django
    payload = {
        'nonce': nonce,
        'return_sso_url': settings.DISCOURSE_SSO_CALLBACK_URL,
        'email': request.user.email,
        'external_id': str(request.user.id), # Use Django user ID as external_id
        'username': request.user.username,
        'name': request.user.get_full_name() or request.user.username, # Provide a name if available
        # Add other parameters if needed, e.g., 'avatar_url', 'about_me', 'website'
        # 'require_activation': 'true' if user.is_active else 'false', # Example: if Django handles activation
        # 'suppress_welcome_message': 'true', # To prevent Discourse welcome emails
    }

    # Encode the payload into a query string
    query_string = urllib.parse.urlencode(payload)

    # Base64 encode the query string
    sso_payload = base64.b64encode(query_string.encode('utf-8')).decode('utf-8')

    # Calculate the HMAC-SHA256 signature
    signature = hmac.new(
        settings.DISCOURSE_SSO_SECRET.encode('utf-8'),
        sso_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Construct the redirect URL
    redirect_url = f"{settings.DISCOURSE_SSO_LOGIN_URL}?sso={urllib.parse.quote_plus(sso_payload)}&sig={signature}"

    return redirect(redirect_url)

@csrf_exempt # Necessary as Discourse posts to this URL
def discourse_sso_callback(request):
    """
    Handles the callback from Discourse after SSO.
    Validates the payload and ensures the Django user is logged in.
    """
    sso_payload = request.POST.get('sso')
    signature = request.POST.get('sig')

    if not sso_payload or not signature:
        return HttpResponseBadRequest("Missing SSO payload or signature.")

    # Verify the signature
    expected_signature = hmac.new(
        settings.DISCOURSE_SSO_SECRET.encode('utf-8'),
        sso_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        # Log suspicious activity
        print(f"SSO Signature mismatch: Received={signature}, Expected={expected_signature}")
        return HttpResponseBadRequest("Invalid SSO signature.")

    try:
        # Decode and parse the payload
        decoded_payload = base64.b64decode(sso_payload).decode('utf-8')
        payload_params = urllib.parse.parse_qs(decoded_payload)

        nonce = payload_params.get('nonce', [None])[0]
        external_id = payload_params.get('external_id', [None])[0] # This should be the Django user ID
        email = payload_params.get('email', [None])[0]
        # Retrieve other parameters, but Django is the source of truth

        # Verify the nonce against the one stored in the session
        # Note: The nonce verification here is primarily to confirm the request originated from
        # a Django-initiated SSO flow. The actual user linking/auth is based on Django's session.
        stored_nonce = request.session.pop('discourse_sso_nonce', None)
        stored_user_id = request.session.pop('discourse_sso_user_id', None)

        if not stored_nonce or nonce != stored_nonce or not stored_user_id or external_id != str(stored_user_id):
             # This could indicate a replay attack or an issue with the session/linking
             print(f"SSO Nonce/User ID mismatch: Stored Nonce={stored_nonce}, Received Nonce={nonce}, Stored User ID={stored_user_id}, Received External ID={external_id}")
             return HttpResponseBadRequest("Invalid or expired SSO request or user mismatch.")

        # At this point, we have a validated SSO callback for a specific Django user.
        # Ensure the user is logged in. If not, log them in based on the stored user ID.
        if not request.user.is_authenticated or request.user.id != stored_user_id:
            try:
                user = User.objects.get(id=stored_user_id)
                # Note: We are logging in based on the Django user ID stored in the session,
                # not based on the Discourse payload data, as Django is the source of truth.
                login(request, user)
            except User.DoesNotExist:
                 print(f"Django user with ID {stored_user_id} not found during SSO callback.")
                 return HttpResponseBadRequest("User not found.")

        # Redirect the user to the appropriate page after the SSO handshake is complete.
        # This could be the homepage, a specific forum page, or the page they were trying to access.
        # You might store the redirect URL in the session in the discourse_sso_login view.
        redirect_url_after_sso = request.session.pop('redirect_url_after_sso', settings.LOGIN_REDIRECT_URL)
        return redirect(redirect_url_after_sso)

    except Exception as e:
        # Log the error
        print(f"Error processing Discourse SSO callback: {e}")
        # Render an error page or redirect to an error URL
        # Consider a more user-friendly error page
        return HttpResponseBadRequest("An error occurred during SSO processing.")

@login_required
def discourse_forum_link(request):
    """
    Redirects the logged-in user to the Discourse forum, triggering SSO if needed.
    """
    # Check if the user is already linked or if SSO is required.
    # For simplicity, we'll always initiate SSO for now.
    # In a more complex scenario, you might check if a DiscourseProfile exists and is linked.

    # Store the desired redirect URL after SSO completion (e.g., the Discourse base URL)
    request.session['redirect_url_after_sso'] = settings.DISCOURSE_BASE_URL

    # Redirect to the SSO login view which will handle the handshake
    return redirect('discourse:discourse_sso_login')

