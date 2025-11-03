import tkinter as tk
import pyperclip

import ctx_ui
import ui_ops

def reformat_text(text):
    """
    Reformat text to ensure only one space exists between words.
    """
    # Split text into lines
    words = text.split()
    
    # Process each line to normalize whitespace
    normalized_words = []
    for word in words:
        if word in [',', ':', '.', ';'] and len(normalized_words) > 0:
            normalized_words[-1] += word
        else:
            normalized_words.append(word)
    
    # Join lines back with newlines
    return ' '.join(normalized_words)

# Function to copy selected text to clipboard
def copy_to_clipboard():
    """Copy selected text to clipboard, or all text if none selected."""
    try:
        selected_text = ctx_ui.text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
    except tk.TclError:  # No selection
        selected_text = ctx_ui.text_output.get("1.0", tk.END)
    
    if selected_text:
        # Apply reformatting if the option is checked
        if ctx_ui.reformat_lines_var.get():
            selected_text = reformat_text(selected_text)
        
        pyperclip.copy(selected_text)
        ui_ops.set_status("Text copied to clipboard.")
    else:
        ui_ops.set_status("No text to copy.")

# Function to handle text selection
def on_text_selection(event):
    """Copy selected text to clipboard when text is selected and checkbox is checked"""
    try:
        # Force focus to the text widget to ensure selection is visible
        ctx_ui.text_output.focus_set()
        
        # Ensure the selection is in view and update display
        ctx_ui.text_output.see(tk.SEL_FIRST)
        ctx_ui.text_output.update_idletasks()
        
        if ctx_ui.copy_on_select_var.get():
            selected_text = ctx_ui.text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                # Apply reformatting if the option is checked
                if ctx_ui.reformat_lines_var.get():
                    selected_text = reformat_text(selected_text)
                
                pyperclip.copy(selected_text)
                ui_ops.set_status("Selected text copied to clipboard.")
    except tk.TclError:  # No selection or other Tcl errors
        pass  # Do nothing if no text is selected or other errors occur

def log(message):
    """Log messages to the console."""
    print(message)
