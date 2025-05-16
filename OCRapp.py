import tkinter as tk
from tkinter import scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD
import pytesseract
from PIL import Image, ImageTk
import os
import platform
import pyperclip
import time
# from settings import save_settings, load_settings, apply_settings, settings
import settings
import ctx_ui
import ui_ops

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = 'Z:\\dev\\vcpkg\\installed\\x64-windows-static\\tools\\tesseract\\tesseract.exe'

image_load_time = 0.0
image_resize_time = 0.0
image_ocr_time = 0.0
image_file_name = ""
extracted_text = ""
error_message = ""

def on_file_select(event):
    """Handles file selection from the listbox."""
    selection = file_listbox.curselection()
    if not selection:
        return
        
    filename = file_listbox.get(selection[0])
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
        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, directory)
        ui_ops.refresh_file_list()
        
        # Select the file in the listbox
        filename = os.path.basename(file_path)
        for i in range(file_listbox.size()):
            if file_listbox.get(i) == filename:
                file_listbox.selection_clear(0, tk.END)
                file_listbox.selection_set(i)
                file_listbox.see(i)
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
        window.update_idletasks()
        display_image()
        
        # Set the loaded image path
        loaded_image_path = file_path
        
        # Automatically process the image for OCR
        process_image()
    except Exception as e:
        error_message = f"Error loading image: {e}"
        show_status()
        image_label.config(image=None)
        image_label.image = None
        original_image = None

def handle_drop(event):
    """
    Handles files dropped onto the application.
    Extracts the file path from the drop event and loads the image.
    """
    global error_message

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
        load_image(file_path)
    else:
        error_message = "Dropped file is not a supported image format"

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
        # Start timing for resize operation
        start_time = time.time()
        
        # Get current display area dimensions
        display_width = image_label.winfo_width()
        display_height = image_label.winfo_height()
        
        # Use default dimensions if the widget hasn't been rendered yet
        if display_width <= 1:
            display_width = 300
        if display_height <= 1:
            display_height = 300
            
        # Check if dimensions have changed enough to warrant a resize
        # Small changes (less than 5 pixels) don't trigger a resize to improve performance
        if not force and (abs(display_width - last_display_width) < 5 and 
            abs(display_height - last_display_height) < 5 and 
            hasattr(image_label, 'image') and 
            image_label.image is not None):
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
        image_label.config(image=photo)
        image_label.image = photo  # Keep a reference to prevent garbage collection
        
        # Calculate resize time
        image_resize_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        if force:
            # For forced updates, keep the existing status message
            pass
        else:
            # Update status label with dimensions info and timing
            show_status()
            
    except Exception as e:
        status_label.config(text=f"Error displaying image: {e}")
        image_label.config(image=None)
        image_label.image = None

def show_status():
    """
    Displays the current status and statistics of the image processing.
    Shows error information or the time taken for loading, resizing, and OCR processing.
    """
    global image_load_time, image_resize_time, image_ocr_time, loaded_image_path
    
    stats = "";
    
    if(image_file_name != ""):
        stats += f"Image [{image_file_name}] loaded in {image_load_time:.2f}ms | Resized: {image_resize_time:.2f}ms | OCR: {image_ocr_time:.2f}ms - {len(extracted_text)} characters"
    
    if error_message:
        stats = f"Error: {error_message}"
    
    if stats != "":
        status_label.config(text=stats)


def process_image():
    """
    Processes the loaded image using OCR.
    Extracts the text from the image and displays it in the text area.
    Handles potential errors during the OCR process.
    Includes timing information for the OCR processing.
    """
    global original_image, extracted_text, image_ocr_time, image_file_name, loaded_image_path
    
    if not loaded_image_path or not original_image:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, "Please select an image first.")
        return

    # Start timing for OCR processing
    start_time = time.time()
    
    try:
        # Perform OCR on the image using pytesseract
        extracted_text = pytesseract.image_to_string(original_image)
        
        # Calculate OCR processing time
        image_ocr_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Clear previous text and insert the new extracted text
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, extracted_text)
        
        # Update status with file name and timing information
        image_file_name = os.path.basename(loaded_image_path)
        show_status()
    except FileNotFoundError:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, "Error: Image file not found.")
        show_status()
    except Exception as e:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, f"Error during OCR processing: {e}")
        show_status()

def reformat_text(text):
    """
    Reformat text to ensure only one space exists between words.
    """
    # Split text into lines
    words = text.split()
    
    # Process each line to normalize whitespace
    normalized_words = []
    for word in words:
        if word in [',', ':', '.', ';'] and len(normalized_words) > 0:
            normalized_words[-1] += word
        else:
            normalized_words.append(word)
    
    # Join lines back with newlines
    return ' '.join(normalized_words)

