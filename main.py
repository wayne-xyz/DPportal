from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from drive_utils import search_in_target_folders
from update_task import download_tif_file
from drive_utils import rewrite_update_log


app = Flask(__name__, static_folder='static')

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/get_csv')
def get_csv():
    csv_path = os.path.join(app.static_folder, 'data', 'Shapefile_data_20240819.csv')
    return send_from_directory(os.path.dirname(csv_path), os.path.basename(csv_path))

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

# using the cron.yaml to run the update_task function
@app.route('/update_task')
def update_task():
    download_tif_file()
    return jsonify({'status': 'success'})

@app.route('/update_log')
def update_log():
    rewrite_update_log()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)