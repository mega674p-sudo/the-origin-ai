import pickle
from googleapiclient.discovery import build

VIDEO_IDS = ["xx-ZlQLgH_M", "2H3kg8OGbLI"]
with open("token.pickle", "rb") as token:
    credentials = pickle.load(token)
youtube = build("youtube", "v3", credentials=credentials)
response = youtube.videos().list(part="snippet,status", id=",".join(VIDEO_IDS)).execute()
for item in response.get("items", []):
    snippet = item["snippet"]
    status = item["status"]
    print({
        "id": item["id"],
        "title": snippet.get("title"),
        "channel_id": snippet.get("channelId"),
        "published_at": snippet.get("publishedAt"),
        "privacy": status.get("privacyStatus"),
        "upload_status": status.get("uploadStatus"),
    })
missing = sorted(set(VIDEO_IDS) - {item["id"] for item in response.get("items", [])})
print({"missing_or_inaccessible": missing})
owned = youtube.channels().list(part="id", mine=True).execute()
print({"authenticated_channel_id": owned["items"][0]["id"] if owned.get("items") else None})