# Function to copy selected text to clipboard
def copy_to_clipboard():
    """Copy selected text to clipboard, or all text if none selected."""
    try:
        selected_text = text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
    except tk.TclError:  # No selection
        selected_text = text_output.get("1.0", tk.END)
    
    if selected_text:
        # Apply reformatting if the option is checked
        if reformat_lines_var.get():
            selected_text = reformat_text(selected_text)
        
        pyperclip.copy(selected_text)
        status_label.config(text="Text copied to clipboard.")
    else:
        status_label.config(text="No text to copy.")

# Function to delete the current image file
def delete_image():
    """Delete the current image file from storage."""
    global loaded_image_path, original_image, last_display_width, last_display_height
    
    if not loaded_image_path or not os.path.exists(loaded_image_path):
        status_label.config(text="No valid image to delete.")
        return
    
    try:
        os.remove(loaded_image_path)
        status_label.config(text=f"Image deleted: {loaded_image_path}")
        
        # Remove from listbox
        filename = os.path.basename(loaded_image_path)
        for i in range(file_listbox.size()):
            if file_listbox.get(i) == filename:
                file_listbox.delete(i)
                break
        
        # Clear the UI elements
        text_output.delete("1.0", tk.END)
        image_label.config(image=None)
        image_label.image = None
        
        # Reset cache variables
        loaded_image_path = ""
        original_image = None
        last_display_width = 0
        last_display_height = 0
    except Exception as e:
        status_label.config(text=f"Error deleting image: {e}")

# Function to handle text selection
def on_text_selection(event):
    """Copy selected text to clipboard when text is selected and checkbox is checked"""
    if copy_on_select_var.get():
        try:
            selected_text = text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                # Apply reformatting if the option is checked
                if reformat_lines_var.get():
                    selected_text = reformat_text(selected_text)
                
                pyperclip.copy(selected_text)
                status_label.config(text="Selected text copied to clipboard.")
        except tk.TclError:  # No selection
            pass  # Do nothing if no text is selected

ctx_ui.refresh_file_list = ui_ops.refresh_file_list

# Create the main window
ctx_ui.window = window = TkinterDnD.Tk()
window.title("Tess-a-shot")

# Load settings before configuring the UI
settings.load(settings.settings)
settings.current_directory = settings.settings["last_directory"]

# Global variables for caching
last_display_width = 0
last_display_height = 0
loaded_image_path = ""
original_image = None
last_resize_time = 0
resize_delay = 300  # Milliseconds

# Create main frame to organize the layout
ctx_ui.main_frame = main_frame = tk.Frame(ctx_ui.window)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Create a PanedWindow for resizable frames (left/right split)
main_paned_window = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, sashwidth=5, sashrelief=tk.RAISED)
main_paned_window.pack(fill=tk.BOTH, expand=True)

# Create left frame for file list
ctx_ui.left_frame = left_frame = tk.Frame(main_paned_window)

# Create right frame for image preview and text output
ctx_ui.right_frame = right_frame = tk.Frame(main_paned_window)

# Add the frames to the main paned window
main_paned_window.add(left_frame, width=250)  # Default width for file list
main_paned_window.add(right_frame, width=650)  # Default width for preview/text

# Create a vertical PanedWindow for the right frame (preview/text split)
right_paned_window = tk.PanedWindow(right_frame, orient=tk.VERTICAL, sashwidth=5, sashrelief=tk.RAISED)
right_paned_window.pack(fill=tk.BOTH, expand=True)

# Create frames for the right paned window
ctx_ui.image_preview_frame = image_preview_frame = tk.Frame(right_paned_window)
ctx_ui.text_output_frame = text_output_frame = tk.Frame(right_paned_window)

# Add the frames to the right paned window
right_paned_window.add(image_preview_frame, height=300)  # Default height for preview
right_paned_window.add(text_output_frame, height=300)    # Default height for text

# Top controls frame
controls_frame = tk.Frame(window)
controls_frame.pack(fill=tk.X, pady=(10, 0))

# Label and entry for directory path
label_directory = tk.Label(controls_frame, text="Directory:")
label_directory.pack(side=tk.LEFT, padx=(10, 5))

ctx_ui.directory_entry = directory_entry = tk.Entry(controls_frame, width=50)
directory_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

# Button to select directory
button_select_directory = tk.Button(controls_frame, text="Browse...", command=ui_ops.select_directory)
button_select_directory.pack(side=tk.LEFT, padx=5)

# Button to refresh file list
button_refresh = tk.Button(controls_frame, text="Refresh", command=ui_ops.refresh_file_list)
button_refresh.pack(side=tk.LEFT, padx=5)

