from drive_utils import perform_static_data_saving_csv, get_folder_id, search_in_folder, count_files_in_date_folder
import time

from update_task import initialize_ee,download_tif_file_by_index

def test_static_data():
    perform_static_data_saving_csv()

# how to run the test
# python3 test.py

def main():
    initialize_ee()
    test_static_data()





if __name__ == "__main__":
    main()