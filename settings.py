import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import scrolledtext
import json
import os

import ctx

# Configuration file path
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".tessashot_config.json")

# Default settings
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

# Global settings variable
settings = DEFAULT_SETTINGS.copy()

def save_settings():
    """Save current application settings to the config file"""
    global settings
    
    # Update window geometry in settings
    settings["window"]["width"] = ctx.window.winfo_width()  
    settings["window"]["height"] = ctx.window.winfo_height()
    settings["window"]["x"] = ctx.window.winfo_x()
    settings["window"]["y"] = ctx.window.winfo_y()
    
    # Calculate pane ratio based on current frame widths
    if ctx.main_frame.winfo_width() > 0:  # Prevent division by zero
        settings["pane_ratio"] = ctx.left_frame.winfo_width() / ctx.main_frame.winfo_width()
    
    # Calculate right pane ratio
    if ctx.right_frame.winfo_height() > 0:  # Prevent division by zero
        settings["right_pane_ratio"] = ctx.image_preview_frame.winfo_height() / ctx.right_frame.winfo_height()
    
    # Update options settings
    settings["options"]["copy_on_select"] = ctx.copy_on_select_var.get()
    settings["options"]["reformat_lines"] = ctx.reformat_lines_var.get()
    
    # Save last directory
    settings["last_directory"] = ctx.current_directory
    
    # Write to file
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_settings():
    """Load application settings from the config file"""
    global settings
    
    try:
        # Check if the config file exists
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                loaded_settings = json.load(f)
                # Update our settings with loaded values
                settings.update(loaded_settings)
    except Exception as e:
        print(f"Error loading settings: {e}")
        
    return settings

def apply_settings():
    """Apply loaded settings to the application"""
    global settings
    
    # Set window size and position
    width = settings["window"]["width"]
    height = settings["window"]["height"]
    x = settings["window"]["x"]
    y = settings["window"]["y"]
    
    # Set window geometry
    geometry = f"{width}x{height}"
    if x is not None and y is not None:
        geometry += f"+{x}+{y}"
    ctx.window.geometry(geometry)
    
    # Set checkbox values
    ctx.copy_on_select_var.set(settings["options"]["copy_on_select"])
    ctx.reformat_lines_var.set(settings["options"]["reformat_lines"])
    
    # Set last used directory
    ctx.current_directory = settings["last_directory"]
    if ctx.current_directory and os.path.exists(ctx.current_directory):
        ctx.directory_entry.delete(0, tk.END)
        ctx.directory_entry.insert(0, ctx.current_directory)
        ctx.refresh_file_list()
