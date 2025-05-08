import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
import pytesseract
from PIL import Image, ImageTk

def select_image():
    """
    Opens a file dialog to select an image file.
    Sets the selected file path to the entry widget.
    Displays the selected image in the image_label.
    """
    file_path = filedialog.askopenfilename()
    entry_image_path.delete(0, tk.END)
    entry_image_path.insert(0, file_path)
    if file_path:
        display_image(file_path)

def display_image(image_path):
    """
    Displays the selected image in the image_label.
    Resizes the image to fit the display area while maintaining aspect ratio.
    """
    try:
        # Open the image using PIL
        img = Image.open(image_path)
        
        # Calculate new dimensions to fit in display area while maintaining aspect ratio
        max_width = 300
        max_height = 300
        width, height = img.size
        
        # Calculate the new dimensions
        if width > height:
            new_width = max_width
            new_height = int(height * (max_width / width))
        else:
            new_height = max_height
            new_width = int(width * (max_height / height))
        
        # Resize the image
        img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to PhotoImage for Tkinter
        photo = ImageTk.PhotoImage(img)
        
        # Update the image label
        image_label.config(image=photo)
        image_label.image = photo  # Keep a reference to prevent garbage collection
        
        # Update status label
        status_label.config(text=f"Image loaded: {image_path.split('/')[-1]}")
    except Exception as e:
        status_label.config(text=f"Error loading image: {e}")
        image_label.config(image=None)
        image_label.image = None

def process_image():
    """
    Processes the image selected in the entry widget using OCR.
    Extracts the text from the image and displays it in the text area.
    Handles potential errors during the OCR process.
    """
    image_path = entry_image_path.get()
    if not image_path:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, "Please select an image first.")
        return

    try:
        # Open the image using PIL (Pillow)
        image = Image.open(image_path)
        # Perform OCR on the image using pytesseract
        extracted_text = pytesseract.image_to_string(image)
        # Clear previous text and insert the new extracted text
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, extracted_text)
        status_label.config(text="OCR processing completed.")
    except FileNotFoundError:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, "Error: Image file not found.")
        status_label.config(text="Error: Image file not found.")
    except Exception as e:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, f"Error during OCR processing: {e}")
        status_label.config(text=f"Error during OCR processing: {e}")

# Create the main window
window = tk.Tk()
window.title("OCR Application with Image Preview")
window.geometry("800x600")  # Increased size to accommodate image display

# Create main frame to organize the layout
main_frame = tk.Frame(window)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Create left frame for image
left_frame = tk.Frame(main_frame)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

# Create right frame for text output
right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

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

# Button to process image
button_process_image = tk.Button(controls_frame, text="Process Image", command=process_image)
button_process_image.pack(side=tk.LEFT, padx=5)

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

text_output = scrolledtext.ScrolledText(right_frame, width=40, height=15)
text_output.pack(fill=tk.BOTH, expand=True)

# Run the application
window.mainloop()