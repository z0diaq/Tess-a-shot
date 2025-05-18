from tkinter import filedialog
import tkinter as tk
import os
import time

import settings
import ctx_ui
import image_ops

status_message = ""

resize_delay = 300  # Milliseconds


def on_file_select(event):
    """Handles file selection from the listbox."""
    selection = ctx_ui.file_listbox.curselection()
    if not selection:
        return
        
    filename = ctx_ui.file_listbox.get(selection[0])
    file_path = os.path.join(settings.current_directory, filename)
    
    # Load the selected image
    image_ops.load_image(file_path)

def handle_drop(event):
    """
    Handles files dropped onto the application.
    Extracts the file path from the drop event and loads the image.
    """
    # Get the file path from the drop event
    file_path = event.data
    
    # Remove curly braces if present (Windows drag and drop format)
    if file_path.startswith("{") and file_path.endswith("}"):
        file_path = file_path[1:-1]
    
    # Remove quotes if present
    if file_path.startswith('"') and file_path.endswith('"'):
        file_path = file_path[1:-1]
    
    # Check if it's an image file (simple check, could be expanded)
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
    if any(file_path.lower().endswith(ext) for ext in image_extensions):
        image_ops.load_image(file_path)
    else:
        set_status("Dropped file is not a supported image format")

def select_directory():
    """Opens a file dialog to select a directory."""
    
    directory_path = filedialog.askdirectory()
    if not directory_path:
        return
        
    settings.current_directory = directory_path
    ctx_ui.directory_entry.delete(0, tk.END)
    ctx_ui.directory_entry.insert(0, directory_path)
    
    # Update the file list
    refresh_file_list()

def refresh_file_list():
    """Refreshes the file list based on the current directory."""
    
    # Clear the current file list
    ctx_ui.file_listbox.delete(0, tk.END)
    
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
            ctx_ui.file_listbox.insert(tk.END, file)
            
        # Update status
        set_status(f"Found {len(files)} image files in {settings.current_directory}")
    except Exception as e:
        set_status(f"Error reading directory: {e}")

def set_status(message):
    """
    Handles errors by displaying an error message in the status label.
    """
    global status_message
    status_message = message
    ctx_ui.status_label.config(text=status_message)

def clear_error():
    """
    Clears the error message.
    """
    global status_message
    status_message = ""
    ctx_ui.status_label.config(text="")

def show_status():
    """
    Displays the current status and statistics of the image processing.
    Shows error information or the time taken for loading, resizing, and OCR processing.
    """
   
    stats = "";
    
    if(image_ops.image_file_name != ""):
        stats += f"Image [{image_ops.image_file_name}] loaded in {image_ops.image_load_time:.2f}ms | Resized: {image_ops.image_resize_time:.2f}ms | OCR: {image_ops.image_ocr_time:.2f}ms - {len(image_ops.extracted_text)} characters"
    
    if status_message:
        stats = f"Error: {status_message}"
    
    if stats != "":
        ctx_ui.status_label.config(text=stats)

# Override the on_resize function to include the PanedWindow
def on_resize(event):
    """
    Handle window resize events with throttling to prevent performance issues.
    Only triggers image resize when the window size has stabilized.
    """
    global last_resize_time
    
    # Skip events from widgets other than the main window
    if event.widget != ctx_ui.window:
        return
        
    # Get current time
    current_time = time.time() * 1000  # Convert to milliseconds
    
    # Cancel any pending resize tasks
    try:
        ctx_ui.window.after_cancel(ctx_ui.window._resize_job)
    except (AttributeError, tk.TclError):
        pass
    
    # Schedule a new resize task with delay
    ctx_ui.window._resize_job = ctx_ui.window.after(resize_delay, image_ops.display_image)

def on_right_pane_drag(event):
    # Cancel any pending resize tasks
    try:
        ctx_ui.window.after_cancel(ctx_ui.window._resize_job)
    except (AttributeError, tk.TclError):
        pass

    ctx_ui.window._resize_job = ctx_ui.window.after(resize_delay, image_ops.display_image)

# Set initial sash position based on settings
def set_initial_sash_positions():
    window_width = ctx_ui.window.winfo_width()
    window_height = ctx_ui.window.winfo_height()
    
    if window_width > 1 and window_height > 1:  # Ensure window has been drawn
        # Set main paned window sash position
        left_width = int(window_width * settings.settings["pane_ratio"])
        ctx_ui.main_paned_window.sash_place(0, left_width, 0)
        
        # Set right paned window sash position
        right_height = int(window_height * settings.settings["right_pane_ratio"])
        ctx_ui.right_paned_window.sash_place(0, 0, right_height)
        
        if ctx_ui.set_sash_job:
            ctx_ui.window.after_cancel(ctx_ui.set_sash_job)

# Save settings on window close
def on_closing():
    settings.save(ctx_ui)
    ctx_ui.window.destroy()
