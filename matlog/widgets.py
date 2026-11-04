"""Small tkinter helpers shared by the window's panes."""
import tkinter as tk
from tkinter import TclError, ttk

from .theme import ACCENT, BORDER, INK, INK_3, SURFACE, px

TOOLTIP_DELAY_MS = 500
TOOLTIP_WRAP = 600
SCROLL_UNIT = 24
SWATCH_PX = 14
DRAG_HANDLE = "\u2261"


def autohiding(bar, sticky_set):
    """A scrollbar `set` that takes the bar away while everything fits."""
    def update(first, last):
        if float(first) <= 0 and float(last) >= 1:
            bar.grid_remove()
        else:
            bar.grid()
        sticky_set(first, last)
    return update


def scrollable(parent):
    """A frame inside a vertically scrolling viewport. Returns (holder, frame to fill)."""
    holder = ttk.Frame(parent)
    holder.rowconfigure(0, weight=1)
    holder.columnconfigure(0, weight=1)
    canvas = tk.Canvas(holder, highlightthickness=0, background=SURFACE,
                       yscrollincrement=px(SCROLL_UNIT), width=1, height=1)
    canvas.grid(row=0, column=0, sticky="nsew")
    vertical = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
    vertical.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=autohiding(vertical, vertical.set))

    inner = ttk.Frame(canvas, padding=(0, 0, px(4), 0))
    window = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    # The content follows the viewport width, so nothing ever scrolls sideways.
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
    bind_scroll(canvas, lambda units: _scroll(canvas, units))
    return holder, inner


def _scroll(canvas, units):
    # A list shorter than its viewport has nothing to scroll, and Tk would still move it.
    if canvas.yview() != (0.0, 1.0):
        canvas.yview_scroll(units, "units")


def bind_scroll(widget, scroll):
    """Call scroll(units) for wheel and trackpad gestures over this widget or its children."""
    def under_pointer(event):
        under = widget.winfo_containing(event.x_root, event.y_root)
        return under is not None and (str(under) + ".").startswith(str(widget) + ".")

    def on_wheel(event):
        if under_pointer(event):
            scroll(-1 if event.delta > 0 else 1)

    def on_button(units):
        def handler(event):
            if under_pointer(event):
                scroll(units)
        return handler

    # The binding is global because the children under the pointer get the events.
    widget.bind_all("<MouseWheel>", on_wheel, add="+")
    if widget.tk.call("tk", "windowingsystem") == "x11":
        widget.bind_all("<Button-4>", on_button(-1), add="+")
        widget.bind_all("<Button-5>", on_button(1), add="+")
    remainder = [0.0]

    def on_touchpad(event):
        if not under_pointer(event):
            return
        remainder[0] += touchpad_delta(widget, event)
        units = int(remainder[0] / SCROLL_UNIT)
        if units:
            remainder[0] -= units * SCROLL_UNIT
            scroll(-units)

    bind_touchpad(widget, on_touchpad, every=True)


def bind_touchpad(widget, handler, every=False):
    """Bind Tk 9's trackpad event. Tk 8.6 has none, and sends trackpads as wheel events."""
    try:
        if every:
            widget.bind_all("<TouchpadScroll>", handler, add="+")
        else:
            widget.bind("<TouchpadScroll>", handler, add="+")
    except TclError:
        return False
    return True


def touchpad_delta(widget, event):
    """The vertical pixels a <TouchpadScroll> event moved."""
    _dx, dy = widget.tk.splitlist(widget.tk.call("tk::PreciseScrollDeltas", event.delta))
    return float(dy)


def scrolling_tree(parent):
    """A multi-select tree with a vertical scrollbar. Returns (holder, tree)."""
    holder = ttk.Frame(parent)
    holder.rowconfigure(0, weight=1)
    holder.columnconfigure(0, weight=1)
    tree = ttk.Treeview(holder, show="tree", selectmode="extended", height=4)
    tree.grid(row=0, column=0, sticky="nsew")
    bar = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
    bar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=autohiding(bar, bar.set))
    return holder, tree


def labelled_entry(parent, row, text, variable, width=None):
    ttk.Label(parent, text=text, style="Muted.TLabel").grid(row=row, column=0, sticky="w",
                                                            pady=px(2), padx=(0, px(8)))
    entry = ttk.Entry(parent, textvariable=variable, width=width)
    entry.grid(row=row, column=1, columnspan=3, sticky="ew", pady=px(2))
    return entry


def heading(parent, text):
    return ttk.Label(parent, text=text.upper(), style="Heading.TLabel")


def divider(parent):
    return ttk.Frame(parent, style="Divider.TFrame", height=1)


def wrapping_label(parent, **options):
    """A label that wraps at whatever width the pane gives it."""
    label = ttk.Label(parent, justify="left", **options)
    label.bind("<Configure>", lambda e: label.configure(wraplength=e.width))
    return label


def swatch(parent, color, on_click):
    """A patch of colour that opens a picker. tk.Button ignores its colour on macOS."""
    patch = tk.Frame(parent, background=color, width=px(SWATCH_PX), height=px(SWATCH_PX),
                     cursor="hand2", highlightthickness=1, highlightbackground=BORDER)
    patch.bind("<Button-1>", lambda _e: on_click())
    return patch


def segmented(parent, variable, choices, command=None):
    """A row of mutually exclusive buttons. `choices` is [(value, text, tooltip or None)]."""
    track = ttk.Frame(parent, style="Track.TFrame", padding=px(2))
    for position, (value, text, tip) in enumerate(choices):
        button = ttk.Radiobutton(track, text=text, value=value, variable=variable,
                                 style="Segment.Toolbutton", command=command, takefocus=False)
        button.grid(row=0, column=position, sticky="ew")
        track.columnconfigure(position, weight=1)
        if tip:
            Tooltip(button, tip)
    return track


