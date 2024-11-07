#  using the downloadApp_gui.py as template to create a new gui for downloading one file by index
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry  # You'll need to install this: pip install tkcalendar
from update_task import download_tif_file_by_index
from tkinter import messagebox

class DownloadOneApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Download One File by Index")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Source Name
        ttk.Label(main_frame, text="Source Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.source_name = ttk.Combobox(main_frame, width=27, state='readonly')
        self.source_name['values'] = ('sentinel', 'nicfi')
        self.source_name.current(0)  # Set default to first option
        self.source_name.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Index
        ttk.Label(main_frame, text="Index:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.index = ttk.Entry(main_frame, width=30)
        self.index.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Date Range
        ttk.Label(main_frame, text="Date Range:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Start Date
        ttk.Label(main_frame, text="From:").grid(row=2, column=1, sticky=tk.W, pady=5)
        self.start_date = DateEntry(main_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2)
        self.start_date.grid(row=2, column=2, sticky=tk.W, pady=5)
        
        # End Date
        ttk.Label(main_frame, text="To:").grid(row=3, column=1, sticky=tk.W, pady=5)
        self.end_date = DateEntry(main_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2)
        self.end_date.grid(row=3, column=2, sticky=tk.W, pady=5)
        
        # Download Button
        self.download_button = ttk.Button(main_frame, text="Download",
                                        command=self.download_file)
        self.download_button.grid(row=4, column=0, columnspan=3, pady=20)
        
    def download_file(self):
        source = self.source_name.get()
        index = self.index.get()
        start_date = self.start_date.get_date().strftime('%Y-%m-%d')
        end_date = self.end_date.get_date().strftime('%Y-%m-%d')
        
        try:
            print(f"Downloading file with index: {index}, source: {source}, start_date: {start_date}, end_date: {end_date}")
            download_tif_file_by_index(index, source, start_date, end_date)
            messagebox.showinfo("Success", "File downloaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download file: {str(e)}")

def main():
    root = tk.Tk()
    app = DownloadOneApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
