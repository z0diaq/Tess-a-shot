# gui.py
# Entry point for Tess-a-shot GUI application
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog, scrolledtext
from PIL import Image, ImageTk
import time
import os
from settings import load_settings, save_settings, apply_settings
from file_ops import select_directory, refresh_file_list, delete_image
from image_ocr import load_image, display_image, process_image
from text_ops import copy_to_clipboard, on_text_selection

def main():
    window = TkinterDnD.Tk()
    window.title("Tess-a-shot")
    # ...existing code for widget setup, event bindings, and mainloop...
    window.mainloop()

if __name__ == "__main__":
    main()
