from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
import csv
from collections import defaultdict
import re
import os

import time


# For save the static data to the csv file 
STATIC_DATE_START= "202301"
STATIC_DATE_END= "202407"



SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# service account key file: two keys are provided, one for dev1, one for dev2
DRIVE_GEE_KEY_FILE = 'stone-armor-430205-e2-2cd696d4afcd.json'

if DRIVE_GEE_KEY_FILE not in os.listdir():
    DRIVE_GEE_KEY_FILE = 'stone-armor-430205-e2-9913c17acb94.json'


# folder names
esri_world_imagery_folder_name="EsriWorldImagery_jpg"
sentinal_jpg_folder_name="sentinel_jpg"
nicfi_jpg_folder_name="nicfi_jpg"
sentinel_tif_folder_name="sentinel_tif_2024"
nicfi_folder_name="nicfi_tif_2024"

# target folders
target_folders=[esri_world_imagery_folder_name, nicfi_jpg_folder_name, sentinal_jpg_folder_name, sentinel_tif_folder_name, nicfi_folder_name]

static_folder_name=[nicfi_folder_name,nicfi_jpg_folder_name,sentinel_tif_folder_name,sentinal_jpg_folder_name]


def is_production():
    # Google App Engine sets this environment variable in the production environment
    return os.getenv('GAE_ENV', '').startswith('standard')


def test_service_account_key_file():
    creds = service_account.Credentials.from_service_account_file(DRIVE_GEE_KEY_FILE,scopes=SCOPES)
    # build the drive service
    drive_service = build('drive', 'v3', credentials=creds)
    # get the folders' names
    results = drive_service.files().list(q="mimeType='application/vnd.google-apps.folder'", spaces='drive', fields='nextPageToken, files(id, name)').execute()
    print(results)



# use service account key file to get the credentials
def get_credentials():
    # using the service account key file
    creds = service_account.Credentials.from_service_account_file(DRIVE_GEE_KEY_FILE,scopes=SCOPES)
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
    # print the folder names, only the name
    print(f"Folders: {[folder['name'] for folder in results.get('files', [])]}")
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
    # print the length of the results
    print(f"Found {len(results)} results")
    return results


# function to check the folder  and return the date range based on the file name for nicfi folder: INDEX-YYYYMMDD-nicfi.tif, sentinel:INDEX-YYYYMMDD-sentinel.tif
def check_folder_date_range(folder_name):
    folder_id = get_folder_id(folder_name)
    files = search_in_folder(folder_id, '1822')

    dates = []
    for file in files:
        name_parts = file['name'].split('-')
        if len(name_parts) >= 2:
            date_str = name_parts[1]
            if date_str.isdigit() and len(date_str) == 8:
                dates.append(date_str)

    if dates:
        # print the date range
        print(f"Date range of {folder_name}: {min(dates)}-{max(dates)}")
        return f"{min(dates)}-{max(dates)}"
    else:
        return "No valid dates found"

# write down the Date range of the two folders in the static log file
def rewrite_update_log():
    # save the logfile in the static folder
    with open('static/update_log.txt', 'w') as log_file:
        sentinel_range = check_folder_date_range(sentinal_jpg_folder_name)
        nicfi_range = check_folder_date_range(nicfi_jpg_folder_name)
        log_file.write(f"Date range of {sentinal_jpg_folder_name}: {sentinel_range}\n")
        log_file.write(f"Date range of {nicfi_jpg_folder_name}: {nicfi_range}\n")



# process the current date in the folder_name and return the count of the files
def count_files_in_date_folder(folder_name, current_date):
    count = 0
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    folder_id = get_folder_id(folder_name)
    
    # Query for image files (jpg, jpeg, tif, tiff) containing the current date
    query = f"'{folder_id}' in parents and name contains '{current_date}' and trashed=false"
    # query += "mimeType='image/jpeg' or mimeType='image/tiff' or "
    # query += "fileExtension='jpg' or fileExtension='jpeg' or fileExtension='tif' or fileExtension='tiff')"
    

    page_token = None
    while True:
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name)',
            pageToken=page_token,
            pageSize=100  # Increase page size for efficiency
        ).execute()
        
        files = results.get('files', [])

        count += len(files)
        
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    if not is_production():
        print(f"Folder {folder_name} has {count} files for date {current_date}")

    return count



#  iterate over the static date range and interate the files_list and save the static data to the csv file
def perform_static_data_saving_csv():
    # get the static date start and end from the environment variables
    static_date_start = STATIC_DATE_START   
    static_date_end = STATIC_DATE_END

    if not is_production():
        print(f"Static date start: {static_date_start}, static date end: {static_date_end}")

    # iterate over the static date range and print the date the format is YYYYMM
    current_date = static_date_end
    while current_date >= static_date_start:
        if not is_production():
            print(f"Processing date: {current_date}")

        # Process the current date here
        for folder_name in static_folder_name:
            count = count_files_in_date_folder(folder_name, current_date)
            
        year = current_date[:4]
        month = current_date[4:6]
        
        # Decrement the date
        month = int(month) - 1
        if month < 1:
            month = 12
            year = str(int(year) - 1)
        
        current_date = f"{year}{month:02d}"

    # ... rest of the function ...
    pass 


    


def test_credentials():
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

    rewrite_update_log()

# main function to run the script
def main():
    test_credentials()



if __name__ == '__main__':
    main()
