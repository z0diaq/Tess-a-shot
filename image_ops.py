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
extracted_text = ""
last_resize_time = 0

# Variables for region selection
selection_start_x = 0
selection_start_y = 0
selection_rect = None
selection_coords = [0, 0, 0, 0]  # [x1, y1, x2, y2] in original image coordinates

img_resized = None
display_scale_factor = (1, 1)  # (width_scale, height_scale)
selection_canvas = None

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

        # Reset or adjust selection coordinates for the new image
        if not ctx_ui.remember_region_var.get() or selection_coords == [0, 0, 0, 0]:
            # If not remembering region or if no region was selected, set to full image
            width, height = original_image.size
            selection_coords = [0, 0, width, height]
        else:
            # Ensure coordinates don't go beyond the new image boundaries
            adjust_selection_to_image_bounds()
        
        # Update the display and force a refresh
        ctx_ui.window.update_idletasks()
        display_image()
        
        # Set the loaded image path
        loaded_image_path = file_path
        
        # Automatically process the image for OCR
        process_image()
    except Exception as e:
        ui_ops.set_status(f"Error loading image: {e}")
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
    global last_display_width, last_display_height, original_image, loaded_image_path, image_resize_time, display_scale_factor
    
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
        ui_ops.set_status(f"Error displaying image: {e}")
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
    
    if not loaded_image_path or not original_image or selection_coords == [0, 0, 0, 0]:
        ctx_ui.text_output.delete("1.0", tk.END)
        ctx_ui.text_output.insert(tk.END, "Please select an image first.")
        return

    # Start timing for OCR processing
    start_time = time.time()
    
    try:
        # Extract the selected region from the original image
        x1, y1, x2, y2 = selection_coords
        region_width = x2 - x1
        region_height = y2 - y1
        
        # Crop the image to the selected region
        region_image = original_image.crop((x1, y1, x2, y2))
        
        # Perform OCR on the selected region using pytesseract
        extracted_text = pytesseract.image_to_string(region_image)
        
        # Calculate OCR processing time
        image_ocr_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Clear previous text and insert the new extracted text
        ctx_ui.text_output.delete("1.0", tk.END)
        ctx_ui.text_output.insert(tk.END, extracted_text)
        
        # TODO: add status message about region based processing

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
        ui_ops.set_status("No valid image to delete.")
        return
    
    try:
        os.remove(loaded_image_path)
        ui_ops.set_status(f"Image deleted: {loaded_image_path}")
        
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
        ui_ops.set_status(f"Error deleting image: {e}")

def adjust_selection_to_image_bounds():
    """
    Adjusts the selection coordinates to ensure they stay within the image boundaries.
    """

    if original_image is None:
        return
        
    width, height = original_image.size
    selection_coords[0] = max(0, min(selection_coords[0], width - 1))
    selection_coords[1] = max(0, min(selection_coords[1], height - 1))
    selection_coords[2] = max(selection_coords[0] + 1, min(selection_coords[2], width))
    selection_coords[3] = max(selection_coords[1] + 1, min(selection_coords[3], height))

def update_selection_rectangle():
    """
    Updates the selection rectangle on the canvas to match the current selection coordinates.
    """
    global selection_coords, display_scale_factor, selection_rect, selection_canvas
    
    if original_image is None:
        return
    
    # If canvas doesn't exist yet, create it
    if not hasattr(ctx_ui.image_label, 'selection_canvas'):
        create_selection_canvas()
        return
    
    # Convert original image coordinates to display coordinates
    x1 = int(selection_coords[0] * display_scale_factor[0])
    y1 = int(selection_coords[1] * display_scale_factor[1])
    x2 = int(selection_coords[2] * display_scale_factor[0])
    y2 = int(selection_coords[3] * display_scale_factor[1])
    
    # Update or create the selection rectangle
    if selection_rect:
        selection_canvas.coords(selection_rect, x1, y1, x2, y2)
    else:
        selection_rect = selection_canvas.create_rectangle(
            x1, y1, x2, y2, 
            outline="blue", 
            width=2,
            dash=(5, 5)
        )

def create_selection_canvas():
    """
    Creates a transparent canvas over the image label for drawing the selection rectangle.
    """
    global selection_canvas, selection_rect
    
    # Create a canvas that overlays the image label
    selection_canvas = tk.Canvas(
        ctx_ui.image_preview_frame, 
        highlightthickness=0,
        bg="systemTransparent"  # Transparent background
    )
    selection_canvas.place(
        x=ctx_ui.image_label.winfo_x(),
        y=ctx_ui.image_label.winfo_y(),
        width=ctx_ui.image_label.winfo_width(),
        height=ctx_ui.image_label.winfo_height()
    )
    
    # Store canvas in image_label for easy access
    ctx_ui.image_label.selection_canvas = selection_canvas
    
    # Set up mouse event bindings for selection
    selection_canvas.bind("<ButtonPress-1>", on_selection_start)
    selection_canvas.bind("<B1-Motion>", on_selection_motion)
    selection_canvas.bind("<ButtonRelease-1>", on_selection_end)

def on_selection_start(event):
    """Handle the start of a rectangle selection."""
    global selection_start_x, selection_start_y, selection_rect
    
    selection_start_x, selection_start_y = event.x, event.y
    
    # Create or update selection rectangle
    if selection_rect:
        selection_canvas.coords(selection_rect, event.x, event.y, event.x, event.y)
    else:
        selection_rect = selection_canvas.create_rectangle(
            event.x, event.y, event.x, event.y, 
            outline="blue", 
            width=2,
            dash=(5, 5)
        )

def on_selection_motion(event):
    """Handle the mouse movement during selection."""
    global selection_rect
    if selection_rect:
        selection_canvas.coords(selection_rect, selection_start_x, selection_start_y, event.x, event.y)

def on_selection_end(event):
    """
    Finalize the selection rectangle and update the selection coordinates.
    Then process the selected region.
    """
    global selection_coords, selection_rect, display_scale_factor
    
    if not selection_rect or not original_image:
        return
    
    # Get the rectangle coordinates in display space
    x1, y1, x2, y2 = selection_canvas.coords(selection_rect)
    
    # Ensure x1 < x2 and y1 < y2
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    
    # Convert display coordinates back to original image coordinates
    orig_x1 = int(x1 / display_scale_factor[0])
    orig_y1 = int(y1 / display_scale_factor[1])
    orig_x2 = int(x2 / display_scale_factor[0])
    orig_y2 = int(y2 / display_scale_factor[1])
    
    # Ensure coordinates are within image bounds
    width, height = original_image.size
    orig_x1 = max(0, min(orig_x1, width - 1))
    orig_y1 = max(0, min(orig_y1, height - 1))
    orig_x2 = max(orig_x1 + 1, min(orig_x2, width))
    orig_y2 = max(orig_y1 + 1, min(orig_y2, height))
    
    # Update selection coordinates
    selection_coords = [orig_x1, orig_y1, orig_x2, orig_y2]
    
    # Update the selection rectangle
    selection_canvas.coords(selection_rect, x1, y1, x2, y2)
    
    # Process the selected region
    process_image()