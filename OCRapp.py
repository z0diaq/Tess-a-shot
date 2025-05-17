import tkinter as tk
from tkinter import scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD
import pytesseract
import os
import platform
import pyperclip
import time
# from settings import save_settings, load_settings, apply_settings, settings
import settings
import ctx_ui
import ui_ops
import file_ops
import image_ops

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = 'Z:\\dev\\vcpkg\\installed\\x64-windows-static\\tools\\tesseract\\tesseract.exe'

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
        ui_ops.error_message = "Dropped file is not a supported image format"


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
        selected_text = ctx_ui.text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
    except tk.TclError:  # No selection
        selected_text = ctx_ui.text_output.get("1.0", tk.END)
    
    if selected_text:
        # Apply reformatting if the option is checked
        if reformat_lines_var.get():
            selected_text = reformat_text(selected_text)
        
        pyperclip.copy(selected_text)
        status_label.config(text="Text copied to clipboard.")
    else:
        status_label.config(text="No text to copy.")

# Function to handle text selection
def on_text_selection(event):
    """Copy selected text to clipboard when text is selected and checkbox is checked"""
    if copy_on_select_var.get():
        try:
            selected_text = ctx_ui.text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
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
file_listbox.bind('<<ListboxSelect>>', file_ops.on_file_select)

# Right Frame - Image Preview Components
image_frame_label = tk.Label(image_preview_frame, text="Image Preview:")
image_frame_label.pack(pady=(0, 5), anchor=tk.W)

ctx_ui.image_label = tk.Label(image_preview_frame, bg="lightgray")
ctx_ui.image_label.pack(fill=tk.BOTH, expand=True)

# Make image_label a drop target
ctx_ui.image_label.drop_target_register(DND_FILES)
ctx_ui.image_label.dnd_bind("<<Drop>>", handle_drop)

# Right Frame - Text Output Components
text_output_controls = tk.Frame(text_output_frame)
text_output_controls.pack(fill=tk.X, pady=(0, 5))

text_label = tk.Label(text_output_controls, text="Extracted Text:")
text_label.pack(side=tk.LEFT, pady=(0, 5))

# Add buttons for text operations
button_copy = tk.Button(text_output_controls, text="Copy Text", command=copy_to_clipboard)
button_copy.pack(side=tk.RIGHT, padx=5)

button_delete = tk.Button(text_output_controls, text="Delete Image File", command=image_ops.delete_image, bg="#ffcccc")
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
ctx_ui.text_output = scrolledtext.ScrolledText(text_output_frame)
ctx_ui.text_output.pack(fill=tk.BOTH, expand=True)

# Bind the text selection event to the text_output widget
ctx_ui.text_output.bind("<<Selection>>", on_text_selection)

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
    window._resize_job = window.after(resize_delay, image_ops.display_image)

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
