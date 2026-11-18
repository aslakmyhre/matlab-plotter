"""Asking which of several files beside the logs to use."""
import os
import tkinter as tk
from tkinter import ttk

from .theme import px

MESSAGE_WRAP = 420


def choose_file(parent, title, message, paths, skip_text):
    """The path picked from `paths`, or None when the user skips or closes the window."""
    window = tk.Toplevel(parent)
    window.title(title)
    window.transient(parent.winfo_toplevel())
    window.resizable(False, False)
    body = ttk.Frame(window, padding=px(16))
    body.pack(fill="both", expand=True)
    ttk.Label(body, text=message, wraplength=px(MESSAGE_WRAP), justify="left").pack(
        anchor="w", pady=(0, px(10)))
    picked = tk.StringVar(window, value=paths[0])
    for path in paths:
        ttk.Radiobutton(body, text=os.path.basename(path), value=path,
                        variable=picked).pack(anchor="w", pady=px(1))
    result = []

    def use(_event=None):
        result.append(picked.get())
        window.destroy()

    buttons = ttk.Frame(body)
    buttons.pack(anchor="e", pady=(px(14), 0))
    ttk.Button(buttons, text=skip_text, command=window.destroy).pack(side="left",
                                                                     padx=(0, px(6)))
    ttk.Button(buttons, text="Use", style="Accent.TButton", command=use).pack(side="left")
    window.bind("<Return>", use)
    window.bind("<Escape>", lambda _e: window.destroy())
    # A grab needs the window on screen, and keeps the main window from changing meanwhile.
    window.wait_visibility()
    window.grab_set()
    window.focus_set()
    parent.wait_window(window)
    return result[0] if result else None
