from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
import pickle
import time
import os.path


os.environ['GOOGLE_DRIVE_CREDENTIALS'] = 'google_drive_credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


# folder names
esri_world_imagery_folder_name="EsriWorldImagery_jpg"
sentinal_jpg_folder_name="sentinel_jpg"
nicfi_jpg_folder_name="nicfi_jpg"
sentinel_tif_folder_name="sentinel_tif_2024"
nicfi_folder_name="nicfi_tif_2024"

# target folders
target_folders=[esri_world_imagery_folder_name,sentinal_jpg_folder_name, nicfi_jpg_folder_name, sentinel_tif_folder_name, nicfi_folder_name]

# for the google drive api, 
ALLOWED_EMAIL='qinheyi@gmail.com' ,






# Get credentials from Google Drive :
# 1. Using the development environment, the token.pickle file will be used, upload the token.pickle file to Cloud
# 2. If the token is expired, local server will be used to get the token then upload the token.pickle file to Cloud
def get_credentials():

    # check the credentials.json exists
    SERVICE_ACCOUNT_FILE = 'google_drive_credentials.json'
    token_file = 'token.pickle'

    creds = None
    if os.getenv('GAE_ENV', '') == 'standard':
        # Use google_drive_credentials.json in production
        print("Current environment is production")
        
        # still using the token.pickle file in production
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        else:
            print("token.pickle not found")
        
        
    else:
        # Use local file storage in development
        print("Current environment is development")
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                print("Token refresh failed. Creating new token.")
                creds = None
        
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                'google_drive_credentials.json',
                SCOPES
            )
            if os.getenv('GAE_ENV', '') == 'standard':
                creds = flow.run_local_server(port=0)
            else:
                os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
                creds = flow.run_local_server(port=8080)
        
        if os.getenv('GAE_ENV', '') != 'standard':
            # Only save to file in development
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

    return creds

# check if the credentials are valid by calling the drive api and print a message 
def check_credentials():
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    
    start_time = time.time()
    
    # Query Google Drive for folders
    results = service.files().list(q="mimeType='application/vnd.google-apps.folder'", spaces='drive', fields='nextPageToken, files(id, name)').execute()
    
    end_time = time.time()
    
    folder_count = len(results.get('files', []))
    execution_time = end_time - start_time
    
    print(f"Found {folder_count} folders")
    print(f"Query took {execution_time:.2f} seconds")




# get the folder id of the folder with the name of folder_name
def get_folder_id(folder_name):
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(q=f"name='{folder_name}'", spaces='drive', fields='nextPageToken, files(id, name)').execute()
    return results.get('files', [])[0]['id']    


# Search for files in Google Drive
def search_drive(query):
    creds = get_credentials()

    try:
        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API
        results = service.files().list(
            q=f"mimeType contains 'image/' and name contains '{query}'",
            spaces='drive',
            fields="nextPageToken, files(id, name, thumbnailLink)",
            pageSize=10
        ).execute()
        items = results.get('files', [])

        if not items:
            return []
        else:
            return [{
                'id': item['id'],
                'name': item['name'],
                'thumbnailLink': item.get('thumbnailLink', '')
            } for item in items]

    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

# search in a specific folder
def search_in_folder(folder_id, query_string):
    creds = get_credentials()
    try:
        service = build('drive', 'v3', credentials=creds)
        query = f"'{folder_id}' in parents and name contains '{query_string}' and trashed=false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType, thumbnailLink, webContentLink, webViewLink, size)"
        ).execute()
        items = results.get('files', [])
        
        return [{
            'name': item['name'],
            'thumbnailLink': item.get('thumbnailLink', ''),
            'mimeType': item['mimeType'],
            'webContentLink': item.get('webContentLink', ''),
            'webViewLink': item.get('webViewLink', ''),
            'size': item.get('size', '')
        } for item in items]
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

# search in all target folders and add a target folder name to the result
def search_in_target_folders(query_string):
    start_time = time.time()
    results = []
    for folder_name in target_folders:
        folder_id = get_folder_id(folder_name)
        folder_results = search_in_folder(folder_id, query_string)
        folder_results_with_name = [
            {
                "folder": folder_name,
                "file": result  # result is already a dict, no need to parse
            }
            for result in folder_results
        ]
        results.extend(folder_results_with_name)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Search in target folders took {execution_time:.2f} seconds")
    print(results)
    return results


# function to check the folder  and return the date range based on the file name for nicfi folder: INDEX-YYYYMMDD-nicfi.tif, sentinel:INDEX-YYYYMMDD-sentinel.tif
def check_folder_date_range(folder_name):
    folder_id = get_folder_id(folder_name)
    files = search_in_folder(folder_id, '')

    dates = []
    for file in files:
        name_parts = file['name'].split('-')
        if len(name_parts) >= 2:
            date_str = name_parts[1]
            if date_str.isdigit() and len(date_str) == 8:
                dates.append(date_str)

    if dates:
        date_range = f"{min(dates)}-{max(dates)}"
        print(f"Folder Date Range: {date_range}")
    else:
        print("No valid dates found in folder")

# Example usage



# main function to run the script
def main():
    check_credentials()
    
    # folder_id = get_folder_id('EsriWorldImagery_jpg')
    # print(folder_id)
    # print(search_in_folder(folder_id, '1822'))
    # folder_id_sentinel=get_folder_id(sentinel_tif_folder_name)
    # print(folder_id_sentinel)
    # print(search_in_folder(folder_id_sentinel, '1822'))
    # folder_id_nicfi=get_folder_id(nicfi_folder_name)
    # print(folder_id_nicfi)
    # print(search_in_folder(folder_id_nicfi, '1822'))

    check_folder_date_range(sentinel_tif_folder_name)

if __name__ == '__main__':
    main()