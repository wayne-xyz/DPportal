import datetime
from google.oauth2 import service_account
import ee
import pandas as pd



SERVICE_ACCOUNT_KEY_FILE = 'stone-armor-430205-e2-2cd696d4afcd.json'
EE_PROJECT_ID="stone-armor-430205-e2"
SHARED_ASSETS_ID="projects/ee-qinheyi/assets/1823_ADRSM"
SHAPE_FILE_SIZE_THRESHOLD=0.1 # in hectares
FILTER_FIELD_NAME="AREA_HA"
NICFI_IMAGE_PROJECT='projects/planet-nicfi/assets/basemaps/americas'
SENTINEL_IMAGE_PROJECT='COPERNICUS/S2_SR_HARMONIZED'


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

# function to initialize the earth engine before using it
def initialize_ee():
    ee.Authenticate()
    ee.Initialize(get_credentials(),project=EE_PROJECT_ID)


# function to export the tif file image from GEE to Google Drive, based on the size of the shape 
def export_tif_image_dynamic_size(ind, feature, image, date_str='YYYYMM', source_name="Source", folder_name="tif_file", shape_size=1):
    """
    Export a TIF image from Google Earth Engine to Google Drive with dynamic sizing.

    Args:
        ind (int): Index for the shapefile.
        feature (ee.Feature): Shape of the area of interest.
        image (ee.Image): Image to export.
        date_str (str, optional): Image date in 'YYYYMM' or 'YYYYMMDD' format. Defaults to 'YYYYMM'.
        source_name (str, optional): Source of the image (e.g., 'sentinel', 'nicfi'). Defaults to "Source".
        folder_name (str, optional): Folder name in Google Drive for export. Defaults to "tif_file".
        shape_size (float, optional): Size of the shape in hectares. Defaults to 1.

    Returns:
        None
    """
    # Convert hectares to square meters (1 hectare = 10,000 square meters).
    if shape_size < 4:
        exportSizeSqMeters = 5 * 10000
    else:
        exportSizeSqMeters = shape_size * 10000 *2


    # Get the centroid of the feature.
    centroid = feature.geometry().centroid()

    # Create a bounding box of 5 hectares centered on the centroid.
    halfSideLength = (exportSizeSqMeters ** 0.5)
    exportRegion = centroid.buffer(halfSideLength).bounds()

    # define the scale for two type of image
    res_scale=10
    if source_name=="sentinel":
        res_scale=10
    elif source_name=="nicfi":
        res_scale=5
    else:
        print("source_name error")
        return

    # Start the export task.
    task = ee.batch.Export.image.toDrive(
        image=image.clip(exportRegion),
        description=f"export_{ind}_{date_str}",
        folder=folder_name,
        region=exportRegion,
        scale=res_scale,
        crs='EPSG:4326',
        maxPixels=1e13,
        fileNamePrefix=f"{ind}-{date_str}-{source_name}"
    )
    task.start()
    print(f"Export task started for index {ind} with date {date_str}")


def check_ee_task_list():
    # get the task list from the earth engine
    # List all tasks
    tasks = ee.batch.Task.list()
    print(tasks)

def test_export_tif_image_dynamic_size():
    # test the export_tif_image_dynamic_size function
    start_time = datetime.datetime.now() 

    test_filter_field_name="Index"
    index_value=1815
    test_selecter=ee.Filter.eq(test_filter_field_name, index_value)
    shapefile_table=ee.FeatureCollection(SHARED_ASSETS_ID)
    test_feature=shapefile_table.filter(test_selecter).first()

    # get the geometry of the test feature and size of the geometry
    test_geometry=test_feature.geometry()
    test_size=test_geometry.area().getInfo()
    print(f"The test feature has size {test_size} square meters")

    # loac csv file from the static/data/Shapefile_data_20240819.csv
    csv_file_path='static/data/Shapefile_data_20240819.csv'
    df=pd.read_csv(csv_file_path)
    size_value_ha=df.loc[df['Index']==index_value, 'AREA_HA'].values[0]
    print(f"The test feature has size {size_value_ha} hectares")

    # Define a simple query to test access to the NICFI collection
    try:
        nicfi = ee.ImageCollection(NICFI_IMAGE_PROJECT)
        # Use the most recent complete quarter
        nicfi_image = nicfi.filterDate("2024-06-01T00:00:00", "2024-07-01T00:00:00").sort('system:time_start', False).first()

        print(ee.Date( nicfi_image.date()).format().getInfo())

        if nicfi_image:
            print("NICFI image retrieved successfully")
            export_tif_image_dynamic_size(index_value, test_feature, nicfi_image, date_str='YYYYMM', source_name="nicfi", folder_name="test_file", shape_size=size_value_ha)
        else:
            print("No NICFI image found for the given date range")

    except Exception as e:
        print(f"Error accessing NICFI collection: {e}")

    #end time
    end_time = datetime.datetime.now()
    print(f"Time taken: {end_time - start_time}")


# monthly task to download the tif file from the gee and save them in drive
def download_tif_file():
    # print the current date and time

    print(datetime.datetime.now())


# function to test the earth engine connection
def test_ee_connection():
    #Start time
    start_time = datetime.datetime.now()
    # test the earth engine connection

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




# save the static file to the static folder from the google drive
def save_static_file():
    # save the static file to the static folder
    #  path for csv file
    static_csv_file_path='static/data/static_data.csv'

    # perform the static file by check the google drive folder 


    pass



def main():
    print("Starting the task")
    initialize_ee()
    test_ee_connection()
    test_export_tif_image_dynamic_size()



if __name__ == "__main__":
    download_tif_file()
    main()
