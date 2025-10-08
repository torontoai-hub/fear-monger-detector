# config.py

import os
from dotenv import load_dotenv

# Load .env file content into environment variables
load_dotenv()

TOKEN_FILE = os.getenv("TOKEN_FILE", "fitbit_tokens.json")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPES = os.getenv("SCOPES")
FITBIT_HEART_ENDPOINT = "/1/user/-/activities/heart/date/{date}/1d/1min.json"
DATE_FORMAT = "%Y-%m-%d"
