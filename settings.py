import os
import json
import tkinter as tk

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".tessashot_config.json")

current_directory = ""
current_file = ""
selection_coords = [0, 0, 0, 0]  # [x1, y1, x2, y2] in original image coordinates

DEFAULT_SETTINGS = {
    "window": {
        "width": 900,
        "height": 700,
        "x": None,
        "y": None
    },
    "pane_ratio": 0.25,  # 25% for file list (left column)
    "middle_pane_ratio": 0.45,  # 45% for image preview (middle column), remaining 30% for text/options (right column)
    "options": {
        "copy_on_select": False,
        "reformat_lines": False,
        "remember_region": False
    },
    "last_directory": "",
    "last_file": "",
    "last_selection": {
        "x1": 0,
        "y1": 0,
        "x2": 0,
        "y2": 0
    },
    "file_list_columns": {
        "name": 200,
        "size": 80
    }
}

settings = DEFAULT_SETTINGS.copy()

def save(ctx_ui):
    settings["window"]["width"] = ctx_ui.window.winfo_width()
    settings["window"]["height"] = ctx_ui.window.winfo_height()
    settings["window"]["x"] = ctx_ui.window.winfo_x()
    settings["window"]["y"] = ctx_ui.window.winfo_y()
    if ctx_ui.main_frame.winfo_width() > 0:
        settings["pane_ratio"] = ctx_ui.left_frame.winfo_width() / ctx_ui.main_frame.winfo_width()
        settings["middle_pane_ratio"] = ctx_ui.middle_frame.winfo_width() / ctx_ui.main_frame.winfo_width()
    settings["options"]["copy_on_select"] = ctx_ui.copy_on_select_var.get()
    settings["options"]["reformat_lines"] = ctx_ui.reformat_lines_var.get()
    settings["options"]["remember_region"] = ctx_ui.remember_region_var.get()
    settings["last_directory"] = current_directory
    settings["last_file"] = current_file
    if ctx_ui.remember_region_var.get():
        settings["last_selection"] = {
            "x1": selection_coords[0],
            "y1": selection_coords[1],
            "x2": selection_coords[2],
            "y2": selection_coords[3]
        }
    else:
        settings["last_selection"] = {
            "x1": 0,
            "y1": 0,
            "x2": 0,
            "y2": 0
        }
    # Save file list column widths if available
    if hasattr(ctx_ui, 'file_tree') and ctx_ui.file_tree is not None:
        settings["file_list_columns"] = {
            "name": ctx_ui.file_tree.column("name", option="width"),
            "size": ctx_ui.file_tree.column("size", option="width")
        }
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
    ctx_ui.remember_region_var.set(settings["options"].get("remember_region", False))

    selection_coords[0] = settings["last_selection"]["x1"]
    selection_coords[1] = settings["last_selection"]["y1"]
    selection_coords[2] = settings["last_selection"]["x2"]
    selection_coords[3] = settings["last_selection"]["y2"]

    global current_directory, current_file

    current_directory = settings["last_directory"]
    current_file = settings["last_file"]
    if current_directory and os.path.exists(current_directory):
        ctx_ui.directory_entry.delete(0, tk.END)
        ctx_ui.directory_entry.insert(0, current_directory)
        ctx_ui.refresh_file_list()

    # Restore file list column widths if available
    if hasattr(ctx_ui, 'file_tree') and ctx_ui.file_tree is not None:
        col_settings = settings.get("file_list_columns", {})
        if col_settings:
            ctx_ui.file_tree.column("name", width=col_settings.get("name", 200))
            ctx_ui.file_tree.column("size", width=col_settings.get("size", 80))

