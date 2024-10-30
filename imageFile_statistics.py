from drive_utils import get_credentials,get_folder_id,is_production
from googleapiclient.discovery import build
from datetime import datetime
import csv
from collections import defaultdict
from googleapiclient.http import MediaFileUpload

NICFI_TIF_FOLDER_NAME='nicfi_tif_2024'
NICFI_JPG_FOLDER_NAME='nicfi_jpg'
SENTINEL_2_TIF_FOLDER_NAME='sentinel_tif_2024'
SENTINEL_2_JPG_FOLDER_NAME='sentinel_jpg'
STATIC_CSV_FILE_NAME='imageFile_statistics.csv'
STATIC_CSV_FILE_FOLDER_DRIVE="Images"
APP_ENGINE_TMP_DIR='/tmp'

# scopes for writing the csv file to the drive
SCOPES_WRITE_CSV_TO_DRIVE=["https://www.googleapis.com/auth/drive.file"]


CSV_START_DATE='2024-10'
CSV_END_DATE='2021-01'


#  get the files'names in the folder by the folder id, normally each page of results is 100 files
def get_files_in_folder(folder_id):
    # using the google drive api to get the files in the folder
    # return the files'names
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    query = f"'{folder_id}' in parents and trashed=false"
    
    results = []
    page_token = None
    while True:
        print(f"Getting the files in the folder {folder_id}, current page token last 10 is {page_token[-10:] if page_token else 'None'}")
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name)',
            pageToken=page_token
        ).execute()
        results.extend(response.get('files', []))
        
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    
    return [file['name'] for file in results]


# function get all the files'names in the drive folder
def get_all_files_names_in_drive_folder(folder_name):
    # get the folder id
    print(f"Start to get all files'names in the folder {folder_name}, at time {datetime.now()}")
    folder_id=get_folder_id(folder_name)
    # get all the files'names in the folder
    files_names=get_files_in_folder(folder_id)

    print(f"End to get all files'names in the folder {folder_name}, at time {datetime.now()}, the number of files is {len(files_names)}")
    # return the files'names    
    return files_names


#  main functioin to parse all 4 folders'files'names to csv file by monthly show them in the csv file, to be a table for the data
def image_files_names_statistics_to_csv():

    start_time = datetime.now()
    print(f"Start to parse the file names to csv file at {start_time}")


    # Get all files from each folder
    nicfi_tif_files = get_all_files_names_in_drive_folder(NICFI_TIF_FOLDER_NAME)
    nicfi_jpg_files = get_all_files_names_in_drive_folder(NICFI_JPG_FOLDER_NAME)
    sentinel_tif_files = get_all_files_names_in_drive_folder(SENTINEL_2_TIF_FOLDER_NAME)
    sentinel_jpg_files = get_all_files_names_in_drive_folder(SENTINEL_2_JPG_FOLDER_NAME)
    
    # Create dictionaries to store counts by month
    nicfi_tif_counts = defaultdict(int)
    nicfi_jpg_counts = defaultdict(int)
    sentinel_tif_counts = defaultdict(int)
    sentinel_jpg_counts = defaultdict(int)
    
    # Count files by month for each type
    # NICFI TIF format: xxxxx-YYYY-MM-nicif.tif
    for filename in nicfi_tif_files:
        parts = filename.split('-')
        if len(parts) >= 2:
            date_str = parts[1] + '-' + parts[2][:2]  # Get YYYY-MM
            nicfi_tif_counts[date_str] += 1
    
    # Other files format: xxxx-YYYYMMDD-xxxx.tif/jpg
    for filename in nicfi_jpg_files:
        parts = filename.split('-')
        if len(parts) >= 2:
            date_part = parts[1]  # Get YYYYMMDD
            if len(date_part) >= 6:
                date_str = date_part[:4] + '-' + date_part[4:6]  # Convert to YYYY-MM
                nicfi_jpg_counts[date_str] += 1
    
    for filename in sentinel_tif_files:
        parts = filename.split('-')
        if len(parts) >= 2:
            date_part = parts[1]  # Get YYYYMMDD
            if len(date_part) >= 6:
                date_str = date_part[:4] + '-' + date_part[4:6]  # Convert to YYYY-MM
                sentinel_tif_counts[date_str] += 1
    
    for filename in sentinel_jpg_files:
        parts = filename.split('-')
        if len(parts) >= 2:
            date_part = parts[1]  # Get YYYYMMDD
            if len(date_part) >= 6:
                date_str = date_part[:4] + '-' + date_part[4:6]  # Convert to YYYY-MM
                sentinel_jpg_counts[date_str] += 1


    # Generate list of months from start to end date
    start = datetime.now().replace(day=1)  # First day of current month
    end = datetime.strptime(CSV_END_DATE, '%Y-%m')
    months = []
    current = start
    while current >= end:  # Note: >= because we're going backwards in time
        months.append(current.strftime('%Y-%m'))
        current = datetime(current.year + (current.month-2)//12, 
                         ((current.month-2)%12)+1, 
                         1)
    
    # Write to CSV to the drive folder
    csv_folder_id = get_folder_id(STATIC_CSV_FILE_FOLDER_DRIVE)

    # if in my local machine, save the csv file to the local machine, if in app engine, save the csv file to the app engine tmp dir
    if not is_production():
        csv_path = f"{STATIC_CSV_FILE_NAME}"
    else:   
        csv_path = f"{APP_ENGINE_TMP_DIR}/{STATIC_CSV_FILE_NAME}"

    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['Month', 'NICFI TIF', 'NICFI JPG', 'Sentinel-2 TIF', 'Sentinel-2 JPG'])
        # Write data for each month
        for month in months:
            writer.writerow([
                month,
                nicfi_tif_counts[month],
                nicfi_jpg_counts[month],
                sentinel_tif_counts[month],
                sentinel_jpg_counts[month]
            ])
    
    # Upload the CSV to Drive
    file_id = upload_csv_to_drive(csv_path, csv_folder_id)
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"End to parse the file names to csv file at {end_time}, the total time is {duration}")
    return file_id


