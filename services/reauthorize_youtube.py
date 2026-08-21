import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube"]
CLIENT_SECRETS = "/home/ubuntu/.config/n8n/google_oauth_client.json"
TOKEN_PATH = "/home/ubuntu/the-origin-ai/token.pickle"

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
flow.redirect_uri = "https://8080-ixjtf3ox6s8fd9j3rygk1-bfd4cbc5.sg1.manus.computer/"
auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
print("AUTH_URL=" + auth_url, flush=True)
code = input("AUTH_CODE=").strip()
flow.fetch_token(code=code)
with open(TOKEN_PATH, "wb") as token:
    pickle.dump(flow.credentials, token)
print("REAUTHORIZED", flush=True)
