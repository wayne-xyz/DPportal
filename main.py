from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from drive_utils import search_in_target_folders,is_production,get_credentials,get_folder_id
from daily_task import perform_static_data_saving_csv
import json
from datetime import datetime
import csv
from update_task import schedule_task_download_last_month
import pandas as pd
import logging
from google.cloud import tasks_v2
from google.oauth2 import service_account
from googleapiclient.discovery import build
from imageFile_statistics import get_file_id,image_files_names_statistics_to_csv



app = Flask(__name__, static_folder='static')


STATIC_CSV_FILE_NAME='imageFile_statistics.csv'
STATIC_CSV_FILE_FOLDER_DRIVE='Images'



# show the main page
@app.route('/')
def hello():
    return render_template('index.html')

# load the csv file to browser
@app.route('/get_csv')
def get_csv():
    csv_path = os.path.join(app.static_folder, 'data', 'Shapefile_data_20240819.csv')
    df = pd.read_csv(csv_path)
    return df.to_json(orient='records')


def parse_date(date_str):
    return datetime.strptime(date_str, '%Y%m').strftime('%b %Y')

# show the static data page
@app.route('/data_statistics')
def data_statistics():
    # 
    return render_template('data_statics.html')



#  Setting the cloud task client and the queue
PROJECT_ID='stone-armor-430205-e2'
QUEUE_NAME='Dailly-Task'
QUEUE_LOCATION='us-central1'
APP_ENGINE_SERVICE_ACCOUNT_KEY_FILE='stone-armor-430205-e2-2e2b33825983.json'
try:
    task_credential=service_account.Credentials.from_service_account_file(APP_ENGINE_SERVICE_ACCOUNT_KEY_FILE)
    client = tasks_v2.CloudTasksClient(credentials=task_credential)
    logging.info("CloudTasksClient created successfully")
except Exception as e:
    logging.error(f"Error creating CloudTasksClient: {str(e)}")



# ========================== corn job task ==========================
#  corn job task to update the static data , for the statistics csv file update   
@app.route('/daily_task')
def daily_task():
    """Endpoint triggered by cron to create the Cloud Task"""


    start_time = datetime.now()
    logging.info(f"Creating task at {start_time}")

    try:
        # Construct the queue path
        parent = client.queue_path(PROJECT_ID, QUEUE_LOCATION, QUEUE_NAME)

        # Create task
        task = {
            'app_engine_http_request': {
                'http_method': tasks_v2.HttpMethod.POST,
                'relative_uri': '/process_daily_task',
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
        }

        # Create the task
        response = client.create_task(request={
            'parent': parent,
            'task': task
        })

        logging.info(f"Task created: {response.name}")
        return jsonify({
            'status': 'success',
            'message': 'Task created successfully',
            'task_name': response.name,
            'creation_time': start_time.isoformat()
        })

    except Exception as e:
        logging.error(f"Error creating task: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

#  this is the scheduled task function to update the statistics csv file
@app.route('/process_daily_task', methods=['POST'])
def process_daily_task():
    """Endpoint that actually processes the task"""
    # Verify the request is from Cloud Tasks
    if 'X-AppEngine-QueueName' not in request.headers:
        return 'Unauthorized', 403

    start_time = datetime.now()
    logging.info(f"Starting task processing at {start_time}")

    try:
        # Perform your long-running task
        image_files_names_statistics_to_csv()
        
        end_time = datetime.now()
        duration = end_time - start_time
        logging.info(f"Task completed successfully at {end_time}. Duration: {duration}")
        
        return jsonify({
            'status': 'success',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': str(duration)
        })

    except Exception as e:
        logging.error(f"Error processing task: {str(e)}")
        # Return 500 to trigger task retry
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# using the cron.yaml to run the update_task function
@app.route('/update_task')
def update_task():
    try:
        schedule_task_download_last_month()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ========================== corn job task ==========================


# search the files in the target folders
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')

    # Perform the search in target folders
    results = search_in_target_folders(query)

    # Format the results to be returned as JSON
    formatted_results = [
        {
            'folder': result['folder'],
            'name': result['file']['name'],
            'thumbnailLink': result['file']['thumbnailLink'],
            'webViewLink': result['file']['webViewLink'],
            'webContentLink': result['file']['webContentLink'],
            'size': result['file']['size']
        }
        for result in results
    ]

    return jsonify(formatted_results)


# TODO: fix the limit only for the javascript fetch request and from the same origin
@app.route('/get_esri_api_key')
def get_esri_api_key():
    api_key = json.load(open('esri_api_key.json'))['ESRI_API_KEY']
    return jsonify({'api_key': api_key})


@app.route('/get_statistics_csv')
def get_statistics_csv():
    """Fetch CSV from Drive and return as JSON"""
    try:
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)
        
        # Get folder ID
        folder_id = get_folder_id(STATIC_CSV_FILE_FOLDER_DRIVE)
        if not folder_id:
            logging.error("Folder not found")
            return jsonify({'error': 'Statistics folder not found'}), 404
            
        # Get file ID
        file_id = get_file_id(STATIC_CSV_FILE_NAME, folder_id)
        if not file_id:
            logging.error("CSV file not found")
            return jsonify({'error': 'Statistics file not found'}), 404
            
        # Get file metadata including modification time
        file_metadata = service.files().get(fileId=file_id, 
                                          fields='modifiedTime').execute()
        modified_time = file_metadata.get('modifiedTime')
        
        try:
            # Download file content
            request = service.files().get_media(fileId=file_id)
            content = request.execute()
            
            # Parse CSV content
            csv_content = content.decode('utf-8').splitlines()
            reader = csv.DictReader(csv_content)
            
            # Convert to list of dictionaries
            data = []
            for row in reader:
                # Parse and format the date if needed
                if 'Month' in row:
                    try:
                        # Assuming date format is 'YYYY-MM'
                        date_obj = datetime.strptime(row['Month'], '%Y-%m')
                        row['Month'] = date_obj.strftime('%b %Y')  # Format as 'Mar 2024'
                    except ValueError as e:
                        logging.warning(f"Date parsing error: {e}")
                
                # Convert numeric strings to integers
                for key in ['NICFI TIF', 'NICFI JPG', 'Sentinel-2 TIF', 'Sentinel-2 JPG']:
                    if key in row:
                        try:
                            row[key] = int(row[key])
                        except ValueError:
                            row[key] = 0
                
                data.append(row)
            
            # Sort by date (newest first)
            data.sort(key=lambda x: datetime.strptime(x['Month'], '%b %Y'), reverse=True)
            
            logging.info(f"Successfully fetched and parsed CSV with {len(data)} rows")
            return jsonify({
                'data': data,
                'lastUpdated': modified_time
            })
            
        except Exception as file_error:
            logging.error(f"Error reading file content: {str(file_error)}")
            return jsonify({'error': 'Failed to read statistics file'}), 500
            
    except Exception as e:
        logging.error(f"Error in get_statistics_csv: {str(e)}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
