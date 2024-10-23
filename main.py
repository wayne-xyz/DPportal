from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from drive_utils import search_in_target_folders
from daily_task import perform_static_data_saving_csv
import json
from datetime import datetime
import csv
from update_task import schedule_task_download_last_month
import pandas as pd
import logging
from google.cloud import tasks_v2
from google.oauth2 import service_account
app = Flask(__name__, static_folder='static')

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
    """Read and display data from CSV file"""
    data = []
    
    # Determine the correct file path
    if os.getenv('GAE_ENV', '').startswith('standard'):
        csv_file_path = '/tmp/static_data.csv'
        logging.info(f"Running on App Engine, using path: {csv_file_path}")
    else:
        csv_file_path = 'static_data.csv'
        logging.info(f"Running locally, using path: {csv_file_path}")

    try:
        # Check if file exists
        if not os.path.exists(csv_file_path):
            logging.error(f"CSV file not found at: {csv_file_path}")
            return jsonify({'error': 'Data file not found'}), 404

        # Read the static data csv file
        with open(csv_file_path, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                row['date'] = parse_date(row['date'])
                data.append(row)    
        
        logging.info(f"Successfully read {len(data)} rows from CSV")
        
        # Sort the data by date in descending order
        data.sort(key=lambda x: datetime.strptime(x['date'], '%b %Y'), reverse=True)
        
        return render_template('data_statics.html', data=data)
        
    except FileNotFoundError:
        error_msg = f"CSV file not found at: {csv_file_path}"
        logging.error(error_msg)
        return jsonify({'error': error_msg}), 404
        
    except Exception as e:
        error_msg = f"Error reading CSV file: {str(e)}"
        logging.error(error_msg)
        return jsonify({'error': error_msg}), 500



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
#  corn job task to update the static data    
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
        perform_static_data_saving_csv()
        
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
