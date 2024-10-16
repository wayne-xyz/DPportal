from drive_utils import perform_static_data_saving_csv, get_folder_id, search_in_folder, count_files_in_date_folder
import time

from update_task import test_ee_connection,test_export_tif_image_dynamic_size,monthly_task,nicfi_image_collection_by_month,get_nicfi_image_by_month,initialize_ee,get_feature_by_index


# how to run the test
# python3 test.py



#  write the test for the perform_static_data_saving_csv function
def test_perform_static_data_saving_csv():
    perform_static_data_saving_csv()

def test_search_in_folder():
    folder_id = get_folder_id('EsriWorldImagery_jpg')
    print(folder_id)
    print(search_in_folder(folder_id, '1822'))

def test_count_files_in_date_folder():
    #  get the function running time
    start_time = time.time()
    print(count_files_in_date_folder("sentinel_tif_2024", "202401"))
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")

def test_ee():
    test_ee_connection()

def test_export():
    test_export_tif_image_dynamic_size()

def test_nicfi_image_collection_by_month():
    nicfi_image_collection_by_month('2024-09')


if __name__ == "__main__":

    initialize_ee()
    get_feature_by_index(133)
