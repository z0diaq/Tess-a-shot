import os
import time
import tkinter as tk
from PIL import Image, ImageTk
import pytesseract
import threading
import pyperclip

import ui_ops
import ctx_ui
import settings
import text_ops

original_image = None
loaded_image_path = None
image_file_name = None
image_load_time = 0
image_resize_time = 0
image_ocr_time = 0
extracted_text = ""
last_resize_time = 0

# Variables for region selection
selection_start_x = 0
selection_start_y = 0
selection_rect = None

img_resized = None
display_scale_factor = (1, 1)  # (width_scale, height_scale)

# For OCR cancellation
ocr_generation = 0
ocr_generation_lock = threading.Lock()

# Zoom and pan variables
zoom_level = 1.0  # Current zoom level
pan_offset_x = 0  # Pan offset in display pixels
pan_offset_y = 0
drag_start_x = 0  # Starting point for drag operation
drag_start_y = 0

def load_image(file_path):
    """
    Loads an image from the specified file path, updates the UI, and processes the image for OCR.
    """
    global loaded_image_path, original_image, image_load_time, image_file_name, selection_rect, zoom_level, pan_offset_x, pan_offset_y
    
    # Reset zoom and pan when loading a new image
    zoom_level = 1.0
    pan_offset_x = 0
    pan_offset_y = 0

    # Update the directory entry if it's from a different directory
    directory = os.path.dirname(file_path)
    if directory != settings.current_directory and os.path.exists(directory):
        settings.current_directory = directory
        ctx_ui.directory_entry.delete(0, tk.END)
        ctx_ui.directory_entry.insert(0, directory)
        ui_ops.refresh_file_list()
        
        # Select the file in the treeview
        filename = os.path.basename(file_path)
        for iid in ctx_ui.file_tree.get_children():
            if ctx_ui.file_tree.item(iid, "values")[0] == filename:
                ctx_ui.file_tree.selection_set(iid)
                ctx_ui.file_tree.see(iid)
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

        ctx_ui.text_output.delete("1.0", tk.END)
        ctx_ui.text_output.insert(tk.END, "Processing image...")
        
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
    global last_display_width, last_display_height, original_image, loaded_image_path, image_resize_time, display_scale_factor, img_resized, selection_rect
    
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
        
        display_scale_factor = (width / new_width, height / new_height)

        # Apply zoom to the dimensions
        zoomed_width = int(new_width * zoom_level)
        zoomed_height = int(new_height * zoom_level)

        # Resize the image with zoom applied
        img_resized = original_image.resize((zoomed_width, zoomed_height), Image.LANCZOS)
        
        # Convert to PhotoImage for Tkinter
        photo = ImageTk.PhotoImage(img_resized)

        canvas_width = ctx_ui.image_canvas.winfo_width()
        canvas_height = ctx_ui.image_canvas.winfo_height()
        
        # Calculate base position (centered)
        base_image_x = (canvas_width - zoomed_width) // 2
        base_image_y = (canvas_height - zoomed_height) // 2
        
        # Apply pan offset
        image_x = base_image_x + pan_offset_x
        image_y = base_image_y + pan_offset_y

        # Clear canvas and redraw image
        ctx_ui.image_canvas.delete("all")
        ctx_ui.image_canvas.photo = photo  # Keep a reference!
        ctx_ui.image_canvas.create_image(image_x, image_y, anchor="nw", image=photo)
        
        # Calculate resize time
        image_resize_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Reset or adjust selection coordinates for the new image
        if not ctx_ui.remember_region_var.get() or settings.selection_coords == [0, 0, 0, 0]:
            # If not remembering region or if no region was selected, set to full image
            text_ops.log(f"Re-setting selection coordinates to full image: {settings.selection_coords}")
            width, height = original_image.size
            settings.selection_coords = [0, 0, width, height]
            selection_rect = None  # Reset selection rectangle reference
        else:
            # Keep the existing selection coordinates (they're in original image space)
            text_ops.log(f"Keeping existing selection coordinates: {settings.selection_coords}")
            # Update the visual selection rectangle to match the stored coordinates
            update_selection_rectangle_from_coords()

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

