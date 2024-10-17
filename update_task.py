import datetime
import os
import yaml
from google.oauth2 import service_account
import ee
import pandas as pd
from ee.ee_exception import EEException
from abc import ABC, abstractmethod
from typing import List, Tuple
import time

# Constants
SERVICE_ACCOUNT_KEY_FILE = 'stone-armor-430205-e2-2cd696d4afcd.json'
EE_PROJECT_ID = "stone-armor-430205-e2"
SHARED_ASSETS_ID = "projects/ee-qinheyi/assets/1823_ADRSM"
NICFI_IMAGE_PROJECT = 'projects/planet-nicfi/assets/basemaps/americas'
SENTINEL_IMAGE_PROJECT = 'COPERNICUS/S2_SR_HARMONIZED' #
TASK_YAML_FILE_PATH = 'update_task.yaml' # the path to the yaml file, in the yaml file: three keys: dev_test_folder_name, nicfi_folder_name, sentinel_folder_name
EXPORT_TARGET_SHAPE_INDEX_FILE_PATH = 'static/data/Target_index.csv' # the path to the target index csv file
SHAPEFILE_DATA_PATH = 'static/data/Shapefile_data_20240819.csv' # the path to the shapefile data csv file
MAX_CONCURRENT_TASKS = 2000
TASK_CHECK_INTERVAL = 600  # seconds




# Utility functions
def is_production():
    return os.getenv('GAE_ENV', '').startswith('standard')

def get_credentials():
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_KEY_FILE, 
        scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/earthengine']
    )

def initialize_ee():
    if not ee.data._initialized:
        ee.Initialize(get_credentials(), project=EE_PROJECT_ID)
        print("Earth Engine initialized.")

def read_task_yaml():
    with open(TASK_YAML_FILE_PATH, 'r') as task_file:
        return yaml.safe_load(task_file)

def read_target_index_csv():
    df = pd.read_csv(EXPORT_TARGET_SHAPE_INDEX_FILE_PATH)
    return df['Index'].tolist()

# Global variables
TARGET_INDEX_LIST = read_target_index_csv()



# Image Source classes
class ImageSource(ABC):
    @abstractmethod
    def get_collection(self, start_date: str, end_date: str) -> ee.ImageCollection:
        pass

    @abstractmethod
    def get_export_dates(self, start_date: str, end_date: str) -> List[Tuple[str, str]]:
        pass

class NICFISource(ImageSource):
    def get_collection(self, start_date: str, end_date: str) -> ee.ImageCollection:
        return ee.ImageCollection(NICFI_IMAGE_PROJECT).filterDate(start_date, end_date)

    def get_export_dates(self, start_date: str, end_date: str) -> List[Tuple[str, str]]:
        return [(start_date, end_date)]

