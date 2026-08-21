import os
import pickle
import sys
from googleapiclient.discovery import build

TOKEN = "/home/ubuntu/the-origin-ai/token.pickle"

def delete_video(video_id):
    if not os.path.exists(TOKEN):
        print("No token found.")
        return
        
    with open(TOKEN, "rb") as f:
        credentials = pickle.load(f)
    
    youtube = build("youtube", "v3", credentials=credentials)
    
    try:
        youtube.videos().delete(id=video_id).execute()
        print(f"Video ID {video_id} has been deleted.")
    except Exception as e:
        print(f"Failed to delete video: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        delete_video(sys.argv[1])
    else:
        print("Please provide a Video ID.")
