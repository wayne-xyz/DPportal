from drive_utils import perform_static_data_saving_csv, get_folder_id, search_in_folder, count_files_in_date_folder
import time

from update_task import initialize_ee,download_tif_file_by_index


# how to run the test
# python3 test.py

def main():
    initialize_ee()
    download_tif_file_by_index(133,'nicfi', '2024-10-01', '2024-11-01')
    download_tif_file_by_index(133,'sentinel', '2024-10-01', '2024-11-01')




if __name__ == "__main__":
    main()