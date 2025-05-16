from tkinter import filedialog, END
import os

import settings
import ctx_ui

def select_directory():
    """Opens a file dialog to select a directory."""
    
    directory_path = filedialog.askdirectory()
    if not directory_path:
        return
        
    settings.current_directory = directory_path
    ctx_ui.directory_entry.delete(0, END)
    ctx_ui.directory_entry.insert(0, directory_path)
    
    # Update the file list
    refresh_file_list()

def refresh_file_list():
    """Refreshes the file list based on the current directory."""
    
    # Clear the current file list
    ctx_ui.file_listbox.delete(0, END)
    
    if not settings.current_directory or not os.path.exists(settings.current_directory):
        return
    
    # Get all image files in the directory
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif')
    try:
        files = [f for f in os.listdir(settings.current_directory) 
                if os.path.isfile(os.path.join(settings.current_directory, f)) 
                and f.lower().endswith(image_extensions)]
        
        # Sort files alphabetically
        files.sort()
        
        # Add files to the listbox
        for file in files:
            ctx_ui.file_listbox.insert(END, file)
            
        # Update status
        ctx_ui.status_label.config(text=f"Found {len(files)} image files in {settings.current_directory}")
    except Exception as e:
        ctx_ui.status_label.config(text=f"Error reading directory: {e}")

def on_file_select(event):
    """Handles file selection from the listbox."""
    selection = ctx_ui.file_listbox.curselection()
    if not selection:
        return
        
    filename = ctx_ui.file_listbox.get(selection[0])
    file_path = os.path.join(settings.current_directory, filename)
    
    # Load the selected image
    load_image(file_path)
