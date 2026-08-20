import os
import pickle
import google.oauth2.credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    credentials = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            client_secrets_file = '/home/ubuntu/.config/n8n/google_oauth_client.json'
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            flow.redirect_uri = 'https://8080-ixjtf3ox6s8fd9j3rygk1-bfd4cbc5.sg1.manus.computer/'
            # Manual flow for sandbox environment
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            print(f'Please visit this URL to authorize: {auth_url}')
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            credentials = flow.credentials
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return build('youtube', 'v3', credentials=credentials)

def upload_video(youtube, file_path, title, description, category_id='27', privacy_status='public'):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': category_id,
            'tags': ['Shorts', 'Science', 'BlackHole', 'AI']
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
    video_path = '/home/ubuntu/the-origin-ai/output_dm/final_video_v2.mp4'
    title = 'ความลับของสสารมืด: สิ่งที่มองไม่เห็นแต่ครองจักรวาล #Shorts #Science #DarkMatter'
    description = 'สำรวจความลึกลับของสสารมืดที่คอยยึดเหนี่ยวจักรวาลนี้ไว้ในสไตล์ Cinematic Science'
    upload_video(youtube, video_path, title, description)
