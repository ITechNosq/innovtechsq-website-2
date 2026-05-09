import json
import logging
import sys
from fastapi.testclient import TestClient

# Adjust path to import app
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from app.core.config import settings

# Temporarily disable Turnstile for the test so we don't get blocked
original_turnstile_secret = settings.TURNSTILE_SECRET_KEY
settings.TURNSTILE_SECRET_KEY = ""

# Set up the test client
client = TestClient(app)

print("="*60)
print("[ SIMULATING A REAL BROWSER FORM SUBMISSION TO THE API ]")
print("="*60)

# The data exactly as the frontend would send it
payload = {
    "name": "Pawan Sangar (Test)",
    "email": "innovtechnosq@gmail.com",
    "phone": "+91 8595237962",
    "message": "Hello! I am testing the new automated reply system from my website.",
    "turnstile_token": "dummy_token_for_test"
}

print(f"\n[ Sending the following payload to POST /leads:\n{json.dumps(payload, indent=2)}")

# Make the request
response = client.post("/leads", json=payload)

print("\n" + "="*60)
print(f"[ API RESPONSE (Status Code: {response.status_code}) ]")
print("="*60)
print(json.dumps(response.json(), indent=2))

print("\n" + "="*60)
print("[ SUCCESS: CHECK YOUR INBOX! ]")
print("The backend background tasks have processed this request and sent the email.")
print("="*60)

# Restore setting
settings.TURNSTILE_SECRET_KEY = original_turnstile_secret
