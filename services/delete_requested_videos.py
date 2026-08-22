import pickle
from googleapiclient.discovery import build

VIDEO_IDS = ["xx-ZlQLgH_M", "2H3kg8OGbLI"]
with open("token.pickle", "rb") as token:
    credentials = pickle.load(token)
youtube = build("youtube", "v3", credentials=credentials)
for video_id in VIDEO_IDS:
    youtube.videos().delete(id=video_id).execute()
    print(f"deleted {video_id}")