def update_selection_rectangle_from_coords():
    """
    Creates or updates the selection rectangle on the canvas based on the stored selection coordinates.
    This function converts from original image coordinates to display coordinates.
    """
    global selection_rect, display_scale_factor
    
    if not original_image or settings.selection_coords == [0, 0, 0, 0]:
        return
    
    # Get canvas and image display info
    canvas_width = ctx_ui.image_canvas.winfo_width()
    canvas_height = ctx_ui.image_canvas.winfo_height()
    if img_resized is not None:
        img_width, img_height = img_resized.size
    else:
        return
    
    # Calculate base position (centered)
    base_image_x = (canvas_width - img_width) // 2
    base_image_y = (canvas_height - img_height) // 2
    
    # Apply pan offset
    image_x = base_image_x + pan_offset_x
    image_y = base_image_y + pan_offset_y
    
    # Convert original image coordinates to display coordinates
    orig_x1, orig_y1, orig_x2, orig_y2 = settings.selection_coords
    orig_img_width, orig_img_height = original_image.size
    
    # Scale coordinates to display size
    if orig_img_width > 0 and orig_img_height > 0:
        display_x1 = int((orig_x1 / orig_img_width) * img_width) + image_x
        display_y1 = int((orig_y1 / orig_img_height) * img_height) + image_y
        display_x2 = int((orig_x2 / orig_img_width) * img_width) + image_x
        display_y2 = int((orig_y2 / orig_img_height) * img_height) + image_y

        # Ensure selection rectangle is with image bounds
        display_x1 = max(image_x, min(display_x1, image_x + img_width))
        display_x2 = max(image_x, min(display_x2, image_x + img_width))
        display_y1 = max(image_y, min(display_y1, image_y + img_height))
        display_y2 = max(image_y, min(display_y2, image_y + img_height))
        
        # Create or update the selection rectangle
        if selection_rect:
            ctx_ui.image_canvas.delete(selection_rect)
            
        selection_rect = ctx_ui.image_canvas.create_rectangle(
            display_x1, display_y1, display_x2, display_y2,
            outline='green', width=2, fill='green', stipple='gray50'
        )

        text_ops.log(f"Updated selection rectangle - Original coords: {settings.selection_coords}, Display coords: [{display_x1}, {display_y1}, {display_x2}, {display_y2}]")

def process_image_async():
    """
    Processes the loaded image using OCR in a background thread.
    Cancels previous OCR operation if a new one is started.
    """
    global original_image, extracted_text, image_ocr_time, loaded_image_path, ocr_generation

    with ocr_generation_lock:
        ocr_generation += 1
        my_generation = ocr_generation

    def ocr_task(my_generation):
        if not loaded_image_path or not original_image or settings.selection_coords == [0, 0, 0, 0]:
            if my_generation == ocr_generation:
                ctx_ui.text_output.delete("1.0", tk.END)
                ctx_ui.text_output.insert(tk.END, "Please select an image first.")
            return
        start_time = time.time()
        try:
            x1, y1, x2, y2 = settings.selection_coords
            region_image = original_image.crop((x1, y1, x2, y2))
            result = pytesseract.image_to_string(region_image)
            elapsed = (time.time() - start_time) * 1000
            def update_ui():
                nonlocal result, elapsed
                global extracted_text, image_ocr_time
                if my_generation != ocr_generation:
                    return  # Cancelled
                image_ocr_time = elapsed
                extracted_text = result
                ctx_ui.text_output.delete("1.0", tk.END)
                ctx_ui.text_output.insert(tk.END, result)
                ui_ops.show_status()
                
                # Auto-copy to clipboard if "Copy text on region select" is enabled
                if ctx_ui.copy_on_region_select_var.get() and result:
                    # Apply reformatting if the option is checked
                    text_to_copy = result
                    if ctx_ui.reformat_lines_var.get():
                        text_to_copy = text_ops.reformat_text(text_to_copy)
                    pyperclip.copy(text_to_copy)
                    ui_ops.set_status("Text extracted and copied to clipboard.")
            ctx_ui.window.after(0, update_ui)
        except Exception as e:
            def update_ui_error(e):
                if my_generation != ocr_generation:
                    return  # Cancelled
                ctx_ui.text_output.delete("1.0", tk.END)
                ctx_ui.text_output.insert(tk.END, f"Error during OCR processing: {e}")
                ui_ops.show_status()
            ctx_ui.window.after(0, update_ui_error, e)
    threading.Thread(target=ocr_task, args=(my_generation,), daemon=True).start()

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
        
        # Remove from treeview
        filename = os.path.basename(loaded_image_path)
        next_iid = None
        iids = list(ctx_ui.file_tree.get_children())
        for idx, iid in enumerate(iids):
            if ctx_ui.file_tree.item(iid, "values")[0] == filename:
                ctx_ui.file_tree.delete(iid)
                # Determine next file index
                if len(iids) > 1:
                    if idx < len(iids) - 1:
                        next_iid = iids[idx + 1]
                    elif idx > 0:
                        next_iid = iids[idx - 1]
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

        # Automatically open and process the next file in the list, if any
        if next_iid is not None:
            file_name = ctx_ui.file_tree.item(next_iid, "values")[0]
            ctx_ui.file_tree.selection_set(next_iid)
            ctx_ui.file_tree.see(next_iid)
            next_file_path = os.path.join(settings.current_directory, file_name)
            load_image(next_file_path)
    except Exception as e:
        ui_ops.set_status(f"Error deleting image: {e}")

