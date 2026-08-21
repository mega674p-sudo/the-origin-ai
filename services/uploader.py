import os
import pickle
import sys
import google.oauth2.credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

def get_authenticated_service():
    credentials = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            client_secrets_file = '/home/ubuntu/.config/n8n/google_oauth_client.json'
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            flow.redirect_uri = 'https://8080-ixjtf3ox6s8fd9j3rygk1-bfd4cbc5.sg1.manus.computer/'
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            print(f'Please visit this URL to authorize: {auth_url}')
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            credentials = flow.credentials
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return build('youtube', 'v3', credentials=credentials)

def upload_video(youtube, file_path, title, description, category_id='27', privacy_status='public'):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': category_id,
            'tags': ['Shorts', 'Science', 'Mystery', 'AI']
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f'Uploaded {int(status.progress() * 100)}%')
    
    print(f'Video ID {response["id"]} was successfully uploaded.')
    return response['id']

if __name__ == '__main__':
    youtube = get_authenticated_service()
    
    # Arguments: script.py [video_path] [title] [description]
    video_path = sys.argv[1] if len(sys.argv) > 1 else '/home/ubuntu/the-origin-ai/output_dm/final_video_v2.mp4'
    title = sys.argv[2] if len(sys.argv) > 2 else 'ความลับจักรวาล #Shorts #Science'
    description = sys.argv[3] if len(sys.argv) > 3 else 'สำรวจความลึกลับของจักรวาลในสไตล์ Cinematic Science'
    
    upload_video(youtube, video_path, title, description)
