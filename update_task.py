import datetime
from google.oauth2 import service_account
import ee


SERVICE_ACCOUNT_KEY_FILE = 'stone-armor-430205-e2-2cd696d4afcd.json'
EE_PROJECT_ID="stone-armor-430205-e2"
SHARED_ASSETS_ID="projects/ee-qinheyi/assets/1823_ADRSM"
SHAPE_FILE_SIZE_THRESHOLD=0.1 # in hectares
FILTER_FIELD_NAME="AREA_HA"


# function to update the log file in the static folder, with the current date and time, add the message to the log file
def update_log_file(message):
    with open('static/log.txt', 'a') as log_file:
        log_file.write(f"{datetime.datetime.now()}: {message}\n")
        # example message: 2024-05-15 12:00:00: The task is starting

# function to get the credentials from the service account key file, this scope could write to the drive
def get_credentials():
    # get the credentials from the service account key file
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE, scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/earthengine'])
    return creds

def download_tif_file():
    # print the current date and time

    print(datetime.datetime.now())


def test_ee_connection():
    #Start time
    start_time = datetime.datetime.now()
    # test the earth engine connection

    # authenticate the earth engine
    ee.Authenticate()
    ee.Initialize(get_credentials())

    # Use ee.data.getAsset() instead of ee.Asset()
    asset = ee.data.getAsset(SHARED_ASSETS_ID)

    
    # get the count of the features 
    shapefile_table=ee.FeatureCollection(SHARED_ASSETS_ID)
    # print the count of the features and some description
    print(f"The asset has {shapefile_table.size().getInfo()} features")
    print(f"The asset type is: {asset['type']}")

    # get the count of the features size greater than 0.1 AREA_HA
    features_size_greater_than_0_1HA = shapefile_table.filter(ee.Filter.gte(FILTER_FIELD_NAME, SHAPE_FILE_SIZE_THRESHOLD))
    print(f"The asset has {features_size_greater_than_0_1HA.size().getInfo()} features with size greater than {SHAPE_FILE_SIZE_THRESHOLD} hectares")

    # End time
    end_time = datetime.datetime.now()
    
    print("Earth Engine connection successful")
    print(f"Time taken: {end_time - start_time}")



def main():
    print("Starting the task")
    test_ee_connection()


if __name__ == "__main__":
    download_tif_file()
    main()
