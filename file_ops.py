# file_ops.py
import os
import tkinter as tk

def select_directory(filedialog, directory_entry, current_directory, refresh_file_list):
    directory_path = filedialog.askdirectory()
    if not directory_path:
        return current_directory
    current_directory = directory_path
    directory_entry.delete(0, tk.END)
    directory_entry.insert(0, directory_path)
    refresh_file_list()
    return current_directory

def refresh_file_list(current_directory, file_listbox, status_label):
    file_listbox.delete(0, tk.END)
    if not current_directory or not os.path.exists(current_directory):
        return
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif')
    try:
        files = [f for f in os.listdir(current_directory)
                if os.path.isfile(os.path.join(current_directory, f))
                and f.lower().endswith(image_extensions)]
        files.sort()
        for file in files:
            file_listbox.insert(tk.END, file)
        status_label.config(text=f"Found {len(files)} image files in {current_directory}")
    except Exception as e:
        status_label.config(text=f"Error reading directory: {e}")

def delete_image(loaded_image_path, file_listbox, text_output, image_label, status_label):
    import os
    if not loaded_image_path or not os.path.exists(loaded_image_path):
        status_label.config(text="No valid image to delete.")
        return False
    try:
        os.remove(loaded_image_path)
        status_label.config(text=f"Image deleted: {loaded_image_path}")
        filename = os.path.basename(loaded_image_path)
        for i in range(file_listbox.size()):
            if file_listbox.get(i) == filename:
                file_listbox.delete(i)
                break
        text_output.delete("1.0", tk.END)
        image_label.config(image=None)
        image_label.image = None
        return True
    except Exception as e:
        status_label.config(text=f"Error deleting image: {e}")
        return False
