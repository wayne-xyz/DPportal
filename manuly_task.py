from update_task import initialize_ee,download_tif_file_by_index


def main():
    initialize_ee()
    download_tif_file_by_index(133,'nicfi', '2024-10-01', '2024-11-01')
    download_tif_file_by_index(133,'sentinel', '2024-10-01', '2024-11-01')


