# DPportal
portal website on Google cloud App Engine

## Deployment Instructions

### Google Cloud setup

1. Create a new project in Google Cloud Console
2. Enable the App Engine API for the project
3. Google Drive API setup 
4. Enable the Google Drive API for the project
5. Create a new OAuth 2.0 client ID and download the JSON key file
6. Set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` to the path of the JSON key file
7. Hide the JSON key file by adding it to .gitignore (google_drive_credentials.json)




### Deployment
1. Install the requirements

```
pip install -r requirements.txt
```

2. Deploy the app

```
gcloud app deploy
```