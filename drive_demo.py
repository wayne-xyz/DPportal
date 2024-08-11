from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os.path
import pickle


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

EsriWorldImagery_jpg_dir = "/My Drive/Dumpsite_Images/Images/EsriWorldImagery_jpg/"



def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'google_drive_credentials.json',
                SCOPES
            )
            if os.getenv('ENVIRONMENT') == 'production':
                creds = flow.run_console()
            else:
                os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
                creds = flow.run_local_server(port=8080)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def search_files(service, query):
    results = []
    page_token = None
    while True:
        response = service.files().list(q=query,
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name, mimeType)',
                                        pageToken=page_token).execute()
        results.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return results

def main():
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)

    # Print directories in the root folder
    print("Directories in root folder:")
    root_directories = search_files(service, "mimeType='application/vnd.google-apps.folder' and 'root' in parents")
    for directory in root_directories:
        print(f"Name: {directory['name']}, ID: {directory['id']}")





if __name__ == '__main__':
    main()