# image_ocr.py
import os
import time
from PIL import Image, ImageTk
import pytesseract
import tkinter as tk

def load_image(file_path, directory_entry, current_directory, file_listbox, window, display_image, process_image, image_label):
    directory = os.path.dirname(file_path)
    if directory != current_directory and os.path.exists(directory):
        current_directory = directory
        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, directory)
        # refresh_file_list() should be called by the caller if needed
        filename = os.path.basename(file_path)
        for i in range(file_listbox.size()):
            if file_listbox.get(i) == filename:
                file_listbox.selection_clear(0, tk.END)
                file_listbox.selection_set(i)
                file_listbox.see(i)
                break
    start_time = time.time()
    try:
        original_image = Image.open(file_path)
        last_display_width = 0
        last_display_height = 0
        image_load_time = (time.time() - start_time) * 1000
        window.update_idletasks()
        display_image()
        loaded_image_path = file_path
        process_image()
        return original_image, loaded_image_path, image_load_time
    except Exception as e:
        image_label.config(image=None)
        image_label.image = None
        return None, '', 0

def display_image(original_image, image_label, last_display_width, last_display_height, force=False):
    if original_image is None:
        return last_display_width, last_display_height, 0
    try:
        start_time = time.time()
        display_width = image_label.winfo_width()
        display_height = image_label.winfo_height()
        if display_width <= 1:
            display_width = 300
        if display_height <= 1:
            display_height = 300
        if not force and (abs(display_width - last_display_width) < 5 and abs(display_height - last_display_height) < 5 and hasattr(image_label, 'image') and image_label.image is not None):
            return last_display_width, last_display_height, 0
        last_display_width = display_width
        last_display_height = display_height
        width, height = original_image.size
        if width / height > display_width / display_height:
            new_width = display_width
            new_height = int(height * (display_width / width))
        else:
            new_height = display_height
            new_width = int(width * (display_height / height))
        img_resized = original_image.resize((new_width, new_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img_resized)
        image_label.config(image=photo)
        image_label.image = photo
        image_resize_time = (time.time() - start_time) * 1000
        return last_display_width, last_display_height, image_resize_time
    except Exception:
        image_label.config(image=None)
        image_label.image = None
        return last_display_width, last_display_height, 0

def process_image(original_image, loaded_image_path, text_output, status_label):
    if not loaded_image_path or not original_image:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, "Please select an image first.")
        return '', 0
    start_time = time.time()
    try:
        extracted_text = pytesseract.image_to_string(original_image)
        image_ocr_time = (time.time() - start_time) * 1000
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, extracted_text)
        return extracted_text, image_ocr_time
    except Exception as e:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, f"Error during OCR processing: {e}")
        return '', 0

def reformat_text(text):
    words = text.split()
    normalized_words = []
    for word in words:
        if word in [',', ':', '.', ';'] and len(normalized_words) > 0:
            normalized_words[-1] += word
        else:
            normalized_words.append(word)
    return ' '.join(normalized_words)
