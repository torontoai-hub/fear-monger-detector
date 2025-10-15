# fitbit_auth.py
import base64
import json
import os
import requests
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import time
from .config import TOKEN_FILE, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES

# Local port used by the temporary HTTP server to capture Fitbit's OAuth redirect
PORT = 8090

def generate_auth_url():
    """
    Builds the Fitbit OAuth 2.0 authorization URL with the required query parameters.
    The user will be redirected here to grant access to their Fitbit data.
    """

    params = {
        "response_type": "code",          # Fitbit returns an authorization code
        "client_id": CLIENT_ID,           # Fitbit app's client ID
        "redirect_uri": REDIRECT_URI,     # Must match the one set in your Fitbit app settings
        "scope": SCOPES,                  # Data access scopes (e.g., heartrate, activity)
        "expires_in": "604800"            # Optional: requested token validity in seconds (7 days)
    }

    return "https://www.fitbit.com/oauth2/authorize?" + urllib.parse.urlencode(params)

class FitbitAuthHandler(BaseHTTPRequestHandler):
    """
    A simple HTTP request handler that captures the authorization code
    when Fitbit redirects back to the redirect URI.
    """

    def do_GET(self):
        # Extract the 'code' query parameter from the redirect URL
        code = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("code")

        if code:
            # Store the code on the server instance for retrieval
            self.server.auth_code = code[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Fitbit authentication successful!</h1>"
                             b"You can close this window.</body></html>")
        else:
            # If no code parameter is present, return a 400 response
            self.send_response(400)
            self.end_headers()

def get_auth_code():
    """
    Opens the Fitbit authorization page in a browser and waits for the redirect
    containing the authorization code. This is a one-time step to obtain tokens.
    """

    url = generate_auth_url()
    print("Opening browser for Fitbit authorization...")
    webbrowser.open(url)
    server = HTTPServer(("localhost", PORT), FitbitAuthHandler)

    # Handles a single request (Fitbit’s redirect with the code)
    server.handle_request()

    # Retrieve the captured authorization code
    return getattr(server, "auth_code", None)

def authenticate():
    """
    Performs the full OAuth 2.0 authentication flow:
    1. Opens Fitbit's authorization page for user consent.
    2. Captures the authorization code after redirect.
    3. Exchanges the code for access and refresh tokens.
    4. Saves tokens locally to TOKEN_FILE for reuse.
    """

    auth_code = get_auth_code()
    if not auth_code:
        raise Exception("No authorization code obtained.")

    # Fitbit token exchange endpoint
    token_url = "https://api.fitbit.com/oauth2/token"
    data = {
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": auth_code
    }

     # Basic Auth header: Base64 encoded "client_id:client_secret"   
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Exchange the authorization code for tokens
    response = requests.post(token_url, data=data, headers=headers)
    if response.ok:
        tokens = response.json()
        # Add timestamp for later refresh checks
        tokens["timestamp"] = time.time()
        # Save tokens locally as JSON for reuse by other scripts

        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)
        print("Tokens saved to", TOKEN_FILE)

        # Return the access token for immediate use if needed
        return tokens["access_token"]
    else:
        raise Exception(f"Failed to authenticate: {response.text}")

if __name__ == "__main__":
    # Run the full authentication flow if the script is executed directly
    authenticate()
