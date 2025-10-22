import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk  # Add ttk for Treeview
from tkinterdnd2 import DND_FILES, TkinterDnD

import ctx_ui
import settings
import ui_ops
import text_ops
import image_ops

def set_interaction_mode(mode):
    """Set the interaction mode and update the context menu."""
    ctx_ui.interaction_mode = mode
    ui_ops.set_status(f"Mode: {mode.replace('_', ' ').title()}")

def show_context_menu(event):
    """Show the context menu at the cursor position."""
    if ctx_ui.context_menu is None:
        create_context_menu()
    
    # Update labels based on current mode
    mode_labels = {
        "area_selection": "Area selection",
        "drag": "Drag",
        "zoom_in": "Zoom in",
        "zoom_out": "Zoom out"
    }
    
    mode_index = {
        "area_selection": 0,
        "drag": 1,
        "zoom_in": 2,
        "zoom_out": 3
    }
    
    # Update each menu item with or without checkmark
    for mode, idx in mode_index.items():
        label = mode_labels[mode]
        if mode == ctx_ui.interaction_mode:
            ctx_ui.context_menu.entryconfigure(idx, label=f"✓ {label}")
        else:
            ctx_ui.context_menu.entryconfigure(idx, label=f"  {label}")
    
    try:
        ctx_ui.context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        ctx_ui.context_menu.grab_release()

def create_context_menu():
    """Create the context menu for the image canvas."""
    ctx_ui.context_menu = tk.Menu(ctx_ui.window, tearoff=0)
    ctx_ui.context_menu.add_command(
        label="✓ Area selection",
        command=lambda: set_interaction_mode("area_selection")
    )
    ctx_ui.context_menu.add_command(
        label="  Drag",
        command=lambda: set_interaction_mode("drag")
    )
    ctx_ui.context_menu.add_command(
        label="  Zoom in",
        command=lambda: set_interaction_mode("zoom_in")
    )
    ctx_ui.context_menu.add_command(
        label="  Zoom out",
        command=lambda: set_interaction_mode("zoom_out")
    )

