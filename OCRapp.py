import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD
import pytesseract
from PIL import Image, ImageTk
import os
import platform
import pyperclip
import time

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = 'Z:\\dev\\vcpkg\\installed\\x64-windows-static\\tools\\tesseract\\tesseract.exe'

image_load_time = 0.0
image_resize_time = 0.0
image_ocr_time = 0.0
image_file_name = ""
extracted_text = ""
error_message = ""

def select_image():
    """
    Opens a file dialog to select an image file.
    Delegates image loading to the load_image function.
    If no file is selected, it returns without doing anything.
    """
    
    file_path = filedialog.askopenfilename()
    if not file_path:
        return
    load_image(file_path) 

def load_image(file_path):
    """
    Loads an image from the specified file path, updates the UI, and processes the image for OCR.
    """
    global loaded_image_path, original_image, image_load_time

    entry_image_path.delete(0, tk.END)
    entry_image_path.insert(0, file_path)
    
    # Reset cache variables
    loaded_image_path = file_path
    
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
    Processes the image selected in the entry widget using OCR.
    Extracts the text from the image and displays it in the text area.
    Handles potential errors during the OCR process.
    Includes timing information for the OCR processing.
    """
    global original_image, extracted_text, image_ocr_time, image_file_name
    
    image_path = entry_image_path.get()
    if not image_path:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, "Please select an image first.")
        return

    # Start timing for OCR processing
    start_time = time.time()
    
    try:
        # Use the cached original image if available
        if original_image is None:
            original_image = Image.open(image_path)
            
        # Perform OCR on the image using pytesseract
        extracted_text = pytesseract.image_to_string(original_image)
        
        # Calculate OCR processing time
        image_ocr_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Clear previous text and insert the new extracted text
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, extracted_text)
        
        # Update status with file name and timing information
        image_file_name = loaded_image_path.split('/')[-1]
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

# Create the main window
window = TkinterDnD.Tk()
window.title("Tess-a-shot")
window.geometry("800x600")

# Global variables for caching
last_display_width = 0
last_display_height = 0
loaded_image_path = ""
original_image = None
last_resize_time = 0
resize_delay = 300  # Milliseconds

# Create main frame to organize the layout
main_frame = tk.Frame(window)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Create a PanedWindow for resizable frames
paned_window = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, sashwidth=5, sashrelief=tk.RAISED)
paned_window.pack(fill=tk.BOTH, expand=True)

# Create left frame for image
left_frame = tk.Frame(paned_window)
left_frame.drop_target_register(DND_FILES)
left_frame.dnd_bind("<<Drop>>", handle_drop)

# Create right frame for text output
right_frame = tk.Frame(paned_window)

# Add the frames to the paned window
paned_window.add(left_frame, width=400)  # Default width
paned_window.add(right_frame, width=400)  # Default width

# Top controls frame
controls_frame = tk.Frame(window)
controls_frame.pack(fill=tk.X, pady=(10, 0))

# Label and entry for image path
label_image_path = tk.Label(controls_frame, text="Image Path:")
label_image_path.pack(side=tk.LEFT, padx=(10, 5))

entry_image_path = tk.Entry(controls_frame, width=40)
entry_image_path.pack(side=tk.LEFT, padx=5)

# Button to select image
button_select_image = tk.Button(controls_frame, text="Select Image", command=select_image)
button_select_image.pack(side=tk.LEFT, padx=5)

# Add buttons frame for text operations
buttons_frame = tk.Frame(window)
buttons_frame.pack(fill=tk.X, pady=5)

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
    
    image_path = entry_image_path.get()
    if not image_path or not os.path.exists(image_path):
        status_label.config(text="No valid image to delete.")
        return
    
    try:
        os.remove(image_path)
        status_label.config(text=f"Image deleted: {image_path}")
        
        # Clear the UI elements
        entry_image_path.delete(0, tk.END)
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

# Copy button
button_copy = tk.Button(buttons_frame, text="Copy Text", command=copy_to_clipboard)
button_copy.pack(side=tk.LEFT, padx=10)

# Delete button
button_delete = tk.Button(buttons_frame, text="Delete Image File", command=delete_image, bg="#ffcccc")
button_delete.pack(side=tk.LEFT, padx=10)

# Status label
status_label = tk.Label(window, text="No image loaded", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

# Image display area (left side)
image_frame_label = tk.Label(left_frame, text="Image Preview:")
image_frame_label.pack(pady=(0, 5), anchor=tk.W)

image_label = tk.Label(left_frame, bg="lightgray", width=40, height=15)
image_label.pack(fill=tk.BOTH, expand=True)

# Text output area (right side)
text_label = tk.Label(right_frame, text="Extracted Text:")
text_label.pack(pady=(0, 5), anchor=tk.W)

# Add checkboxes in a horizontal frame
checkboxes_frame = tk.Frame(right_frame)
checkboxes_frame.pack(anchor=tk.W, pady=(0, 5), fill=tk.X)

# "Copy text on select" checkbox
copy_on_select_var = tk.BooleanVar()
copy_on_select_checkbox = tk.Checkbutton(checkboxes_frame, text="Copy text on select", variable=copy_on_select_var)
copy_on_select_checkbox.pack(side=tk.LEFT, padx=(0, 10))

# "Reformat copied lines" checkbox
reformat_lines_var = tk.BooleanVar()
reformat_lines_checkbox = tk.Checkbutton(checkboxes_frame, text="Reformat copied lines", variable=reformat_lines_var)
reformat_lines_checkbox.pack(side=tk.LEFT)

text_output = scrolledtext.ScrolledText(right_frame, width=40, height=15)
text_output.pack(fill=tk.BOTH, expand=True)

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

# Bind the text selection event to the text_output widget
text_output.bind("<<Selection>>", on_text_selection)

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

# Set initial sash position to 50% of the window width
def set_initial_sash_position():
    window_width = window.winfo_width()
    if window_width > 1:  # Ensure window has been drawn
        paned_window.sash_place(0, window_width // 2, 0)
        window.after_cancel(set_sash_job)

# Schedule the sash position setting after the window is drawn
set_sash_job = window.after(100, set_initial_sash_position)

# Run the application
window.mainloop()