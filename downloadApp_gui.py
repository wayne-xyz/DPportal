import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry  # You'll need to install this: pip install tkcalendar
from update_task import download_tif_file
from datetime import datetime
import logging

class DownloadApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TIF Downloader")
        self.root.geometry("400x300")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Source Type Selection
        ttk.Label(main_frame, text="Source Type:").grid(row=0, column=0, pady=5, sticky=tk.W)
        self.source_type = ttk.Combobox(main_frame, values=['nicfi', 'sentinel'])
        self.source_type.grid(row=0, column=1, pady=5, padx=5)
        self.source_type.set('nicfi')  # default value
        
        # Date Selection
        ttk.Label(main_frame, text="Start Date:").grid(row=1, column=0, pady=5, sticky=tk.W)
        self.start_date = DateEntry(main_frame, width=20, date_pattern='yyyy-mm-dd')
        self.start_date.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(main_frame, text="End Date:").grid(row=2, column=0, pady=5, sticky=tk.W)
        self.end_date = DateEntry(main_frame, width=20, date_pattern='yyyy-mm-dd')
        self.end_date.grid(row=2, column=1, pady=5, padx=5)
        
        # Download Button
        self.download_btn = ttk.Button(main_frame, text="Download", command=self.start_download)
        self.download_btn.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Status Label
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, length=300, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=2, pady=5)
    
    def start_download(self):
        try:
            # Get values
            source = self.source_type.get()
            start = self.start_date.get_date().strftime('%Y-%m-%d')
            end = self.end_date.get_date().strftime('%Y-%m-%d')
            
            # Validate dates
            if datetime.strptime(end, '%Y-%m-%d') <= datetime.strptime(start, '%Y-%m-%d'):
                self.status_var.set("Error: End date must be after start date")
                return
            
            # Update UI
            self.status_var.set("Downloading...")
            self.download_btn.state(['disabled'])
            self.progress.start()
            
            # Start download in a separate thread to prevent UI freezing
            import threading
            thread = threading.Thread(target=self.perform_download, args=(source, start, end))
            thread.start()
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            self.download_btn.state(['!disabled'])
            self.progress.stop()
    
    def perform_download(self, source, start, end):
        try:
            # Perform download
            download_tif_file(source, start, end)
            
            # Update UI on completion
            self.root.after(0, self.download_complete, "Download tif tasks from Earth Engine submmited successfully!")
            
        except Exception as e:
            # Update UI on error
            self.root.after(0, self.download_complete, f"Error: {str(e)}")
    
    def download_complete(self, message):
        self.status_var.set(message)
        self.download_btn.state(['!disabled'])
        self.progress.stop()

def main():
    root = tk.Tk()
    app = DownloadApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
