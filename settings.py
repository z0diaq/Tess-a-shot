import os
import json
import tkinter as tk

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".tessashot_config.json")

current_directory = ""

DEFAULT_SETTINGS = {
    "window": {
        "width": 900,
        "height": 700,
        "x": None,
        "y": None
    },
    "pane_ratio": 0.3,  # 30% for file list, 70% for preview/text
    "right_pane_ratio": 0.5,  # 50% split for image preview and text output
    "options": {
        "copy_on_select": False,
        "reformat_lines": False
    },
    "last_directory": ""
}

settings = DEFAULT_SETTINGS.copy()

def save(ctx_ui):
    settings["window"]["width"] = ctx_ui.window.winfo_width()
    settings["window"]["height"] = ctx_ui.window.winfo_height()
    settings["window"]["x"] = ctx_ui.window.winfo_x()
    settings["window"]["y"] = ctx_ui.window.winfo_y()
    if ctx_ui.main_frame.winfo_width() > 0:
        settings["pane_ratio"] = ctx_ui.left_frame.winfo_width() / ctx_ui.main_frame.winfo_width()
    if ctx_ui.right_frame.winfo_height() > 0:
        settings["right_pane_ratio"] = ctx_ui.image_preview_frame.winfo_height() / ctx_ui.right_frame.winfo_height()
    settings["options"]["copy_on_select"] = ctx_ui.copy_on_select_var.get()
    settings["options"]["reformat_lines"] = ctx_ui.reformat_lines_var.get()
    settings["last_directory"] = current_directory
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load(settings):
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                loaded_settings = json.load(f)
                settings.update(loaded_settings)
    except Exception as e:
        print(f"Error loading settings: {e}")
    return settings

def apply(ctx_ui):
    width = settings["window"]["width"]
    height = settings["window"]["height"]
    x = settings["window"]["x"]
    y = settings["window"]["y"]
    geometry = f"{width}x{height}"
    if x is not None and y is not None:
        geometry += f"+{x}+{y}"
    ctx_ui.window.geometry(geometry)
    ctx_ui.copy_on_select_var.set(settings["options"]["copy_on_select"])
    ctx_ui.reformat_lines_var.set(settings["options"]["reformat_lines"])
    current_directory = settings["last_directory"]
    if current_directory and os.path.exists(current_directory):
        ctx_ui.directory_entry.delete(0, tk.END)
        ctx_ui.directory_entry.insert(0, current_directory)
        ctx_ui.refresh_file_list()
