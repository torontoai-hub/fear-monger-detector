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

PORT = 8090

def generate_auth_url():
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "expires_in": "604800"
    }
    return "https://www.fitbit.com/oauth2/authorize?" + urllib.parse.urlencode(params)

class FitbitAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        code = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("code")
        if code:
            self.server.auth_code = code[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Fitbit authentication successful!</h1>"
                             b"You can close this window.</body></html>")
        else:
            self.send_response(400)
            self.end_headers()

def get_auth_code():
    url = generate_auth_url()
    print("Opening browser for Fitbit authorization...")
    webbrowser.open(url)
    server = HTTPServer(("localhost", PORT), FitbitAuthHandler)
    server.handle_request()
    return getattr(server, "auth_code", None)

def authenticate():
    auth_code = get_auth_code()
    if not auth_code:
        raise Exception("No authorization code obtained.")

    token_url = "https://api.fitbit.com/oauth2/token"
    data = {
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": auth_code
    }
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(token_url, data=data, headers=headers)
    if response.ok:
        tokens = response.json()
        tokens["timestamp"] = time.time()
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)
        print("Tokens saved to", TOKEN_FILE)
        return tokens["access_token"]
    else:
        raise Exception(f"Failed to authenticate: {response.text}")

if __name__ == "__main__":
    authenticate()
