import os
import pickle
from googleapiclient.discovery import build

TOKEN = "/home/ubuntu/the-origin-ai/token.pickle"
with open(TOKEN, "rb") as f:
    credentials = pickle.load(f)

youtube = build("youtube", "v3", credentials=credentials)
channel = youtube.channels().list(part="contentDetails", mine=True).execute()["items"][0]
uploads_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
playlist = youtube.playlistItems().list(
    part="snippet,contentDetails",
    playlistId=uploads_id,
    maxResults=10,
).execute()
for item in playlist.get("items", []):
    snippet = item["snippet"]
    print(f'{item["contentDetails"]["videoId"]}\t{snippet.get("publishedAt")}\t{snippet.get("title")}')
        
if not playlist.get("items"):
    print("NO_UPLOADS")
        
__import__("sys").exit(0)