def update_selection_rectangle():
    """
    Updates the selection coordinates based on the current selection rectangle on the canvas.
    This function converts from display coordinates to original image coordinates.
    """
    global selection_rect, display_scale_factor
    if not selection_rect or not original_image:
        return
        
    # Get canvas size and displayed image size
    canvas_width = ctx_ui.image_canvas.winfo_width()
    canvas_height = ctx_ui.image_canvas.winfo_height()
    if img_resized is not None:
        img_width, img_height = img_resized.size
    else:
        img_width, img_height = canvas_width, canvas_height
    
    # Calculate base position (centered)
    base_image_x = (canvas_width - img_width) // 2
    base_image_y = (canvas_height - img_height) // 2
    
    # Apply pan offset
    image_x = base_image_x + pan_offset_x
    image_y = base_image_y + pan_offset_y
    
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
        orig_x1 = int((rel_x1 / img_width) * original_image.size[0])
        orig_y1 = int((rel_y1 / img_height) * original_image.size[1])
        orig_x2 = int((rel_x2 / img_width) * original_image.size[0])
        orig_y2 = int((rel_y2 / img_height) * original_image.size[1])
    else:
        orig_x1 = orig_y1 = orig_x2 = orig_y2 = 0
    
    # Ensure coordinates are within image bounds
    width, height = original_image.size
    orig_x1 = max(0, min(orig_x1, width - 1))
    orig_y1 = max(0, min(orig_y1, height - 1))
    orig_x2 = max(orig_x1 + 1, min(orig_x2, width))
    orig_y2 = max(orig_y1 + 1, min(orig_y2, height))
    
    # Update selection coordinates
    settings.selection_coords = [orig_x1, orig_y1, orig_x2, orig_y2]
    
    # Update the selection rectangle coordinates on canvas
    ctx_ui.image_canvas.coords(selection_rect, x1, y1, x2, y2)

    # Log new selection coordinates
    text_ops.log(f"Updated selection coordinates: {settings.selection_coords}")
    text_ops.log(f"Canvas coordinates: {ctx_ui.image_canvas.coords(selection_rect)}")

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
        
        # Calculate base position (centered)
        base_image_x = (canvas_width - img_width) // 2
        base_image_y = (canvas_height - img_height) // 2
        
        # Apply pan offset
        image_x = base_image_x + pan_offset_x
        image_y = base_image_y + pan_offset_y
        
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
    update_selection_rectangle()
    # Process the selected region
    process_image_async()

