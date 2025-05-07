import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
import pytesseract
from PIL import Image

def select_image():
    """
    Opens a file dialog to select an image file.
    Sets the selected file path to the entry widget.
    """
    file_path = filedialog.askopenfilename()
    entry_image_path.delete(0, tk.END)
    entry_image_path.insert(0, file_path)

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
    except FileNotFoundError:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, "Error: Image file not found.")
    except Exception as e:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, f"Error during OCR processing: {e}")

# Create the main window
window = tk.Tk()
window.title("Simple OCR Application")
window.geometry("400x400")  # Increased height for text area

# Label and entry for image path
label_image_path = tk.Label(window, text="Image Path:")
label_image_path.pack(pady=(10, 0))  # Added padding

entry_image_path = tk.Entry(window, width=40)
entry_image_path.pack()

# Button to select image
button_select_image = tk.Button(window, text="Select Image", command=select_image)
button_select_image.pack(pady=5)

# Button to process image
button_process_image = tk.Button(window, text="Process Image", command=process_image)
button_process_image.pack(pady=5)

# Text area for output
label_output = tk.Label(window, text="Extracted Text:") #Added a label for the text area
label_output.pack(pady=(10,0))
text_output = scrolledtext.ScrolledText(window, width=40, height=10)
text_output.pack(pady=5)

# Run the application
window.mainloop()