def add_placeholder(entry, variable, text):
    """Grey hint text inside an entry, while it is empty."""
    hint = tk.Label(entry, text=text, foreground=INK_3, background=SURFACE, cursor="xterm")
    hint.bind("<Button-1>", lambda _e: entry.focus_set())

    def refresh(*_trace):
        if variable.get():
            hint.place_forget()
        else:
            hint.place(x=px(6), rely=0.5, anchor="w")

    variable.trace_add("write", refresh)
    refresh()


class Tooltip:
    """Help that appears when the pointer rests on a widget.

    `text` may be a callable taking the event, for widgets whose text depends on where the
    pointer is. It returns the text, or "" for no tip.
    """

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.pending = None
        self.window = None
        self.shown_text = ""
        widget.bind("<Motion>", self._moved, add="+")
        widget.bind("<Leave>", lambda _e: self._hide(), add="+")
        widget.bind("<ButtonPress>", lambda _e: self._hide(), add="+")
        # A tip still waiting to appear must not outlive a row that gets rebuilt.
        widget.bind("<Destroy>", lambda _e: self._hide(), add="+")

    def _moved(self, event):
        text = self.text(event) if callable(self.text) else self.text
        if text == self.shown_text and self.window is not None:
            return
        self._hide()
        self.shown_text = text
        if text:
            self.pending = self.widget.after(TOOLTIP_DELAY_MS, self._show, event.x_root,
                                             event.y_root)

    def _show(self, x, y):
        self.pending = None
        self.window = tk.Toplevel(self.widget)
        self.window.overrideredirect(True)
        self.window.geometry(f"+{x + px(12)}+{y + px(14)}")
        tk.Label(self.window, text=self.shown_text, background=INK, foreground=SURFACE,
                 font="TkTooltipFont", justify="left", wraplength=px(TOOLTIP_WRAP),
                 padx=px(8), pady=px(4)).pack()

    def _hide(self):
        if self.pending:
            self.widget.after_cancel(self.pending)
            self.pending = None
        if self.window is not None:
            self.window.destroy()
            self.window = None
        self.shown_text = ""


class Checklist(ttk.Frame):
    """Rows of a drag handle, a tick box, a colour patch and a label, keyed by a string.

    A click calls on_toggle() and a finished drag calls on_reorder(keys). Setting the ticks
    from code calls neither, so the list can follow the plot without feeding back into it.
    """

    def __init__(self, parent, on_toggle, on_color, on_reorder, handle_tip):
        super().__init__(parent)
        self.on_toggle = on_toggle
        self.on_color = on_color
        self.on_reorder = on_reorder
        self.handle_tip = handle_tip
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        holder, self.inner = scrollable(self)
        holder.grid(row=0, column=0, sticky="nsew")
        self.inner.columnconfigure(1, weight=1)
        self.rows = {}
        # The keys in the order shown.
        self.order = []
        self.dragged = None
        self.order_before_drag = []

    def set_items(self, items):
        """Rebuild for `items`, a list of (key, text, colour). Starts with nothing ticked."""
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.rows = {}
        self.order = [key for key, _text, _color in items]
        self.dragged = None
        for key, text, color in items:
            handle = tk.Label(self.inner, text=DRAG_HANDLE, foreground=INK_3, background=SURFACE,
                              cursor="sb_v_double_arrow")
            handle.bind("<ButtonPress-1>", lambda _e, k=key: self._start_drag(k))
            handle.bind("<B1-Motion>", self._drag)
            handle.bind("<ButtonRelease-1>", lambda _e: self._finish_drag())
            Tooltip(handle, self.handle_tip)
            ticked = tk.BooleanVar(self, value=False)
            box = ttk.Checkbutton(self.inner, text=text, variable=ticked, command=self.on_toggle,
                                  style="Row.TCheckbutton", takefocus=False)
            patch = swatch(self.inner, color, lambda k=key: self.on_color(k))
            self.rows[key] = (ticked, box, patch, handle)
        self._place_rows()

    def _place_rows(self):
        for row, key in enumerate(self.order):
            _ticked, box, patch, handle = self.rows[key]
            handle.grid(row=row, column=0, padx=(0, px(4)))
            box.grid(row=row, column=1, sticky="ew")
            patch.grid(row=row, column=2, padx=(px(4), 0))

    def _start_drag(self, key):
        self.dragged = key
        self.order_before_drag = list(self.order)
        self.rows[key][3].configure(foreground=ACCENT)

    def _drag(self, event):
        if self.dragged is None:
            return
        self._scroll_at_edges(event.y_root)
        _column, target = self.inner.grid_location(0, event.y_root - self.inner.winfo_rooty())
        target = min(max(target, 0), len(self.order) - 1)
        position = self.order.index(self.dragged)
        if target != position:
            self.order.insert(target, self.order.pop(position))
            self._place_rows()

    def _scroll_at_edges(self, pointer_y):
        """Dragging past the top or bottom of the view brings the hidden rows in."""
        viewport = self.inner.master
        top = viewport.winfo_rooty()
        if pointer_y < top:
            viewport.yview_scroll(-1, "units")
        elif pointer_y > top + viewport.winfo_height():
            viewport.yview_scroll(1, "units")

    def _finish_drag(self):
        if self.dragged is None:
            return
        self.rows[self.dragged][3].configure(foreground=INK_3)
        self.dragged = None
        if self.order != self.order_before_drag:
            self.on_reorder(list(self.order))

    def checked(self):
        return [key for key in self.order if self.rows[key][0].get()]

    def set_checked(self, keys):
        for key, row in self.rows.items():
            row[0].set(key in keys)

    def rename(self, key, text):
        if key in self.rows:
            self.rows[key][1].configure(text=text)