def center_image_on_point(click_x, click_y, current_width, current_height, new_zoom_level):
    """
    Calculate pan offsets to center the image on a specific point after zoom.
    
    Args:
        click_x, click_y: Click coordinates on canvas
        current_width, current_height: Current displayed image dimensions
        new_zoom_level: The zoom level to apply
        
    Returns:
        tuple: (pan_offset_x, pan_offset_y)
    """
    canvas_width = ctx_ui.image_canvas.winfo_width()
    canvas_height = ctx_ui.image_canvas.winfo_height()
    
    # Get current image position
    base_image_x = (canvas_width - current_width) // 2
    base_image_y = (canvas_height - current_height) // 2
    image_x = base_image_x + pan_offset_x
    image_y = base_image_y + pan_offset_y
    
    # Calculate position relative to current image
    rel_x = click_x - image_x
    rel_y = click_y - image_y
    
    # Calculate new image dimensions after zoom
    width, height = original_image.size
    if width / height > canvas_width / canvas_height:
        new_width = canvas_width
        new_height = int(height * (canvas_width / width))
    else:
        new_height = canvas_height
        new_width = int(width * (canvas_height / height))
    
    zoomed_width = int(new_width * new_zoom_level)
    zoomed_height = int(new_height * new_zoom_level)
    
    # Calculate the ratio of where the click was in the current image
    if current_width > 0 and current_height > 0:
        click_ratio_x = rel_x / current_width
        click_ratio_y = rel_y / current_height
    else:
        click_ratio_x = 0.5
        click_ratio_y = 0.5
    
    # Calculate where that point is in the new zoomed image
    new_point_x = click_ratio_x * zoomed_width
    new_point_y = click_ratio_y * zoomed_height
    
    # Center the canvas on the click position
    canvas_center_x = canvas_width // 2
    canvas_center_y = canvas_height // 2
    
    # Calculate new pan offset to center on click point
    base_new_image_x = (canvas_width - zoomed_width) // 2
    base_new_image_y = (canvas_height - zoomed_height) // 2
    
    new_pan_x = canvas_center_x - base_new_image_x - new_point_x
    new_pan_y = canvas_center_y - base_new_image_y - new_point_y
    
    return (new_pan_x, new_pan_y)

def zoom_in_at_point(event):
    """Zoom in by 1.5x and center on the click position."""
    global zoom_level, pan_offset_x, pan_offset_y
    
    if not original_image or img_resized is None:
        return
    
    current_width, current_height = img_resized.size
    
    # Apply zoom
    zoom_level *= 1.5
    
    # Calculate new pan offsets to center on click point
    pan_offset_x, pan_offset_y = center_image_on_point(
        event.x, event.y, current_width, current_height, zoom_level
    )
    
    # Redraw the image
    display_image(force=True)

def zoom_out_at_point(event):
    """Zoom out by 1.5x and center on the click position."""
    global zoom_level, pan_offset_x, pan_offset_y
    
    if not original_image or img_resized is None:
        return
    
    current_width, current_height = img_resized.size
    
    # Apply zoom
    zoom_level /= 1.5
    
    # Don't zoom out beyond 1.0
    if zoom_level < 1.0:
        zoom_level = 1.0
        pan_offset_x = 0
        pan_offset_y = 0
    else:
        # Calculate new pan offsets to center on click point
        pan_offset_x, pan_offset_y = center_image_on_point(
            event.x, event.y, current_width, current_height, zoom_level
        )
    
    # Redraw the image
    display_image(force=True)

def on_drag_start(event):
    """Start dragging the image."""
    global drag_start_x, drag_start_y
    drag_start_x = event.x
    drag_start_y = event.y

def on_drag_motion(event):
    """Handle image dragging."""
    global pan_offset_x, pan_offset_y, drag_start_x, drag_start_y
    
    if not original_image:
        return
    
    # Calculate drag delta
    delta_x = event.x - drag_start_x
    delta_y = event.y - drag_start_y
    
    # Update pan offset
    pan_offset_x += delta_x
    pan_offset_y += delta_y
    
    # Update drag start position
    drag_start_x = event.x
    drag_start_y = event.y
    
    # Redraw the image
    display_image(force=True)

def on_drag_end(event):
    """End dragging the image."""
    pass  # Nothing special to do on drag end

def on_mouse_press(event):
    """Route mouse press event based on interaction mode."""
    # Don't handle mouse events if context menu is active
    if ctx_ui.context_menu_active:
        return
    
    mode = ctx_ui.interaction_mode
    
    if mode == "area_selection":
        on_selection_start(event)
    elif mode == "drag":
        on_drag_start(event)
    elif mode == "zoom_in":
        zoom_in_at_point(event)
    elif mode == "zoom_out":
        zoom_out_at_point(event)
    else:
        # Default to area selection
        on_selection_start(event)

def on_mouse_motion(event):
    """Route mouse motion event based on interaction mode."""
    mode = ctx_ui.interaction_mode
    
    if mode == "area_selection":
        on_selection_motion(event)
    elif mode == "drag":
        on_drag_motion(event)
    # zoom_in and zoom_out don't have motion handlers

def on_mouse_release(event):
    """Route mouse release event based on interaction mode."""
    mode = ctx_ui.interaction_mode
    
    if mode == "area_selection":
        on_selection_end(event)
    elif mode == "drag":
        on_drag_end(event)
    # zoom_in and zoom_out don't have release handlers
