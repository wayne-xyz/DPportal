from drive_utils import perform_static_data_saving_csv, get_folder_id, search_in_folder, count_files_in_date_folder


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

    print(count_files_in_date_folder("sentinel_tif_2024", '202401'))


if __name__ == "__main__":
    test_count_files_in_date_folder()

