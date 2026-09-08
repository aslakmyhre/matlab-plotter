"""Small tkinter helpers shared by the tabs."""
import tkinter as tk
from tkinter import ttk


def scrollable(parent, horizontal=False):
    """A frame inside a scrolling viewport. Returns the frame to fill."""
    holder = ttk.Frame(parent)
    holder.rowconfigure(0, weight=1)
    holder.columnconfigure(0, weight=1)
    canvas = tk.Canvas(holder, highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")
    vertical = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
    vertical.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=vertical.set)
    if horizontal:
        bar = ttk.Scrollbar(holder, orient="horizontal", command=canvas.xview)
        bar.grid(row=1, column=0, sticky="ew")
        canvas.configure(xscrollcommand=bar.set)

    inner = ttk.Frame(canvas, padding=(2, 2))
    window = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    if not horizontal:
        # Without a horizontal bar the content must follow the viewport width.
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
    canvas.bind_all("<MouseWheel>", lambda e: _wheel(canvas, e), add="+")
    return holder, inner


def _wheel(canvas, event):
    if canvas.winfo_containing(event.x_root, event.y_root) is None:
        return
    canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")


def labelled_entry(parent, row, text, variable, width=None):
    ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=1)
    entry = ttk.Entry(parent, textvariable=variable, width=width)
    entry.grid(row=row, column=1, columnspan=3, sticky="ew", pady=1)
    return entry
