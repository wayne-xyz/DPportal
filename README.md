# DPportal
portal website on Google cloud App Engine

URL: https://stone-armor-430205-e2.uc.r.appspot.com/

## Developing ToDo List
- [ ] Support name of dumpsite ( auto-complete)
- [ ] migrate all the jpeg files from OneDrive to Google Drive 
- [ ] Monthly update of jpeg files and tif files adding functionality, both nicfi and sentinel
- [ ] Map viewing functionality
- [ ] Long term authentication for Google Drive, limitation for user



## Version 1.0 Features 
- Search for files in Google Drive, by the index of dumpsite.
- View file details, only jpeg files are supported.
- Download file, both jpeg and tif files are supported.
- Include the sentinel(2024), nicfi(2024), Esriworldimagery, 




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

After updating the code, deploy the app:
```
gcloud app deploy
```

Monitor the app's logs:
```
gcloud app logs tail -s default
```