# Left Frame Components (File List)
file_list_label = tk.Label(left_frame, text="Image Files:")
file_list_label.pack(pady=(0, 5), anchor=tk.W)

# Create scrollable listbox for files
file_list_frame = tk.Frame(left_frame)
file_list_frame.pack(fill=tk.BOTH, expand=True)

ctx_ui.file_listbox = file_listbox = tk.Listbox(file_list_frame, selectmode=tk.SINGLE, exportselection=0)
file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

file_scrollbar = tk.Scrollbar(file_list_frame, orient=tk.VERTICAL, command=file_listbox.yview)
file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
file_listbox.config(yscrollcommand=file_scrollbar.set)

# Bind file selection event
file_listbox.bind('<<ListboxSelect>>', on_file_select)

# Right Frame - Image Preview Components
image_frame_label = tk.Label(image_preview_frame, text="Image Preview:")
image_frame_label.pack(pady=(0, 5), anchor=tk.W)

image_label = tk.Label(image_preview_frame, bg="lightgray")
image_label.pack(fill=tk.BOTH, expand=True)

# Make image_label a drop target
image_label.drop_target_register(DND_FILES)
image_label.dnd_bind("<<Drop>>", handle_drop)

# Right Frame - Text Output Components
text_output_controls = tk.Frame(text_output_frame)
text_output_controls.pack(fill=tk.X, pady=(0, 5))

text_label = tk.Label(text_output_controls, text="Extracted Text:")
text_label.pack(side=tk.LEFT, pady=(0, 5))

# Add buttons for text operations
button_copy = tk.Button(text_output_controls, text="Copy Text", command=copy_to_clipboard)
button_copy.pack(side=tk.RIGHT, padx=5)

button_delete = tk.Button(text_output_controls, text="Delete Image File", command=delete_image, bg="#ffcccc")
button_delete.pack(side=tk.RIGHT, padx=5)

# Add checkboxes in a horizontal frame
checkboxes_frame = tk.Frame(text_output_frame)
checkboxes_frame.pack(anchor=tk.W, pady=(0, 5), fill=tk.X)

# "Copy text on select" checkbox
ctx_ui.copy_on_select_var = copy_on_select_var = tk.BooleanVar()
copy_on_select_checkbox = tk.Checkbutton(checkboxes_frame, text="Copy text on select", variable=copy_on_select_var)
copy_on_select_checkbox.pack(side=tk.LEFT, padx=(0, 10))

# "Reformat copied lines" checkbox
ctx_ui.reformat_lines_var = reformat_lines_var = tk.BooleanVar()
reformat_lines_checkbox = tk.Checkbutton(checkboxes_frame, text="Reformat copied lines", variable=reformat_lines_var)
reformat_lines_checkbox.pack(side=tk.LEFT)

# Text output area
text_output = scrolledtext.ScrolledText(text_output_frame)
text_output.pack(fill=tk.BOTH, expand=True)

# Bind the text selection event to the text_output widget
text_output.bind("<<Selection>>", on_text_selection)

# Status bar at the bottom
ctx_ui.status_label = status_label = tk.Label(window, text="No image loaded", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

# Override the on_resize function to include the PanedWindow
def on_resize(event):
    """
    Handle window resize events with throttling to prevent performance issues.
    Only triggers image resize when the window size has stabilized.
    """
    global last_resize_time
    
    # Skip events from widgets other than the main window
    if event.widget != window:
        return
        
    # Get current time
    current_time = time.time() * 1000  # Convert to milliseconds
    
    # Cancel any pending resize tasks
    try:
        window.after_cancel(window._resize_job)
    except (AttributeError, tk.TclError):
        pass
    
    # Schedule a new resize task with delay
    window._resize_job = window.after(resize_delay, display_image)

# Bind the resize event to the window
window.bind("<Configure>", on_resize)

# Set initial sash position based on settings
def set_initial_sash_positions():
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    
    if window_width > 1 and window_height > 1:  # Ensure window has been drawn
        # Set main paned window sash position
        left_width = int(window_width * settings.settings["pane_ratio"])
        main_paned_window.sash_place(0, left_width, 0)
        
        # Set right paned window sash position
        right_height = int(window_height * settings.settings["right_pane_ratio"])
        right_paned_window.sash_place(0, 0, right_height)
        
        window.after_cancel(set_sash_job)

# Save settings on window close
def on_closing():
    settings.save(ctx_ui)
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)

# Apply saved settings
settings.apply(ctx_ui)

# Schedule the sash position setting after the window is drawn
set_sash_job = window.after(100, set_initial_sash_positions)

# Run the application
window.mainloop()
