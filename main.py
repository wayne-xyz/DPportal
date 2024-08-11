from flask import Flask, render_template,request, jsonify
from drive_utils import search_in_target_folders

app = Flask(__name__,static_folder='static')



@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')

    # Perform the search in target folders
    results = search_in_target_folders(query)

    # Format the results to be returned as JSON
    formatted_results = [
        {
            'folder': result.split(': ')[0],
            'name': result.split(': ')[1]
        }
        for result in results
    ]

    return jsonify(formatted_results)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
# ... rest of your app ...