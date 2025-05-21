import tkinter as tk
from tkinter import scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD

import ctx_ui
import settings
import ui_ops
import text_ops
import image_ops

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

    # Create a PanedWindow for resizable frames (left/right split)
    ctx_ui.main_paned_window = tk.PanedWindow(ctx_ui.main_frame, orient=tk.HORIZONTAL, sashwidth=5, sashrelief=tk.RAISED)
    ctx_ui.main_paned_window.pack(fill=tk.BOTH, expand=True)

    # Create left frame for file list
    ctx_ui.left_frame = tk.Frame(ctx_ui.main_paned_window)

    # Create right frame for image preview and text output
    ctx_ui.right_frame = tk.Frame(ctx_ui.main_paned_window)

    # Add the frames to the main paned window
    ctx_ui.main_paned_window.add(ctx_ui.left_frame, width=250)  # Default width for file list
    ctx_ui.main_paned_window.add(ctx_ui.right_frame, width=650)  # Default width for preview/text

    # Create a vertical PanedWindow for the right frame (preview/text split)
    ctx_ui.right_paned_window = tk.PanedWindow(ctx_ui.right_frame, orient=tk.VERTICAL, sashwidth=5, sashrelief=tk.RAISED)
    ctx_ui.right_paned_window.pack(fill=tk.BOTH, expand=True)

    ctx_ui.right_paned_window.bind('<B1-Motion>', ui_ops.on_right_pane_drag)

    # Create frames for the right paned window
    ctx_ui.image_preview_frame = tk.Frame(ctx_ui.right_paned_window)
    ctx_ui.text_output_frame = tk.Frame(ctx_ui.right_paned_window)

    # Add the frames to the right paned window
    ctx_ui.right_paned_window.add(ctx_ui.image_preview_frame, height=300)  # Default height for preview
    ctx_ui.right_paned_window.add(ctx_ui.text_output_frame, height=300)    # Default height for text

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

    # Create scrollable listbox for files
    file_list_frame = tk.Frame(ctx_ui.left_frame)
    file_list_frame.pack(fill=tk.BOTH, expand=True)

    ctx_ui.file_listbox = file_listbox = tk.Listbox(file_list_frame, selectmode=tk.SINGLE, exportselection=0)
    file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    file_scrollbar = tk.Scrollbar(file_list_frame, orient=tk.VERTICAL, command=file_listbox.yview)
    file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    file_listbox.config(yscrollcommand=file_scrollbar.set)

    # Bind file selection event
    file_listbox.bind('<<ListboxSelect>>', ui_ops.on_file_select)

    # Right Frame - Image Preview Components
    image_frame_label = tk.Label(ctx_ui.image_preview_frame, text="Image Preview:")
    image_frame_label.pack(pady=(0, 5), anchor=tk.W)

    ctx_ui.image_canvas = tk.Canvas(ctx_ui.image_preview_frame, bg="lightgray")
    ctx_ui.image_canvas.pack(fill=tk.BOTH, expand=True)

    ctx_ui.image_canvas.bind("<ButtonPress-1>", image_ops.on_selection_start)
    ctx_ui.image_canvas.bind("<B1-Motion>", image_ops.on_selection_motion)
    ctx_ui.image_canvas.bind("<ButtonRelease-1>", image_ops.on_selection_end)

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

    # Add checkboxes in a horizontal frame
    checkboxes_frame = tk.Frame(ctx_ui.text_output_frame)
    checkboxes_frame.pack(anchor=tk.W, pady=(0, 5), fill=tk.X)

    # "Copy text on select" checkbox
    ctx_ui.copy_on_select_var = copy_on_select_var = tk.BooleanVar()
    copy_on_select_checkbox = tk.Checkbutton(checkboxes_frame, text="Copy text on select", variable=copy_on_select_var)
    copy_on_select_checkbox.pack(side=tk.LEFT, padx=(0, 10))

    # "Reformat copied lines" checkbox
    ctx_ui.reformat_lines_var = reformat_lines_var = tk.BooleanVar()
    reformat_lines_checkbox = tk.Checkbutton(checkboxes_frame, text="Reformat copied lines", variable=reformat_lines_var)
    reformat_lines_checkbox.pack(side=tk.LEFT)

    # "Remember region" checkbox
    ctx_ui.remember_region_var = tk.BooleanVar()
    remember_region_checkbox = tk.Checkbutton(checkboxes_frame, text="Remember region", variable=ctx_ui.remember_region_var)
    remember_region_checkbox.pack(side=tk.LEFT, padx=(10, 0))

    # Text output area
    ctx_ui.text_output = scrolledtext.ScrolledText(ctx_ui.text_output_frame)
    ctx_ui.text_output.pack(fill=tk.BOTH, expand=True)

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
