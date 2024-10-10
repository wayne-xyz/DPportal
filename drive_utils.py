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




SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# service account key file
DRIVE_GEE_KEY_FILE = 'stone-armor-430205-e2-2cd696d4afcd.json'

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


# get all the files names by folder name or list of folder names from Google Drive
def get_all_files_names(folder_names):
    all_files = {}
    if isinstance(folder_names, str):
        folder_names = [folder_names]
    
    for folder_name in folder_names:
        folder_id = get_folder_id(folder_name)
        files = search_in_folder(folder_id, '')
        all_files[folder_name] = [file['name'] for file in files]
    
    return all_files


def perform_saving_static_data():
    # save the all_files to the csv file
    all_files_dict = get_all_files_names(static_folder_name)

    if is_production()==False:
        print(all_files_dict)


    # Define the CSV file path
    output_csv = 'static/data/static_data.csv'
        # Dictionary to store the aggregated data
    result = defaultdict(lambda: defaultdict(int))

   # Regular expressions for matching the two formats
    regex_format_1 = re.compile(r'\d{3,6}-\d{4}-\d{2}-.*\.(tif|jpg)')
    regex_format_2 = re.compile(r'\d{3,6}-\d{6}-.*\.(tif|jpg)')

    # Process each folder and its files
    for folder, files in all_files_dict.items():
        for file in files:
            try:
                # Check if the file matches the first format: index-YYYY-MM-sourcetype.tif/jpg
                if regex_format_1.match(file):
                    # Split the filename by '-' and '.'
                    parts = file.split('-')
                    if len(parts) != 3:
                        continue  # Skip filenames that don't match the expected format
                    
                    index, date_part, rest = parts
                    year, month = date_part.split('-')
                    yyyymm = f"{year}{month}"  # Create the YYYYMM key

                # Check if the file matches the second format: index-YYYYMM-sourcetype.tif/jpg
                elif regex_format_2.match(file):
                    parts = file.split('-')
                    if len(parts) != 2:
                        continue  # Skip filenames that don't match the expected format

                    index, rest = parts
                    date_part = index[-6:]  # Extract the YYYYMM from the last 6 digits
                    yyyymm = date_part  # Use YYYYMM directly

                else:
                    continue  # Skip files that don't match either format

                # Increment the count for the folder (source) and YYYYMM
                result[yyyymm][folder] += 1

            except Exception as e:
                print(f"Error processing file {file}: {e}")
    
    # Get all folder names (source types, now columns)
    folders = sorted(all_files_dict.keys())

    # Write to CSV
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write the header (folder names as columns)
        writer.writerow(['YYYYMM'] + folders)
        
        # Write the rows (YYYYMM and counts for each folder)
        for yyyymm, counts in sorted(result.items()):
            row = [yyyymm] + [counts.get(folder, 0) for folder in folders]
            writer.writerow(row)
    


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