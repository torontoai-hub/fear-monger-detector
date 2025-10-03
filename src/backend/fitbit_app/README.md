# Fitbit Data Fetcher

A complete Fitbit OAuth 2.0 authentication flow to programmatically fetch Fitbit data (heart rate, activity, sleep, etc.).

---

## Table of Contents

- [Project Structure](#project-structure)  
- [Getting Started](#getting-started)  
  - [Step 1 — Register Your Fitbit App](#step-1-—-register-your-fitbit-app)  
  - [Step 2 — Configure the App](#step-2-—-configure-the-app)  
  - [Step 3 — Authenticate with Fitbit](#step-3-—-authenticate-with-fitbit)  
  - [Step 4 — Fetch Fitbit Data](#step-4-—-fetch-fitbit-data)  
  - [Step 5 — Automatic Token Refresh](#step-5-—-automatic-token-refresh)  
- [Notes](#notes)  
- [Resources](#resources)  

---

## Project Structure

```

fitbit_project/
│
├── config.py             # Fitbit app configuration (CLIENT_ID, CLIENT_SECRET, etc.)
├── fitbit_auth.py        # Handles OAuth authorization & token exchange
├── fitbit_client.py      # Fetches Fitbit data using stored tokens
├── fitbit_tokens.json    # Stores access_token & refresh_token
├── main.py               # Main script to run the app
└── README.md             # Project documentation

```

---

## Getting Started

### Step 1 — Register Your Fitbit App

1. Go to [Fitbit Developer Portal](https://dev.fitbit.com/apps).
2. Create a new app.
3. Copy your:
   - `CLIENT_ID`
   - `CLIENT_SECRET`
4. Set a **Redirect URI** (e.g., `http://localhost:8080` for development).
5. Set your **Scopes** (e.g., `activity heartrate sleep`).

---

### Step 2 — Configure the App

Edit `config.py` with your Fitbit app credentials:

```python
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:8080"
SCOPES = "activity heartrate sleep"
TOKEN_FILE = "fitbit_tokens.json"
```
---

### Step 3 — Authenticate with Fitbit

Run the authentication script to:

* Open a browser window for Fitbit login
* Capture the authorization code
* Exchange it for tokens
* Store tokens locally

```bash
python fitbit_auth.py
```

---

### Step 4 — Fetch Fitbit Data

Use stored tokens to call Fitbit APIs:

```bash
python main.py
```

Example usage:

```python
from fitbit_client import fetch_fitbit_data

data = fetch_fitbit_data("/1/user/-/activities/heart/date/today/1d.json")
print(data)
```

---

### Step 5 — Automatic Token Refresh

The app automatically refreshes tokens when expired, using the stored `refresh_token` in `fitbit_tokens.json`.

---

## Notes

* Fitbit authorization codes expire quickly (30 seconds). Run `fitbit_auth.py` immediately after logging in.
* Store your credentials securely. **Never commit them to public repositories.**
* Fitbit API documentation: [Fitbit Web API Reference](https://dev.fitbit.com/build/reference/web-api/)

---

## Resources

* [Fitbit Developer Portal](https://dev.fitbit.com/)
* [Fitbit OAuth 2.0 Guide](https://dev.fitbit.com/build/reference/web-api/oauth2/)
* [Fitbit API Endpoints](https://dev.fitbit.com/build/reference/web-api/)

---

