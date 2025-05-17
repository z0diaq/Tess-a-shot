import os

import image_ops
import ctx_ui
import settings

def on_file_select(event):
    """Handles file selection from the listbox."""
    selection = ctx_ui.file_listbox.curselection()
    if not selection:
        return
        
    filename = ctx_ui.file_listbox.get(selection[0])
    file_path = os.path.join(settings.current_directory, filename)
    
    # Load the selected image
    image_ops.load_image(file_path)