def upload_csv_to_drive(csv_path, folder_id):
    try:
        creds = get_credentials(SCOPES_WRITE_CSV_TO_DRIVE)
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': STATIC_CSV_FILE_NAME,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(
            csv_path,
            mimetype='text/csv',
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f'File uploaded successfully. File ID: {file.get("id")}')
        return file.get('id')
    except Exception as e:
        print(f'An error occurred while uploading: {str(e)}')
        return None

def test_upload_local_csv_file_to_drive(file_path=STATIC_CSV_FILE_NAME,folder_name=STATIC_CSV_FILE_FOLDER_DRIVE):
    # get the folder id
    folder_id = get_folder_id(folder_name)
    # upload the csv file to the folder
    upload_csv_to_drive(file_path,folder_id)


def fetch_csv_file_from_drive(file_name=STATIC_CSV_FILE_NAME,folder_name=STATIC_CSV_FILE_FOLDER_DRIVE):

    print(f"Start to fetch the csv file from the drive at {datetime.now()}")
    # get the folder id
    folder_id = get_folder_id(folder_name)
    # write the implementation for getting the csv file from the drive and save it to the local machine as name test.csv
    file_id = get_file_id(file_name,folder_id)

    download_file_from_drive(file_id,f"{file_name}")

    print(f"End to fetch the csv file from the drive at {datetime.now()}")
    

def get_file_id(file_name, folder_id):
    # get the file id from the drive
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    
    # Search for the file in the specified folder
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id)',
        pageSize=1  # We only need the first match
    ).execute()
    
    files = results.get('files', [])
    if files:
        return files[0]['id']
    return None


def download_file_from_drive(file_id, file_path):
    # download the file from the drive
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    

    if is_production():
        file_path = f"{APP_ENGINE_TMP_DIR}/{file_path}"

    try:
        # Get the file content
        request = service.files().get_media(fileId=file_id)
        file_content = request.execute()
        
        # Write to file
        with open(file_path, 'wb') as f:
            f.write(file_content)
            
        print(f"File successfully downloaded to {file_path}")
        
    except Exception as e:
        print(f"An error occurred while downloading: {str(e)}")


# only for testing
def main():
    # parse_file_name_to_csv()
    
    fetch_csv_file_from_drive()
    pass

if __name__ == "__main__":
    main()


