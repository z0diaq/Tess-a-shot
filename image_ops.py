import os
import time
import tkinter as tk
from PIL import Image, ImageTk
import pytesseract

import ui_ops
import ctx_ui
import settings

original_image = None
loaded_image_path = None
image_load_time = 0
image_resize_time = 0
image_ocr_time = 0
image_file_name = None
extracted_text = None

def on_file_select(event):
    """Handles file selection from the listbox."""
    selection = ctx_ui.file_listbox.curselection()
    if not selection:
        return
        
    filename = ctx_ui.file_listbox.get(selection[0])
    file_path = os.path.join(settings.current_directory, filename)
    
    # Load the selected image
    load_image(file_path)

def load_image(file_path):
    """
    Loads an image from the specified file path, updates the UI, and processes the image for OCR.
    """
    global loaded_image_path, original_image, image_load_time

    # Update the directory entry if it's from a different directory
    directory = os.path.dirname(file_path)
    if directory != settings.current_directory and os.path.exists(directory):
        settings.current_directory = directory
        ctx_ui.directory_entry.delete(0, tk.END)
        ctx_ui.directory_entry.insert(0, directory)
        ui_ops.refresh_file_list()
        
        # Select the file in the listbox
        filename = os.path.basename(file_path)
        for i in range(ctx_ui.file_listbox.size()):
            if ctx_ui.file_listbox.get(i) == filename:
                ctx_ui.file_listbox.selection_clear(0, tk.END)
                ctx_ui.file_listbox.selection_set(i)
                ctx_ui.file_listbox.see(i)
                break
    
    # Start timing for image loading
    start_time = time.time()
    
    try:
        original_image = Image.open(file_path)
        
        # Force display update immediately
        # First reset dimensions to force redraw
        global last_display_width, last_display_height
        last_display_width = 0
        last_display_height = 0
        
        # Calculate loading time
        image_load_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Update the display and force a refresh
        ctx_ui.window.update_idletasks()
        display_image()
        
        # Set the loaded image path
        loaded_image_path = file_path
        
        # Automatically process the image for OCR
        process_image()
    except Exception as e:
        ui_ops.on_error(f"Error loading image: {e}")
        ctx_ui.image_label.config(image=None)
        ctx_ui.image_label.image = None
        original_image = None

def display_image(force=False):
    """
    Displays the cached original image in the image_label.
    Dynamically resizes the image to fit the available display area while maintaining aspect ratio.
    Uses caching to prevent unnecessary resizing operations.
    
    Args:
        force (bool): If True, forces the image to be redrawn regardless of dimension changes
    """
    global last_display_width, last_display_height, original_image, loaded_image_path, image_resize_time
    
    if original_image is None:
        return
        
    try:
        ui_ops.clear_error()
        
        # Start timing for resize operation
        start_time = time.time()
        
        # Get current display area dimensions
        display_width = ctx_ui.image_label.winfo_width()
        display_height = ctx_ui.image_label.winfo_height()
        
        # Use default dimensions if the widget hasn't been rendered yet
        if display_width <= 1:
            display_width = 300
        if display_height <= 1:
            display_height = 300
            
        # Check if dimensions have changed enough to warrant a resize
        # Small changes (less than 5 pixels) don't trigger a resize to improve performance
        if not force and (abs(display_width - last_display_width) < 5 and 
            abs(display_height - last_display_height) < 5 and 
            hasattr(ctx_ui.image_label, 'image') and 
            ctx_ui.image_label.image is not None):
            return
            
        # Update cached dimensions
        last_display_width = display_width
        last_display_height = display_height
        
        # Get original image dimensions
        width, height = original_image.size
        
        # Calculate the new dimensions to fit the display area
        # while maintaining the aspect ratio
        if width / height > display_width / display_height:
            # Image is wider than the display area (relative to height)
            new_width = display_width
            new_height = int(height * (display_width / width))
        else:
            # Image is taller than the display area (relative to width)
            new_height = display_height
            new_width = int(width * (display_height / height))
        
        # Resize the image
        img_resized = original_image.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to PhotoImage for Tkinter
        photo = ImageTk.PhotoImage(img_resized)
        
        # Update the image label
        ctx_ui.image_label.config(image=photo)
        ctx_ui.image_label.image = photo  # Keep a reference to prevent garbage collection
        
        # Calculate resize time
        image_resize_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        if force:
            # For forced updates, keep the existing status message
            pass
        else:
            # Update status label with dimensions info and timing
            ui_ops.show_status()
            
    except Exception as e:
        ui_ops.on_error(f"Error displaying image: {e}")
        ctx_ui.image_label.config(text=f"Error displaying image: {e}")
        ctx_ui.image_label.config(image=None)
        ctx_ui.image_label.image = None

def process_image():
    """
    Processes the loaded image using OCR.
    Extracts the text from the image and displays it in the text area.
    Handles potential errors during the OCR process.
    Includes timing information for the OCR processing.
    """
    global original_image, extracted_text, image_ocr_time, image_file_name, loaded_image_path

    ui_ops.clear_error()
    
    if not loaded_image_path or not original_image:
        ctx_ui.text_output.delete("1.0", tk.END)
        ctx_ui.text_output.insert(tk.END, "Please select an image first.")
        return

    # Start timing for OCR processing
    start_time = time.time()
    
    try:
        # Perform OCR on the image using pytesseract
        extracted_text = pytesseract.image_to_string(original_image)
        
        # Calculate OCR processing time
        image_ocr_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Clear previous text and insert the new extracted text
        ctx_ui.text_output.delete("1.0", tk.END)
        ctx_ui.text_output.insert(tk.END, extracted_text)
        
        # Update status with file name and timing information
        image_file_name = os.path.basename(loaded_image_path)
        ui_ops.show_status()
    except FileNotFoundError:
        ctx_ui.text_output.delete("1.0", tk.END)
        ctx_ui.text_output.insert(tk.END, "Error: Image file not found.")
        ui_ops.show_status()
    except Exception as e:
        ctx_ui.text_output.delete("1.0", tk.END)
        ctx_ui.text_output.insert(tk.END, f"Error during OCR processing: {e}")
        ui_ops.show_status()

# Function to delete the current image file
def delete_image():
    """Delete the current image file from storage."""
    global loaded_image_path, original_image, last_display_width, last_display_height
    
    if not loaded_image_path or not os.path.exists(loaded_image_path):
        ui_ops.on_error("No valid image to delete.")
        return
    
    try:
        os.remove(loaded_image_path)
        ui_ops.on_error(f"Image deleted: {loaded_image_path}")
        
        # Remove from listbox
        filename = os.path.basename(loaded_image_path)
        for i in range(ctx_ui.file_listbox.size()):
            if ctx_ui.file_listbox.get(i) == filename:
                ctx_ui.file_listbox.delete(i)
                break
        
        # Clear the UI elements
        ctx_ui.text_output.delete("1.0", tk.END)
        ctx_ui.image_label.config(image=None)
        ctx_ui.image_label.image = None
        
        # Reset cache variables
        loaded_image_path = ""
        original_image = None
        last_display_width = 0
        last_display_height = 0
    except Exception as e:
        ui_ops.on_error(f"Error deleting image: {e}")
