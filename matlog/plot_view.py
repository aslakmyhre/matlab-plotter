"""The interactive side of the plot: toolbar, wheel zoom, and zoom kept across redraws."""
import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

from .theme import px
from .widgets import Tooltip, bind_touchpad, touchpad_delta

ZOOM_STEP = 1.2
# Trackpad pixels that count as one wheel notch of zoom.
TOUCHPAD_PIXELS_PER_STEP = 40.0
SHIFT_MASK = 0x1
PAN_MODE, ZOOM_MODE = "pan/zoom", "zoom rect"
IDLE_HINT = "Scroll to zoom, double-click to reset"


class PlotToolbar(NavigationToolbar2Tk):
    """Matplotlib's navigation behind buttons that match the window.

    Its own Tk buttons are never put on screen: their icons and bevels look like nothing
    else in the window, and disabled ones turn into a dither pattern on Linux.
    """

    def __init__(self, canvas, parent):
        self.readout = tk.StringVar(parent, value=IDLE_HINT)
        super().__init__(canvas, parent, pack_toolbar=False)
        self.pan_on = tk.BooleanVar(parent, value=False)
        self.zoom_on = tk.BooleanVar(parent, value=False)

    def build_bar(self, parent):
        """The row of buttons, to be placed by the caller."""
        bar = ttk.Frame(parent, padding=(px(10), px(4)))
        bar.columnconfigure(5, weight=1)
        for column, (text, command, tip) in enumerate((
                ("Full view", self.home, "Back to the full view (or double-click the plot)"),
                ("Back", self.back, "Previous view"),
                ("Forward", self.forward, "Next view"))):
            button = ttk.Button(bar, text=text, style="Ghost.TButton", command=command,
                                takefocus=False)
            button.grid(row=0, column=column)
            Tooltip(button, tip)
        for column, (text, variable, command, tip) in enumerate((
                ("Pan", self.pan_on, self.toggle_pan, "Drag to move the view"),
                ("Zoom box", self.zoom_on, self.toggle_zoom, "Drag a box to zoom into it"))):
            button = ttk.Checkbutton(bar, text=text, style="Plot.Toggle.Toolbutton",
                                     variable=variable, command=command, takefocus=False)
            button.grid(row=0, column=3 + column, padx=(px(6) if column == 0 else px(2), 0))
            Tooltip(button, tip)
        # Width 1 lets a narrow pane cut this text rather than the buttons beside it.
        ttk.Label(bar, textvariable=self.readout, style="Small.TLabel", anchor="e", width=1).grid(
            row=0, column=5, sticky="ew", padx=(px(10), 0))
        return bar

    def toggle_pan(self):
        self.pan()
        self._show_mode()

    def toggle_zoom(self):
        self.zoom()
        self._show_mode()

    def _show_mode(self):
        self.pan_on.set(self.mode == PAN_MODE)
        self.zoom_on.set(self.mode == ZOOM_MODE)

    def set_message(self, s):
        # Matplotlib reports the pointer's position here, with newlines for images.
        self.readout.set(" ".join(s.split()) or IDLE_HINT)


def zoomed_limits(low, high, center, factor):
    """The range scaled by `factor`, with `center` staying where it is on screen."""
    return center + (low - center) * factor, center + (high - center) * factor


class PlotGestures:
    """Wheel or two fingers zoom time around the pointer, shift zooms y, double-click resets."""

    def __init__(self, canvas, toolbar):
        self.canvas = canvas
        self.toolbar = toolbar
        canvas.mpl_connect("scroll_event", self._on_scroll)
        canvas.mpl_connect("button_press_event", self._on_press)
        bind_touchpad(canvas.get_tk_widget(), self._on_touchpad)

    def _on_scroll(self, event):
        if event.inaxes is None or event.step == 0:
            return
        shift = event.guiEvent is not None and event.guiEvent.state & SHIFT_MASK
        self._zoom(event.inaxes, event.xdata, event.ydata, -np.sign(event.step), bool(shift))

    def _on_touchpad(self, event):
        widget = self.canvas.get_tk_widget()
        # Matplotlib counts y from the bottom of the canvas, Tk from the top.
        x, y = event.x, widget.winfo_height() - event.y
        ratio = self.canvas.device_pixel_ratio
        ax = self.canvas.inaxes((x * ratio, y * ratio))
        if ax is None:
            return
        data_x, data_y = ax.transData.inverted().transform((x * ratio, y * ratio))
        steps = touchpad_delta(widget, event) / TOUCHPAD_PIXELS_PER_STEP
        self._zoom(ax, data_x, data_y, steps, bool(event.state & SHIFT_MASK))

    def _zoom(self, ax, x, y, steps, vertical):
        factor = ZOOM_STEP ** steps
        if vertical:
            ax.set_ylim(*zoomed_limits(*ax.get_ylim(), y, factor))
        else:
            ax.set_xlim(*zoomed_limits(*ax.get_xlim(), x, factor))
        self.canvas.draw_idle()

    def _on_press(self, event):
        if event.dblclick and event.inaxes is not None:
            self.toolbar.home()


class ViewMemory:
    """Keeps what the user zoomed to while the figure is rebuilt.

    Stepping through runs or editing a legend redraws from scratch, which would otherwise
    throw the zoom away and make the same time window impossible to compare across runs.
    A view is remembered per panel and per set of limits typed for it, so a new typed limit
    takes effect at once.
    """

    def __init__(self):
        self.home = {}
        self.zoomed = {}

    def capture(self):
        """Note the zoom on the axes about to be cleared."""
        for key, (ax, home) in self.home.items():
            view = (ax.get_xlim(), ax.get_ylim())
            if view == home:
                self.zoomed.pop(key, None)
            else:
                self.zoomed[key] = view
        self.home = {}

    def reapply(self, axes_by_key, toolbar):
        """Make the fresh view the toolbar's Home, then return to any remembered zoom."""
        self.home = {key: (ax, (ax.get_xlim(), ax.get_ylim()))
                     for key, ax in axes_by_key.items()}
        # The toolbar's history refers to axes that no longer exist.
        toolbar.update()
        toolbar.push_current()
        restored = False
        for key, ax in axes_by_key.items():
            if key in self.zoomed:
                xlim, ylim = self.zoomed[key]
                ax.set_xlim(xlim)
                ax.set_ylim(ylim)
                restored = True
        if restored:
            toolbar.push_current()

    def forget(self):
        self.home = {}
        self.zoomed = {}
