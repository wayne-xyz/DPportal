import datetime
import os
import yaml
from google.oauth2 import service_account
import ee
import pandas as pd
from ee.ee_exception import EEException




SERVICE_ACCOUNT_KEY_FILE = 'stone-armor-430205-e2-2cd696d4afcd.json'
EE_PROJECT_ID="stone-armor-430205-e2"
SHARED_ASSETS_ID="projects/ee-qinheyi/assets/1823_ADRSM"
SHAPE_FILE_SIZE_THRESHOLD=0.1 # in hectares
FILTER_FIELD_NAME="AREA_HA"
NICFI_IMAGE_PROJECT='projects/planet-nicfi/assets/basemaps/americas'
SENTINEL_IMAGE_PROJECT='COPERNICUS/S2_SR_HARMONIZED'
DEV_TEST_FOLDER_PREFIX="dev_test"
 
# path for the task.yaml file and parameters
TASK_YAML_FILE_PATH='update_task.yaml'
DEV_TEST_FOLDER_NAME="dev_test"
NICFI_FOLDER_NAME="nicfi_tif_2024"
SENTINEL_FOLDER_NAME="sentinel_tif_2024"

# the number of the image to download in one task
DOWNLOAD_IMAGE_POOL_SIZE=2000

EXPORT_TARGET_SHAPE_INDEX_FILE_PATH='static/data/Target_index.csv'
TARGET_INDEX_LIST=[]

#  PREPRARING =================================================
# read the target index csv file and return the index list
def read_target_index_csv():
    # read the target index csv file
    df = pd.read_csv(EXPORT_TARGET_SHAPE_INDEX_FILE_PATH)
    return df['Index'].tolist()

TARGET_INDEX_LIST=read_target_index_csv()


def read_task_yaml():
    # read the task.yaml file
    with open(TASK_YAML_FILE_PATH, 'r') as task_file:
        task_data = yaml.safe_load(task_file)
    # get the dev_test_folder_name, nicfi_folder_name, sentinel_folder_name from the task_data
    global DEV_TEST_FOLDER_NAME, NICFI_FOLDER_NAME, SENTINEL_FOLDER_NAME
    DEV_TEST_FOLDER_NAME = task_data['dev_test_folder_name']
    NICFI_FOLDER_NAME = task_data['nicfi_folder_name']
    SENTINEL_FOLDER_NAME = task_data['sentinel_folder_name']

    return task_data

# read the task.yaml file
read_task_yaml()

#  PREPRARING =================================================

def is_production():
    # Google App Engine sets this environment variable in the production environment
    return os.getenv('GAE_ENV', '').startswith('standard')



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
def export_tif_image_dynamic_size(ind, feature, image, date_str='YYYYMM', source_name="Source", folder_name=DEV_TEST_FOLDER_PREFIX, shape_size=1):
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


#  check the ee task list is complete or not
def is_ee_tasklist_complete():
    tasks = ee.batch.Task.list()
    for task in tasks:
        if task.state == 'RUNNING' or task.state == 'READY':
            return False
    return True



def check_ee_task_list():
    # get the task list from the earth engine
    # List all tasks
    tasks = ee.batch.Task.list()
    print(tasks)





# monthly task to download the tif file from the gee and save them in drive
def download_tif_file(start_month_str, end_month_str):
    #  month_str format: YYYY-MM
    if nicfi_image is None:
        if is_production():
            print("No NICFI image found, try to get the image from the gee")
        nicfi_image=get_nicfi_image_by_month(start_month_str, end_month_str)
    else:
        if is_production():
            print("NICFI image found")


    # print the current date and time
    print("Download last month tif file start: ", datetime.datetime.now())
    task_submit_count=0
    if is_production():
        nicfi_drive_folder_name=NICFI_FOLDER_NAME
    else:
        nicfi_drive_folder_name=DEV_TEST_FOLDER_NAME

    # for loop the shape file table and get the feature for each shape file
    shapefile_table=ee.FeatureCollection(SHARED_ASSETS_ID)
    # count of the shapefile table
    shapefile_table_count=shapefile_table.size().getInfo()
    print(f"The shapefile table has {shapefile_table_count} features")

    # get the index list of the shapefile table
    index_list=shapefile_table.aggregate_array('Index').getInfo()
    print(f"The index list is {index_list}")

    

    # for loop the index list and get the feature for each index    
    for index in index_list:
        # get the feature for each index
        feature=shapefile_table.filter(ee.Filter.eq('Index', index)).first()
        # get the geometry of the feature and size of the geometry
        geometry=feature.geometry()
        size=geometry.area().getInfo()

        # Import the DataFrame
        df = pd.read_csv('static/data/Shapefile_data_20240819.csv')
        area_value = df.loc[df['Index']==index, 'AREA_HA'].values[0]
        print(f"The feature has size {size} square meters, and the area is {area_value} hectares")
        if index in TARGET_INDEX_LIST:
            # get the nicfi image collection from the nicfi_image_collection
            # perfrom the exporting 
            if is_production():
                print("Index,", index, "Size,", size, "Area,", area_value, "is in the target index list")

            # get the nicfi image collection from the nicfi_image_collection
            pass

    















    print(datetime.datetime.now())



