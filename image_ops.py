import os
import time
import tkinter as tk
from PIL import Image, ImageTk
import pytesseract
import threading

import ui_ops
import ctx_ui
import settings
import text_ops

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

def load_image(file_path):
    """
    Loads an image from the specified file path, updates the UI, and processes the image for OCR.
    """
    global loaded_image_path, original_image, image_load_time, selection_coords, image_file_name, selection_rect

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
        image_file_name = os.path.basename(file_path)
        
        # Automatically process the image for OCR
        process_image_async()
    except Exception as e:
        ui_ops.set_status(f"Error loading image: {e}")
        ctx_ui.image_canvas.photo = None  # Clear the reference to avoid memory leaks
        ctx_ui.image_canvas.delete("all")  # Clear the canvas
        original_image = None

def display_image(force=False):
    """
    Displays the cached original image in the image_label.
    Dynamically resizes the image to fit the available display area while maintaining aspect ratio.
    Uses caching to prevent unnecessary resizing operations.
    
    Args:
        force (bool): If True, forces the image to be redrawn regardless of dimension changes
    """
    global last_display_width, last_display_height, original_image, loaded_image_path, image_resize_time, display_scale_factor, img_resized, selection_coords, selection_rect
    
    if original_image is None:
        return
        
    try:
        ui_ops.clear_error()
        # Start timing for resize operation
        start_time = time.time()
        
        # Get current display area dimensions
        display_width = ctx_ui.image_canvas.winfo_width()
        display_height = ctx_ui.image_canvas.winfo_height()
        text_ops.log(f"Display area: {display_width}x{display_height}")
        
        # Use default dimensions if the widget hasn't been rendered yet
        if display_width <= 1:
            display_width = 300
        if display_height <= 1:
            display_height = 300
            
        # Check if dimensions have changed enough to warrant a resize
        # Small changes (less than 5 pixels) don't trigger a resize to improve performance
        if not force and hasattr(ctx_ui.image_canvas, 'photo') and (abs(display_width - last_display_width) < 5 and 
            abs(display_height - last_display_height) < 5 ):
            return
            
        # Update cached dimensions
        last_display_width = display_width
        last_display_height = display_height
        
        # Get original image dimensions
        width, height = original_image.size
        text_ops.log(f"Original image size: {width}x{height}")
        
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

        canvas_width = ctx_ui.image_canvas.winfo_width()
        image_x = (canvas_width - new_width) // 2
        image_y = 0  # Top-aligned;

        ctx_ui.image_canvas.photo = photo  # Keep a reference!
        ctx_ui.image_canvas.create_image(image_x, image_y, anchor="nw", image=photo)
        
        # Calculate resize time
        image_resize_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        if selection_rect:
            ctx_ui.image_canvas.tag_raise(selection_rect)

        # Reset or adjust selection coordinates for the new image
        ''' WIP: remeber region
        if not ctx_ui.remember_region_var.get() or selection_coords == [0, 0, 0, 0]:
            # If not remembering region or if no region was selected, set to full image
            text_ops.log(f"Re-setting selection coordinates to full image: {selection_coords}")
            width, height = original_image.size
            selection_coords = [0, 0, width, height]
            if selection_rect:
                ctx_ui.image_canvas.delete(selection_rect)
                selection_rect = None  # Reset selection rectangle
        else:
            # Ensure coordinates don't go beyond the new image boundaries
            text_ops.log(f"Adjusting selection coordinates: {selection_coords}")
            adjust_selection_to_image_bounds()
        '''
        width, height = original_image.size
        selection_coords = [0, 0, width, height]
        if selection_rect:
            ctx_ui.image_canvas.delete(selection_rect)
            selection_rect = None  # Reset selection rectangle

        if force:
            # For forced updates, keep the existing status message
            pass
        else:
            # Update status label with dimensions info and timing
            ui_ops.show_status()
            
    except Exception as e:
        ui_ops.set_status(f"Error displaying image: {e}")
        ctx_ui.image_canvas.photo = None  # Clear the reference to avoid memory leaks
        ctx_ui.image_canvas.delete("all")  # Clear the canvas

