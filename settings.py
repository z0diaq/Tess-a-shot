# settings.py
import os
import json
import tkinter as tk

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".tessashot_config.json")
DEFAULT_SETTINGS = {
    "window": {
        "width": 900,
        "height": 700,
        "x": None,
        "y": None
    },
    "pane_ratio": 0.3,
    "right_pane_ratio": 0.5,
    "options": {
        "copy_on_select": False,
        "reformat_lines": False
    },
    "last_directory": ""
}
settings = DEFAULT_SETTINGS.copy()

def save_settings(window, main_frame, left_frame, right_frame, image_preview_frame, copy_on_select_var, reformat_lines_var, current_directory):
    global settings
    settings["window"]["width"] = window.winfo_width()
    settings["window"]["height"] = window.winfo_height()
    settings["window"]["x"] = window.winfo_x()
    settings["window"]["y"] = window.winfo_y()
    if main_frame.winfo_width() > 0:
        settings["pane_ratio"] = left_frame.winfo_width() / main_frame.winfo_width()
    if right_frame.winfo_height() > 0:
        settings["right_pane_ratio"] = image_preview_frame.winfo_height() / right_frame.winfo_height()
    settings["options"]["copy_on_select"] = copy_on_select_var.get()
    settings["options"]["reformat_lines"] = reformat_lines_var.get()
    settings["last_directory"] = current_directory
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_settings():
    global settings
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                loaded_settings = json.load(f)
                settings.update(loaded_settings)
    except Exception as e:
        print(f"Error loading settings: {e}")
    return settings

def apply_settings(window, copy_on_select_var, reformat_lines_var, directory_entry, refresh_file_list, settings, current_directory):
    width = settings["window"]["width"]
    height = settings["window"]["height"]
    x = settings["window"]["x"]
    y = settings["window"]["y"]
    geometry = f"{width}x{height}"
    if x is not None and y is not None:
        geometry += f"+{x}+{y}"
    window.geometry(geometry)
    copy_on_select_var.set(settings["options"]["copy_on_select"])
    reformat_lines_var.set(settings["options"]["reformat_lines"])
    current_directory = settings["last_directory"]
    if current_directory and os.path.exists(current_directory):
        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, current_directory)
        refresh_file_list()
    return current_directory