#  function to manuly download the tif file for the index
def manuly_download_tif_file(index, start_month_str, end_month_str):
    # manuly download the tif file for the index
    # 1. get the nicfi image from the gee
    # 2. perform the export_tif_image_dynamic_size function

    # get the nicfi image from the gee
    nicfi_image=get_nicfi_image_by_month(start_month_str, end_month_str)

    # get the feature by the index
    feature=get_feature_by_index(index)

    if is_production():
        nicfi_export_folder_name=NICFI_FOLDER_NAME
        sentinel_export_folder_name=SENTINEL_FOLDER_NAME
    else:
        print("Not in the production environment, use the dev_test folder", DEV_TEST_FOLDER_NAME)
        nicfi_export_folder_name=DEV_TEST_FOLDER_NAME
        sentinel_export_folder_name=DEV_TEST_FOLDER_NAME
    


    # perform the export_tif_image_dynamic_size function
    export_tif_image_dynamic_size(index, feature, nicfi_image, date_str='YYYYMM', source_name="nicfi", folder_name=DEV_TEST_FOLDER_PREFIX, shape_size=size_value_ha)





    pass







#  function to get the nicfi image by the start month and end month
def get_nicfi_image_by_month(start_month_str, end_month_str):
    #  paramter format: YYYY-MM
    #  change to ee datas format
    # check if ee is not initialized:

    start_month_str = ee.Date(start_month_str).format('YYYY-MM').getInfo()
    end_month_str = ee.Date(end_month_str).format('YYYY-MM').getInfo()
    nicfi = ee.ImageCollection(NICFI_IMAGE_PROJECT)
    image_collection = nicfi.filter(ee.Filter.date(start_month_str, end_month_str))
    if not is_production():
        # get the date of the image collection
        image_count=image_collection.size().getInfo()
        print(f"The image collection has {image_count} images")
        image_collection_date = image_collection.first().date().format('YYYY-MM').getInfo()
        print(f"The image collection date is {image_collection_date}")
    return image_collection


#  function to get the feature by the index
def get_feature_by_index(index):
    # get the feature by the index
    shapefile_table=ee.FeatureCollection(SHARED_ASSETS_ID)
    feature=shapefile_table.filter(ee.Filter.eq('Index', index)).first()
    if not is_production():
        print(f"The feature has size {feature.geometry().area().getInfo()} square meters")
    return feature







#  function to perform the monthly task which is to download the tif file from the gee and save them in drive
def monthly_task():
    # perform the monthly task
    print("Monthly task start: ", datetime.datetime.now())

    # get the current month
    initialize_ee()
    current_month = datetime.datetime.now().strftime("%Y-%m")
    print("Current month: ", current_month)
    
    # check the nicfi image collection newest image month
    nicfi = ee.ImageCollection(NICFI_IMAGE_PROJECT)
    
    #  check the newest nicfi image month is last month or not
    # Calculate last month's date
    last_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

    newest_nicfi_image = get_nicfi_image_by_month(last_month, current_month)

    
    # Get the newest NICFI image date
    newest_nicfi_date = ee.Date(newest_nicfi_image.date()).format('YYYY-MM').getInfo()
    print("Newest NICFI image month: ", newest_nicfi_date)
    
    if newest_nicfi_date == last_month:
        #  perform the download tif file task

        print("The newest NICFI image is from last month")
        if is_ee_tasklist_complete():
            print("The ee task list is complete")
            print("Start to download the tif file of the last month")
            

        else:
            print("The ee task list is not complete")
        



    else:
        print(f"The newest NICFI image is not from last month. It's from: {newest_nicfi_date}")


    # get the shapefile table


    pass





# function to test the earth engine connection
def test_ee_connection():
    #Start time
    initialize_ee()
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




#  function to test the export_tif_image_dynamic_size function
def test_export_tif_image_dynamic_size():
    # test the export_tif_image_dynamic_size function
    start_time = datetime.datetime.now()
    initialize_ee()
    
    # check the current ee's project information
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
        nicfi_image = nicfi.filterDate("2024-06-01T00:00:00", "2024-07-01T00:00:00").sort('system:time_start', False).first()

        if nicfi_image:
            print("NICFI image retrieved successfully")
            print(ee.Date(nicfi_image.date()).format().getInfo())
            export_tif_image_dynamic_size(index_value, test_feature, nicfi_image, date_str='YYYYMM', source_name="nicfi", folder_name=DEV_TEST_FOLDER_PREFIX, shape_size=size_value_ha)
        else:
            print("No NICFI image found for the given date range. This could be due to no images in the specified timeframe.")

    except EEException as ee_error:
        if "not found" in str(ee_error):
            print(f"Error: You do not have access to the NICFI collection. {ee_error}")
            print("Please ensure you have requested and been granted access to NICFI data.")
            print("Visit https://developers.planet.com/nicfi/ to request access if needed.")
        else:
            print(f"Earth Engine error: {ee_error}")
    except Exception as e:
        print(f"Unexpected error accessing NICFI collection: {e}")

    #end time
    end_time = datetime.datetime.now()
    print(f"Time taken: {end_time - start_time}")


def main():
    pass


if __name__ == "__main__":
    main()
