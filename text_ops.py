# text_ops.py
import pyperclip
import tkinter as tk
from .image_ocr import reformat_text

def copy_to_clipboard(text_output, reformat_lines_var, status_label):
    try:
        selected_text = text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
    except tk.TclError:
        selected_text = text_output.get("1.0", tk.END)
    if selected_text:
        if reformat_lines_var.get():
            selected_text = reformat_text(selected_text)
        pyperclip.copy(selected_text)
        status_label.config(text="Text copied to clipboard.")
    else:
        status_label.config(text="No text to copy.")

def on_text_selection(event, text_output, copy_on_select_var, reformat_lines_var, status_label):
    if copy_on_select_var.get():
        try:
            selected_text = text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                if reformat_lines_var.get():
                    selected_text = reformat_text(selected_text)
                pyperclip.copy(selected_text)
                status_label.config(text="Selected text copied to clipboard.")
        except tk.TclError:
            pass
