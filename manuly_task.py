from update_task import download_tif_file_by_index ,schedule_task_download_last_month, cancel_all_ee_tasks,download_tif_file
import time
from datetime import datetime, timedelta
#  set to the folder name in the drive
default_folder = 'dev_test' 

pendding_list=[133,1130,1317,1264,572,139]


def download_by_index(index:int,source_type:str,start_date:str,end_date:str):
    download_tif_file_by_index(index,source_type,start_date,end_date)



def main():
    download_tif_file( 'nicfi', '2024-08-01', '2024-09-01')



if __name__ == "__main__":
    main()


