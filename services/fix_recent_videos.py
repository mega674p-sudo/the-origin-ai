import os
import pickle
from googleapiclient.discovery import build

TOKEN = "/home/ubuntu/the-origin-ai/token.pickle"
if os.path.exists(TOKEN):
    with open(TOKEN, "rb") as f:
        credentials = pickle.load(f)
    youtube = build("youtube", "v3", credentials=credentials)
    
    # List recent uploads
    channel = youtube.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    uploads_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    playlist = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_id,
        maxResults=5,
    ).execute()
    
    for item in playlist.get("items", []):
        vid = item["contentDetails"]["videoId"]
        title = item["snippet"]["title"]
        print(f"Video ID: {vid} | Title: {title}")
else:
    print("No token found.")
