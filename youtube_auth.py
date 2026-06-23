"""
youtube_auth.py
---------------
ONE-TIME LOCAL SCRIPT — Run this on your computer to authorize YouTube uploads.
It will open a browser, ask you to log in to Amy's YouTube/Google account,
then save a token file with the refresh token you'll add to GitHub Secrets.

SETUP (do this once):
  1. Go to https://console.cloud.google.com
  2. Create a new project (or select existing)
  3. Enable "YouTube Data API v3"
  4. Go to APIs & Services → Credentials
  5. Create Credentials → OAuth 2.0 Client IDs → Desktop app
  6. Download the JSON → rename it "youtube_client_secrets.json"
  7. Put youtube_client_secrets.json in this folder (Amy Light/)
  8. Run: py youtube_auth.py
  9. Complete the browser login
  10. Copy the values printed to your GitHub Secrets:
      - YOUTUBE_CLIENT_ID
      - YOUTUBE_CLIENT_SECRET
      - YOUTUBE_REFRESH_TOKEN

Install requirements first:
  pip install google-auth-oauthlib
"""
import json, os, sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import google.oauth2.credentials
except ImportError:
    print("Installing google-auth-oauthlib...")
    os.system("pip install google-auth-oauthlib --break-system-packages 2>/dev/null || pip install google-auth-oauthlib")
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import google.oauth2.credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SECRETS_FILE = "youtube_client_secrets.json"
TOKEN_FILE   = "youtube_token.json"

if not os.path.exists(SECRETS_FILE):
    print(f"""
ERROR: '{SECRETS_FILE}' not found!

Steps to fix:
  1. Go to https://console.cloud.google.com
  2. Create project → Enable "YouTube Data API v3"
  3. APIs & Services → Credentials → Create OAuth 2.0 Client ID → Desktop app
  4. Download JSON → rename to 'youtube_client_secrets.json'
  5. Put it in: {os.getcwd()}
  6. Run this script again
""")
    sys.exit(1)

print("Opening browser for YouTube authorization...")
print("Log in as Amy's Google account that owns the YouTube channel.\n")

flow = InstalledAppFlow.from_client_secrets_file(SECRETS_FILE, SCOPES)
creds = flow.run_local_server(port=0)

# Save token
token_data = {
    "token":         creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri":     creds.token_uri,
    "client_id":     creds.client_id,
    "client_secret": creds.client_secret,
    "scopes":        list(creds.scopes),
}
with open(TOKEN_FILE, "w") as f:
    json.dump(token_data, f, indent=2)

# Load client secrets to display client_id and client_secret
with open(SECRETS_FILE) as f:
    secrets = json.load(f)
client_info = secrets.get("installed") or secrets.get("web", {})

print(f"""
✓ Authorization successful!

Copy these 3 values to GitHub Secrets (Settings → Secrets → Actions):

  YOUTUBE_CLIENT_ID     = {client_info.get('client_id', creds.client_id)}
  YOUTUBE_CLIENT_SECRET = {client_info.get('client_secret', creds.client_secret)}
  YOUTUBE_REFRESH_TOKEN = {creds.refresh_token}

Also saved to: {TOKEN_FILE} (keep this file private — DO NOT commit it)
""")