def setup():
    ctx_ui.refresh_file_list = ui_ops.refresh_file_list

    # Create the main window
    ctx_ui.window = TkinterDnD.Tk()
    ctx_ui.window.title("Tess-a-shot")

    # Load settings before configuring the UI
    settings.load(settings.settings)
    settings.current_directory = settings.settings["last_directory"]

    # Create main frame to organize the layout
    ctx_ui.main_frame = tk.Frame(ctx_ui.window)
    ctx_ui.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Create a PanedWindow for resizable frames (3-column layout)
    ctx_ui.main_paned_window = tk.PanedWindow(ctx_ui.main_frame, orient=tk.HORIZONTAL, sashwidth=5, sashrelief=tk.RAISED)
    ctx_ui.main_paned_window.pack(fill=tk.BOTH, expand=True)

    # Create left frame for file list
    ctx_ui.left_frame = tk.Frame(ctx_ui.main_paned_window)

    # Create middle frame for image preview
    ctx_ui.middle_frame = tk.Frame(ctx_ui.main_paned_window)

    # Create right frame for text output and options
    ctx_ui.right_frame = tk.Frame(ctx_ui.main_paned_window)

    # Add the frames to the main paned window
    ctx_ui.main_paned_window.add(ctx_ui.left_frame, width=250)    # Default width for file list
    ctx_ui.main_paned_window.add(ctx_ui.middle_frame, width=400)  # Default width for image preview
    ctx_ui.main_paned_window.add(ctx_ui.right_frame, width=350)   # Default width for text/options

    # Image preview frame is now directly in the middle frame
    ctx_ui.image_preview_frame = ctx_ui.middle_frame

    # Text output frame is now directly in the right frame
    ctx_ui.text_output_frame = ctx_ui.right_frame

    # Top controls frame
    controls_frame = tk.Frame(ctx_ui.window)
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
    file_list_label = tk.Label(ctx_ui.left_frame, text="Image Files:")
    file_list_label.pack(pady=(0, 5), anchor=tk.W)

    # Create scrollable Treeview for files
    file_list_frame = tk.Frame(ctx_ui.left_frame)
    file_list_frame.pack(fill=tk.BOTH, expand=True)

    columns = ("name", "size")
    ctx_ui.file_tree = file_tree = ttk.Treeview(file_list_frame, columns=columns, show="headings", selectmode="browse")
    file_tree.heading("name", text="Name", command=lambda: ui_ops.sort_file_tree("name"))
    file_tree.heading("size", text="Size (kiB)", command=lambda: ui_ops.sort_file_tree("size"))
    file_tree.column("name", width=settings.settings.get("file_list_columns", {}).get("name", 200), anchor=tk.W)
    file_tree.column("size", width=settings.settings.get("file_list_columns", {}).get("size", 80), anchor=tk.E)
    file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    file_scrollbar = tk.Scrollbar(file_list_frame, orient=tk.VERTICAL, command=file_tree.yview)
    file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    file_tree.configure(yscrollcommand=file_scrollbar.set)

    # Bind file selection event
    file_tree.bind('<<TreeviewSelect>>', ui_ops.on_file_select)

    # Middle Frame - Image Preview Components
    image_frame_label = tk.Label(ctx_ui.image_preview_frame, text="Image Preview:")
    image_frame_label.pack(pady=(0, 5), anchor=tk.W)

    ctx_ui.image_canvas = tk.Canvas(ctx_ui.image_preview_frame, bg="lightgray")
    ctx_ui.image_canvas.pack(fill=tk.BOTH, expand=True)

    # Set default interaction mode
    ctx_ui.interaction_mode = "area_selection"

    # Bind mouse events to routing functions
    ctx_ui.image_canvas.bind("<ButtonPress-1>", image_ops.on_mouse_press)
    ctx_ui.image_canvas.bind("<B1-Motion>", image_ops.on_mouse_motion)
    ctx_ui.image_canvas.bind("<ButtonRelease-1>", image_ops.on_mouse_release)
    
    # Bind right-click to show context menu
    ctx_ui.image_canvas.bind("<Button-3>", show_context_menu)

    # Make image_canvas a drop target
    ctx_ui.image_canvas.drop_target_register(DND_FILES)
    ctx_ui.image_canvas.dnd_bind("<<Drop>>", ui_ops.handle_drop)

    # Right Frame - Text Output Components
    text_output_controls = tk.Frame(ctx_ui.text_output_frame)
    text_output_controls.pack(fill=tk.X, pady=(0, 5))

    text_label = tk.Label(text_output_controls, text="Extracted Text:")
    text_label.pack(side=tk.LEFT, pady=(0, 5))

    # Add buttons for text operations
    button_copy = tk.Button(text_output_controls, text="Copy Text", command=text_ops.copy_to_clipboard)
    button_copy.pack(side=tk.RIGHT, padx=5)

    button_delete = tk.Button(text_output_controls, text="Delete Image File", command=image_ops.delete_image, bg="#ffcccc")
    button_delete.pack(side=tk.RIGHT, padx=5)

    # Create notebook (tabbed interface) for extracted text and options
    notebook = ttk.Notebook(ctx_ui.text_output_frame)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Create "Extracted Text" tab
    extracted_text_tab = tk.Frame(notebook)
    notebook.add(extracted_text_tab, text="Extracted Text")

    # Text output area in the Extracted Text tab
    ctx_ui.text_output = scrolledtext.ScrolledText(extracted_text_tab)
    ctx_ui.text_output.pack(fill=tk.BOTH, expand=True)

    # Create "Options" tab
    options_tab = tk.Frame(notebook)
    notebook.add(options_tab, text="Options")

    # Add checkboxes in the Options tab
    # "Copy text on image region select" checkbox
    ctx_ui.copy_on_region_select_var = tk.BooleanVar()
    copy_on_region_select_checkbox = tk.Checkbutton(options_tab, text="Copy text on image region select", variable=ctx_ui.copy_on_region_select_var)
    copy_on_region_select_checkbox.pack(anchor=tk.W, padx=10, pady=(10, 5))

    # "Copy text on extracted text select" checkbox
    ctx_ui.copy_on_select_var = copy_on_select_var = tk.BooleanVar()
    copy_on_select_checkbox = tk.Checkbutton(options_tab, text="Copy text on extracted text select", variable=copy_on_select_var)
    copy_on_select_checkbox.pack(anchor=tk.W, padx=10, pady=5)

    # "Reformat copied lines" checkbox
    ctx_ui.reformat_lines_var = reformat_lines_var = tk.BooleanVar()
    reformat_lines_checkbox = tk.Checkbutton(options_tab, text="Reformat copied lines", variable=reformat_lines_var)
    reformat_lines_checkbox.pack(anchor=tk.W, padx=10, pady=5)

    # "Remember region" checkbox
    ctx_ui.remember_region_var = tk.BooleanVar()
    remember_region_checkbox = tk.Checkbutton(options_tab, text="Remember region", variable=ctx_ui.remember_region_var)
    remember_region_checkbox.pack(anchor=tk.W, padx=10, pady=5)

    # Bind the text selection event to the text_output widget
    ctx_ui.text_output.bind("<<Selection>>", text_ops.on_text_selection)

    # Status bar at the bottom
    ctx_ui.status_label = status_label = tk.Label(ctx_ui.window, text="No image loaded", bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_label.pack(side=tk.BOTTOM, fill=tk.X)

    # Bind the resize event to the window
    ctx_ui.window.bind("<Configure>", ui_ops.on_resize)

    ctx_ui.window.protocol("WM_DELETE_WINDOW", ui_ops.on_closing)

    # Apply saved settings
    settings.apply(ctx_ui)

    # Schedule the sash position setting after the window is drawn
    ctx_ui.set_sash_job = ctx_ui.window.after(100, ui_ops.set_initial_sash_positions)

    # Run the application
    ctx_ui.window.mainloop()