class SentinelSource(ImageSource):
    def get_collection(self, start_date: str, end_date: str) -> ee.ImageCollection:
        return ee.ImageCollection(SENTINEL_IMAGE_PROJECT).filterDate(start_date, end_date)

    def get_export_dates(self, start_date: str, end_date: str) -> List[Tuple[str, str]]:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        dates = []
        while start < end:
            month_end = start.replace(day=28) + datetime.timedelta(days=4)
            month_end = month_end.replace(day=1) - datetime.timedelta(days=1)
            dates.extend([
                (start.strftime("%Y-%m-%d"), (start.replace(day=10) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")),
                (start.replace(day=10).strftime("%Y-%m-%d"), (start.replace(day=20) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")),
                (start.replace(day=20).strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d"))
            ])
            start = (month_end + datetime.timedelta(days=1))
        return dates

# TIF Downloader class
class TifDownloader:
    def __init__(self, image_source: ImageSource, start_date: str, end_date: str):
        self.image_source = image_source
        self.start_date = start_date
        self.end_date = end_date
        self.drive_folder = self.get_drive_folder()
        self.shapefile_table = self.get_shapefile_table()
        self.task_count = 0
        self.pending_tasks = []

    def get_drive_folder(self):
        task_data = read_task_yaml()
        if isinstance(self.image_source, NICFISource):
            return task_data['nicfi_folder_name'] if is_production() else task_data['dev_test_folder_name']
        elif isinstance(self.image_source, SentinelSource):
            return task_data['sentinel_folder_name'] if is_production() else task_data['dev_test_folder_name']
        else:
            raise ValueError("Unknown image source type")

    def get_shapefile_table(self):
        shapefile_table = ee.FeatureCollection(SHARED_ASSETS_ID)
        print(f"The shapefile table has {shapefile_table.size().getInfo()} features")
        return shapefile_table

    def process_index(self, index: int, start_date: str, end_date: str):
        feature = self.shapefile_table.filter(ee.Filter.eq('Index', index)).first()
        area_info = self.get_area_info(index, feature)
        print(f"Processing Index {index}: {area_info}")
        if index in TARGET_INDEX_LIST:
            collection = self.image_source.get_collection(start_date, end_date)
            self.export_tif_for_index(index, feature, collection, start_date, end_date)

    def get_area_info(self, index: int, feature: ee.Feature) -> str:
        size = feature.geometry().area().getInfo()
        df = pd.read_csv(SHAPEFILE_DATA_PATH)
        area_value = df.loc[df['Index'] == index, 'AREA_HA'].values[0]
        return f"Size: {size} sq meters, Area: {area_value} hectares"

    def export_tif_image_dynamic_size(self, ind, feature, image, date_str, source_name, shape_size):
        if shape_size < 4:
            exportSizeSqMeters = 5 * 10000
        else:
            exportSizeSqMeters = shape_size * 10000 * 2

        centroid = feature.geometry().centroid()
        halfSideLength = (exportSizeSqMeters ** 0.5) / 2
        exportRegion = centroid.buffer(halfSideLength).bounds()

        res_scale = 5 if source_name == "nicfi" else 10

        # for nicfi the date_str should be the YYYY-MM format, for sentinel the date_str should be the YYYYMMDD format
        if source_name == "nicfi":
            date_str = date_str[:7]
        else:
            date_str = date_str[:4] + date_str[5:7] + date_str[8:]  

        # export the image to the drive
        task = ee.batch.Export.image.toDrive(
            image=image.clip(exportRegion),
            description=f"export_{ind}_{date_str}",
            folder=self.drive_folder,
            region=exportRegion,
            scale=res_scale,
            crs='EPSG:4326',
            maxPixels=1e13,
            fileNamePrefix=f"{ind}-{date_str}-{source_name}"
        )
        self.pending_tasks.append(task)
        self.task_count += 1
        print(f"Export task created for index {ind} with date {date_str}")

    def export_tif_for_index(self, index: int, feature: ee.Feature, collection: ee.ImageCollection, start_date: str, end_date: str):
        df = pd.read_csv(SHAPEFILE_DATA_PATH)
        shape_size = df.loc[df['Index'] == index, 'AREA_HA'].values[0]
        
        image = collection.median()  # or any other reduction you prefer
        date_str = start_date
        source_name = "nicfi" if isinstance(self.image_source, NICFISource) else "sentinel"
        
        self.export_tif_image_dynamic_size(index, feature, image, date_str, source_name, shape_size)

    def wait_for_tasks_completion(self):
        while self.pending_tasks:
            time.sleep(TASK_CHECK_INTERVAL)
            completed_tasks = []
            for task in self.pending_tasks:
                status = task.status()['state']
                if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
                    completed_tasks.append(task)
                    self.task_count -= 1
                    print(f"Task {task.id} {status}")
            self.pending_tasks = [task for task in self.pending_tasks if task not in completed_tasks]

    def start_pending_tasks(self):
        while self.pending_tasks and self.task_count < MAX_CONCURRENT_TASKS:
            task = self.pending_tasks.pop(0)
            task.start()
            print(f"Started task {task.id}")

    def is_ee_tasklist_clear(self):
        tasks = ee.batch.Task.list()
        return all(task.state not in ['READY', 'RUNNING'] for task in tasks)



    def download_all(self):
        source_name = "nicfi" if isinstance(self.image_source, NICFISource) else "sentinel"
        print(f"Starting TIF file download for all target indices, source: {source_name}, folder: {self.drive_folder}, period {self.start_date} to {self.end_date}: {datetime.datetime.now()}")
        
        for start_date, end_date in self.image_source.get_export_dates(self.start_date, self.end_date):
            for index in TARGET_INDEX_LIST:
                self.process_index(index, start_date, end_date)
                
                if self.task_count >= MAX_CONCURRENT_TASKS:
                    self.wait_for_tasks_completion()
                
                self.start_pending_tasks()
        
        # Wait for all remaining tasks to complete
        self.wait_for_tasks_completion()

    def download_single(self, index: int):
        source_name = "nicfi" if isinstance(self.image_source, NICFISource) else "sentinel"
        print(f"Starting TIF file download for index {index}, source: {source_name}, period {self.start_date} to {self.end_date}: {datetime.datetime.now()}")
        
        for start_date, end_date in self.image_source.get_export_dates(self.start_date, self.end_date):
            self.process_index(index, start_date, end_date)
            
            if self.task_count >= MAX_CONCURRENT_TASKS:
                self.wait_for_tasks_completion()
            
            self.start_pending_tasks()
        
        # Wait for all remaining tasks to complete
        self.wait_for_tasks_completion()




# download the tif file for the given index, start date and end date
def download_tif_file_by_index(index: int, source_type: str, start_date: str, end_date: str):
    # parameter: 
    # index: the index of the shapefile
    # start_date: the start date of the period to download, format: YYYY-MM-DD
    # end_date: the end date of the period to download, format: YYYY-MM-DD

    # get the image source
    image_source = get_image_source(source_type)

    # initialize the ee
    initialize_ee()

    # create the downloader
    downloader = TifDownloader(image_source, start_date, end_date)

    collection_size = image_source.get_collection(start_date, end_date).size().getInfo()
    if collection_size == 0:
        print(f"No images found for {source_type} in the date range {start_date} to {end_date}.")
        return
    
    if not downloader.is_ee_tasklist_clear():
        print("There are still running or waiting tasks in Earth Engine. Please wait for them to complete before starting a new download.")
        return

    print(f"Found {collection_size} images for {source_type} in the date range {start_date} to {end_date}. Starting download...")
    downloader.download_single(index)






# download the tif file for the given source type, start date and end date download all the images in the date range
def download_tif_file(source_type: str, start_date: str, end_date: str):
    initialize_ee()  # Initialize Earth Engine once at the start

    image_source = get_image_source(source_type)
    collection = image_source.get_collection(start_date, end_date)
    
    # Check if the collection has any images
    collection_size = collection.size().getInfo()
    if collection_size == 0:
        print(f"No images found for {source_type} in the date range {start_date} to {end_date}.")
        return

    downloader = TifDownloader(image_source, start_date, end_date)
    
    if not downloader.is_ee_tasklist_clear():
        print("There are still running or waiting tasks in Earth Engine. Please wait for them to complete before starting a new download.")
        return

    print(f"Found {collection_size} images for {source_type} in the date range {start_date} to {end_date}. Starting download...")
    downloader.download_all()

def get_image_source(source_type: str) -> ImageSource:
    if source_type.lower() == 'nicfi':
        return NICFISource()
    elif source_type.lower() == 'sentinel':
        return SentinelSource()
    else:
        raise ValueError(f"Unsupported source type: {source_type}")


def cancel_all_ee_tasks():
    tasks = ee.batch.Task.list()
    for task in tasks:
        task.cancel()
        print(f"Cancelled task {task.id}")



def schedule_task_download_last_month():
    # get the last month date
    last_month = datetime.datetime.now() - datetime.timedelta(days=30)
    start_date = last_month.strftime("%Y-%m-%d")
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # check the nicfi soucre have the new date range image or not
    nicfi_source = NICFISource()
    collection = nicfi_source.get_collection(start_date, end_date)
    if collection.size().getInfo() == 0:
        print(f"No new images found for the date range {start_date} to {end_date}")
        return
    
    # download the new images
    download_tif_file('nicfi', start_date, end_date)

    



def main():
    pass

if __name__ == "__main__":
    main()
