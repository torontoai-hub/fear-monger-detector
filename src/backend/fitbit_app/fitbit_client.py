"""
fitbit_client.py

Handles communication with the Fitbit Web API, including:
- Loading and refreshing access tokens
- Making authenticated API requests
- Storing new tokens on refresh
"""

import json
import time
import os
import requests
import base64
from .config import TOKEN_FILE, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
from .fitbit_auth import authenticate


# ============================================================
# Function: refresh_token
# ============================================================
def refresh_token(refresh_token):
    """
    Request a new access token using an existing (valid) refresh token.

    Fitbit's OAuth2 flow uses one-time-use refresh tokens.
    When you refresh, Fitbit issues:
        - A new access_token (short-lived)
        - A new refresh_token (use this next time)
    The old refresh token becomes invalid immediately.
    """

    token_url = "https://api.fitbit.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    # Fitbit requires HTTP Basic Auth with client_id:client_secret
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Send POST request to Fitbit token endpoint
    response = requests.post(token_url, data=data, headers=headers)

    # If successful, Fitbit returns new access & refresh tokens
    if response.ok:
        tokens = response.json()
        tokens["timestamp"] = time.time() # store refresh time for expiry tracking

        # Save new token info to local file (replaces old tokens)
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)

        print("New refresh token starts with:", tokens["refresh_token"][:8])
        return tokens["access_token"]# Return full token dictionary (not just access token)
    
    # If refresh fails (e.g., invalid_grant), raise exception with Fitbit's message
    else:
        raise Exception(f"Failed to refresh token: {response.text}")


# ============================================================
# Function: get_token
# ============================================================
def get_token():
    """
    Retrieve a valid access token for Fitbit API calls.

    - If token file exists:
        - Load tokens
        - Check expiry using timestamp + expires_in
        - Refresh if expired and update local file
    - If no token file:
        - Trigger manual authentication flow
    """

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            tokens = json.load(f)

        # Check if current access token is expired (minus 60s safety margin)
        if time.time() > tokens.get("timestamp", 0) + tokens.get("expires_in", 0) - 60:
            return refresh_token(tokens["refresh_token"])
        
        # Return the current valid access token
        return tokens["access_token"]

    # If first-time use, call authenticate() to start OAuth flow
    return authenticate()


# ============================================================
# Function: fetch_fitbit_data
# ============================================================
def fetch_fitbit_data(endpoint):
    """
    Fetch JSON data from a given Fitbit API endpoint.

    Example:
        endpoint = "/1/user/-/activities/heart/date/2025-10-10/1d/1sec.json"
        response = fetch_fitbit_data(endpoint)

    This function:
        - Retrieves a valid token via get_token()
        - Adds the Bearer token to headers
        - Makes a GET request to Fitbit API
        - Returns JSON response data
    """
    
    # Ensure we have a valid access token
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Build full Fitbit API URL
    url = f"https://api.fitbit.com{endpoint}"

    # Make request
    r = requests.get(url, headers=headers)
    
    return r.json()
