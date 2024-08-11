from flask import Flask, render_template,request, jsonify
from drive_utils import search_drive

app = Flask(__name__,static_folder='static')



@app.route('/')
def hello():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)


@app.route('/search')
def search():
    query = request.args.get('query', '')
    # Use the Google Drive API to search for images
    # Return results as JSON
    results = search_drive(query)
    return jsonify(results)

# ... rest of your app ...