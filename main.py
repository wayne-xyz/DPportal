from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from drive_utils import search_in_target_folders
from daily_task import perform_static_data_saving_csv
import json
from datetime import datetime
import csv
from update_task import schedule_task_download_last_month
import pandas as pd

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
@app.route('/data_statics')
def data_statics():
    data = []
    with open('static/data/static_data.csv', 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            row['date'] = parse_date(row['date'])
            data.append(row)
    
    # Sort the data by date in descending order
    data.sort(key=lambda x: datetime.strptime(x['date'], '%b %Y'), reverse=True)
    
    return render_template('data_statics.html', data=data)

# ========================== corn job task ==========================
#  corn job task to update the static data    
@app.route('/daily_task')
def daily_task():
    perform_static_data_saving_csv()
    return jsonify({'status': 'success'})


# using the cron.yaml to run the update_task function
@app.route('/update_task')
def update_task():
    print("update_task", datetime.now())
    schedule_task_download_last_month()
    return jsonify({'status': 'success'})

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