def process_image_async():
    """
    Processes the loaded image using OCR in a background thread.
    Extracts the text from the image and displays it in the text area.
    Handles potential errors during the OCR process.
    Includes timing information for the OCR processing.
    """
    global original_image, extracted_text, image_ocr_time, loaded_image_path

    def ocr_task():
        if not loaded_image_path or not original_image or selection_coords == [0, 0, 0, 0]:
            ctx_ui.text_output.delete("1.0", tk.END)
            ctx_ui.text_output.insert(tk.END, "Please select an image first.")
            return
        start_time = time.time()
        try:
            x1, y1, x2, y2 = selection_coords
            region_image = original_image.crop((x1, y1, x2, y2))
            result = pytesseract.image_to_string(region_image)
            elapsed = (time.time() - start_time) * 1000
            def update_ui():
                nonlocal result, elapsed
                global extracted_text, image_ocr_time
                image_ocr_time = elapsed
                extracted_text = result
                ctx_ui.text_output.delete("1.0", tk.END)
                ctx_ui.text_output.insert(tk.END, result)
                ui_ops.show_status()
            ctx_ui.window.after(0, update_ui)
        except Exception as e:
            def update_ui_error():
                ctx_ui.text_output.delete("1.0", tk.END)
                ctx_ui.text_output.insert(tk.END, f"Error during OCR processing: {e}")
                ui_ops.show_status()
            ctx_ui.window.after(0, update_ui_error)
    threading.Thread(target=ocr_task, daemon=True).start()

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
        ctx_ui.text_output.insert(tk.END, "Image deleted.")
        ctx_ui.image_canvas.delete("all")  # Clear the canvas
        ctx_ui.image_canvas.photo = None  # Clear the reference to avoid memory leaks
        ctx_ui.status_label.config(text="No image loaded")
        
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
    global selection_coords, display_scale_factor, selection_rect
    
    if original_image is None:
        return
        
    # Convert original image coordinates to display coordinates
    x1 = int(selection_coords[0] * display_scale_factor[0])
    y1 = int(selection_coords[1] * display_scale_factor[1])
    x2 = int(selection_coords[2] * display_scale_factor[0])
    y2 = int(selection_coords[3] * display_scale_factor[1])
    
    # Update or create the selection rectangle
    if selection_rect:
        ctx_ui.image_canvas.coords(selection_rect, x1, y1, x2, y2)
    else:
        selection_rect = ctx_ui.image_canvas.create_rectangle(
            x1, y1, x2, y2, 
            outline="blue", 
            width=2,
            dash=(5, 5)
        )

def on_selection_start(event):
    """Handle the start of a rectangle selection."""
    global selection_start_x, selection_start_y, selection_rect
    
    selection_start_x, selection_start_y = event.x, event.y
    
    # Create or update selection rectangle
    if selection_rect:
        ctx_ui.image_canvas.coords(selection_rect, event.x, event.y, event.x, event.y)
    else:
        selection_rect = ctx_ui.image_canvas.create_rectangle(
            event.x, event.y, event.x, event.y, 
            outline='green', width=2, fill='green', stipple='gray50'
        )

def on_selection_motion(event):
    """Handle the mouse movement during selection, constrained to image bounds."""
    global selection_rect
    if selection_rect:
        # Get canvas size and displayed image size
        canvas_width = ctx_ui.image_canvas.winfo_width()
        canvas_height = ctx_ui.image_canvas.winfo_height()
        if img_resized is not None:
            img_width, img_height = img_resized.size
        else:
            img_width, img_height = canvas_width, canvas_height
        # Centered image x offset
        image_x = (canvas_width - img_width) // 2
        image_y = 0  # Top-aligned
        # Constrain mouse to image area
        x = min(max(event.x, image_x), image_x + img_width)
        y = min(max(event.y, image_y), image_y + img_height)
        ctx_ui.image_canvas.tag_raise(selection_rect)
        ctx_ui.image_canvas.coords(selection_rect, selection_start_x, selection_start_y, x, y)

def on_selection_end(event):
    """
    Finalize the selection rectangle and update the selection coordinates.
    Then process the selected region.
    """
    global selection_coords, selection_rect, display_scale_factor
    if not selection_rect or not original_image:
        return
    # Get canvas size and displayed image size
    canvas_width = ctx_ui.image_canvas.winfo_width()
    canvas_height = ctx_ui.image_canvas.winfo_height()
    if img_resized is not None:
        img_width, img_height = img_resized.size
    else:
        img_width, img_height = canvas_width, canvas_height
    image_x = (canvas_width - img_width) // 2
    image_y = 0  # Top-aligned
    # Get the rectangle coordinates in display space
    x1, y1, x2, y2 = ctx_ui.image_canvas.coords(selection_rect)
    # Constrain to image area
    x1 = min(max(x1, image_x), image_x + img_width)
    x2 = min(max(x2, image_x), image_x + img_width)
    y1 = min(max(y1, image_y), image_y + img_height)
    y2 = min(max(y2, image_y), image_y + img_height)
    # Ensure x1 < x2 and y1 < y2
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    # Convert display coordinates back to original image coordinates
    # Adjust for offset and scale
    rel_x1 = x1 - image_x
    rel_y1 = y1 - image_y
    rel_x2 = x2 - image_x
    rel_y2 = y2 - image_y
    if img_width > 0 and img_height > 0:
        orig_x1 = int(rel_x1 * (original_image.size[0] / img_width))
        orig_y1 = int(rel_y1 * (original_image.size[1] / img_height))
        orig_x2 = int(rel_x2 * (original_image.size[0] / img_width))
        orig_y2 = int(rel_y2 * (original_image.size[1] / img_height))
    else:
        orig_x1 = orig_y1 = orig_x2 = orig_y2 = 0
    # Ensure coordinates are within image bounds
    width, height = original_image.size
    orig_x1 = max(0, min(orig_x1, width - 1))
    orig_y1 = max(0, min(orig_y1, height - 1))
    orig_x2 = max(orig_x1 + 1, min(orig_x2, width))
    orig_y2 = max(orig_y1 + 1, min(orig_y2, height))
    # Update selection coordinates
    selection_coords = [orig_x1, orig_y1, orig_x2, orig_y2]
    # Update the selection rectangle
    ctx_ui.image_canvas.coords(selection_rect, x1, y1, x2, y2)
    # Process the selected region
    process_image_async()
