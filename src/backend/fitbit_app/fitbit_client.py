# fitbit_client.py
import json
import time
import os
import requests
import base64
import config
from fitbit_auth import authenticate

def refresh_token(refresh_token):
    token_url = "https://api.fitbit.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    auth_header = base64.b64encode(f"{config.CLIENT_ID}:{config.CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(token_url, data=data, headers=headers)
    if response.ok:
        tokens = response.json()
        tokens["timestamp"] = time.time()
        with open(config.TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)
        print("Token refreshed.")
        return tokens["access_token"]
    else:
        raise Exception(f"Failed to refresh token: {response.text}")

def get_token():
    if os.path.exists(config.TOKEN_FILE):
        with open(config.TOKEN_FILE) as f:
            tokens = json.load(f)

        if time.time() > tokens.get("timestamp", 0) + tokens.get("expires_in", 0) - 60:
            return refresh_token(tokens["refresh_token"])
        return tokens["access_token"]

    return authenticate()

def fetch_fitbit_data(endpoint):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.fitbit.com{endpoint}"
    r = requests.get(url, headers=headers)
    return r.json()
