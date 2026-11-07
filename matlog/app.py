"""The MAT log plotter window."""
import os
import posixpath
import re
import sys
import tkinter as tk
import traceback
from collections import namedtuple
from contextlib import contextmanager
from tkinter import colorchooser, filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from . import (data, expressions, figure as figure_builder, names as names_module, prefs,
               runs as runs_module, store)
from .cursor import Crosshair
from .models import (HIDDEN, LINE_STYLES, PALETTE, XLABEL_MODES, Channel, LineLook, Panel,
                     line_style, palette_color, parse_float, parse_limit)
from .plot_view import PlotGestures, PlotToolbar, ViewMemory
from .theme import ERROR, INK_2, SURFACE, px
from .widgets import (Checklist, DragRows, Tooltip, add_placeholder, divider, heading,
                      labelled_entry, scrollable, scrolling_tree, segmented, swatch,
                      wrapping_label)

APP_TITLE = "MAT log plotter"
MAX_PANELS = 16
# Window and pane sizes, for a 96 dpi display. The sashes move the panes from there.
DEFAULT_WINDOW = (1500, 900)
MIN_WINDOW = (960, 600)
SIDEBAR_WIDTH = 320
INSPECTOR_WIDTH = 400
PANE_WIDTH_LIMITS = (160, 900)
# Below this window width the settings start hidden, leaving the room to the plot.
INSPECTOR_MIN_WINDOW_WIDTH = 1280
PLOT_MIN_SIZE_INCHES = (4, 3)
EMPTY_STATE_RECENT = 5
# Edits redraw on their own once typing pauses this long.
DRAW_DELAY_MS = 400
# Holding an arrow key in the run list loads only the run it stops on.
SELECT_DELAY_MS = 120
# Dragging the window edge lays the plot out again only where it stops.
RELAYOUT_DELAY_MS = 120
# How several runs, or the selected signals of one, are laid out.
OVERLAY, MERGED, GRID, SIDE_BY_SIDE = "overlay", "merged", "grid", "side by side"
LAYOUT_CHOICES = ((OVERLAY, "Overlay", "A panel per signal, a line per run"),
                  (MERGED, "Merged", "Every line in one panel. Colour is the run, dash is the "
                                     "signal"),
                  (GRID, "Grid", "A panel per signal and run: rows are signals, columns runs"),
                  (SIDE_BY_SIDE, "Side by side", "A panel per run, holding its ticked signals. "
                                                 "Colour is the signal"))
FOLDER_PREFIX = "dir:"
FIGURE_FORMATS = (("PNG image", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg"), ("EPS", "*.eps"))
EXPORT_AS_SHOWN, EXPORT_CUSTOM = "As shown on screen", "Custom"
# Width and height in cm. Text keeps its point size, so a small figure reads the same on paper.
EXPORT_PRESETS = {EXPORT_AS_SHOWN: None, "Report, full width": (16, 9),
                  "Report, half width": (8, 6), "Slide": (25, 14), EXPORT_CUSTOM: None}
EXPORT_DPIS = ("160", "300", "600")
DEFAULT_EXPORT_DPI = "300"
# These use the arrow keys themselves.
TEXT_WIDGET_CLASSES = ("TEntry", "TCombobox", "TSpinbox", "Entry", "Listbox", "Spinbox")
INSPECTOR_TABS = ("Signals", "Panels", "Lines", "Figure", "Data")
DEFAULT_LINE_WIDTH = "1.4"
SAMPLE_AXIS_LABEL = "Sample"
CONTROL_MASK = 0x4
# Tk reports Command as Mod1 on macOS. Elsewhere that bit is Alt or NumLock.
COMMAND_MASK = 0x8


class Keys(namedtuple("Keys", "modifier label")):
    """The platform's command modifier, for bindings and for showing shortcuts."""

    def text(self, key):
        return f"{self.label}+{key}"

    @property
    def add_to_selection_mask(self):
        """The modifier bits of a click that adds to a selection."""
        return CONTROL_MASK | (COMMAND_MASK if self.modifier == "Command" else 0)


def platform_keys(widget):
    if widget.tk.call("tk", "windowingsystem") == "aqua":
        return Keys("Command", "Cmd")
    return Keys("Control", "Ctrl")


def with_format_extension(path, format_name):
    """Give a bare filename the extension of the format chosen in the save dialog."""
    if os.path.splitext(path)[1]:
        return path
    return path + dict(FIGURE_FORMATS)[format_name].lstrip("*")


def merged_title(signals):
    """Name every merged signal, with the unit once if they all share it."""
    units = {c.unit.get().strip() for c in signals}
    unit = units.pop() if len(units) == 1 else ""
    names = " \u00b7 ".join(c.display_name() for c in signals)
    return f"{names}  [{unit}]" if unit else names


def export_file_name(title):
    """The figure title, without what file systems refuse."""
    return re.sub(r'[\\/:*?"<>|]+', " ", title).strip() or "figure"


def overlay_title(chosen):
    """How many runs, and the deepest folder holding all of them."""
    # Run folders always use "/", so posixpath splits them on every platform.
    shared = posixpath.commonpath([run.folder for run in chosen])
    return f"{len(chosen)} runs in {shared}" if shared else f"{len(chosen)} runs"


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.keys = platform_keys(self)

        self.arrays = {}
        self.path = None
        # The signals.json the signal names came from, None when typed or defaulted.
        self.names_path = None
        self.channels = []
        # Every logged signal seen so far, by index. A log with fewer signals leaves the rest
        # here, so they come back as they were on the next log that has them.
        self.known_channels = {}
        # Channel indices as the signal list shows them. self.channels itself stays in matrix
        # order, which names files and saved layouts rely on.
        self.signal_order = []
        # Compared runs as the Lines tab shows them, and each run's colour once it has one.
        self.run_rank = []
        self.run_colors = {}
        # The title last set automatically. One that differs was typed, and stays.
        self.auto_title = ""
        # Set once the user picks these, so that new logs leave them alone.
        self.time_chosen = False
        self.orientation_forced = None
        # The names the current log's file holds, by variable.
        self.log_names = {}
        # Which folders were open when the filter was last empty.
        self.open_folders = set()
        self.filter_was_on = False
        # Set when the order changes while overlaid, for the panels of the single-run view.
        self._panels_follow_order = False
        self.panels = []
        self.applied_orientation = "rows"
        self.runs = []
        # Tree item id -> Run, for the runs the filter lets through.
        self.run_items = {}
        # Paths of the runs plotted from the run list, so a repeated selection is a no-op.
        self.shown_runs = ()
        # Set while several runs are plotted together: (runs, channels overlaid).
        self.overlay = None
        # What the overlay panels were laid out for: (channel indices, layout, grid runs).
        self.overlay_layout = None
        # Matrices of the overlaid runs, by path, so adding one run loads only that run.
        self.run_matrices = {}
        # The panel layout in use before that, so one run can be shown again.
        self.single_layout = None
        self.current_run = None
        # A file opened directly, so the layouts can apply to it like to a run.
        self.file_run = None
        # Panel -> its axes in the current figure.
        self.panel_axes = {}
        self._pending_relayout = None
        # Set while several steps of one change each ask for a redraw.
        self._draw_held = False
        self._pending_draw = None
        self._pending_select = None
        # Legend text and style per line, keyed by (run path, channel uid). The single-run
        # view uses "" for the run, so the looks carry over while stepping through runs.
        self.line_looks = {}
        # (panel, look, colour) for every line in the figure, in drawing order.
        self.drawn_lines = []
        # What the Lines tab rows were built for, so typing in them does not rebuild them.
        self.line_rows_shown = None
        self.line_swatches = {}
        # The runs in the Lines tab's run order, while several are compared.
        self.compared_runs = []

        self.prefs, prefs_problem = self._load_prefs()
        self._place_window()
        self.sidebar_width = prefs.saved_int(self.prefs, "sidebar_width", px(SIDEBAR_WIDTH),
                                             *PANE_WIDTH_LIMITS)
        self.inspector_width = prefs.saved_int(self.prefs, "inspector_width", px(INSPECTOR_WIDTH),
                                               *PANE_WIDTH_LIMITS)
        self._make_variables()
        self._build_header()
        self.split = ttk.PanedWindow(self, orient="horizontal")
        self.split.grid(row=2, column=0, sticky="nsew")
        self._build_sidebar()
        self._build_plot()
        self._build_inspector()
        self._build_status()
        self._build_menu()
        self._bind_keys()
        self.split.bind("<Map>", self._place_sashes)
        if not self.inspector_shown.get():
            self.split.forget(self.inspector)
        self.bind_all("<Return>", lambda _e: self.draw())
        master.report_callback_exception = self._report_exception
        self._watch((self.title, self.xlabel, self.linewidth, self.xmin, self.xmax,
                     self.columns))
        if prefs_problem:
            self.status.configure(text=prefs_problem, foreground=ERROR)

    def _make_variables(self):
        self.variable = tk.StringVar()
        self.orientation = tk.StringVar(value="rows")
        self.time_source = tk.StringVar()
        self.title = tk.StringVar()
        # Blank takes the label of the time signal.
        self.xlabel = tk.StringVar()
        self.columns = tk.IntVar(value=1)
        self.panel_count = tk.IntVar(value=1)
        self.linewidth = tk.StringVar(value=DEFAULT_LINE_WIDTH)
        self.auto_x = tk.BooleanVar(value=True)
        self.xmin = tk.StringVar()
        self.xmax = tk.StringVar()
        self.link_x = tk.BooleanVar(value=True)
        self.crosshair_on = tk.BooleanVar(value=True)
        self.run_layout = tk.StringVar(value=OVERLAY)
        self.runs_folder = tk.StringVar()
        roomy = self.master.winfo_screenwidth() >= px(INSPECTOR_MIN_WINDOW_WIDTH)
        self.inspector_shown = tk.BooleanVar(value=self.prefs.get("inspector_shown", roomy)
                                             is not False)
        saved_tab = self.prefs.get("inspector_tab")
        self.inspector_tab = tk.StringVar(value=saved_tab if saved_tab in INSPECTOR_TABS
                                          else INSPECTOR_TABS[0])
        saved_preset = self.prefs.get("export_preset")
        self.export_preset = tk.StringVar(value=saved_preset if saved_preset in EXPORT_PRESETS
                                          else EXPORT_AS_SHOWN)
        self.export_width = tk.StringVar(value=str(self.prefs.get("export_width", "16")))
        self.export_height = tk.StringVar(value=str(self.prefs.get("export_height", "9")))
        self.export_dpi = tk.StringVar(value=str(self.prefs.get("export_dpi",
                                                                DEFAULT_EXPORT_DPI)))
        self.run_filter = tk.StringVar()
        self.run_filter.trace_add("write", lambda *_trace: self.fill_run_tree())

    def _adopt(self, channel):
        self._watch(channel.variables())
        for variable in (channel.name, channel.unit):
            variable.trace_add("write", lambda *_trace, c=channel: self._renamed(c))

    def _renamed(self, channel):
        """Carry a new name to the panel titles, time list and overlay list showing the old."""
        old, new = channel.shown_label, channel.label()
        channel.shown_label = new
        if old:
            for panel in self.panels:
                if panel.title.get() == old:
                    panel.title.set(new)
        if not channel.derived:
            self.refresh_time_sources()
            self.signal_list.rename(str(channel.index), new)

    def _watch(self, variables):
        """Redraw whenever one of these changes, once the edits pause."""
        for variable in variables:
            variable.trace_add("write", self.schedule_draw)

    # ---------- window ----------

    def _place_window(self):
        root = self.master
        root.title(APP_TITLE)
        root.minsize(px(MIN_WINDOW[0]), px(MIN_WINDOW[1]))
        root.geometry(prefs.fitted_geometry(self.prefs.get("geometry"), root.winfo_screenwidth(),
                                            root.winfo_screenheight(), px(DEFAULT_WINDOW[0]),
                                            px(DEFAULT_WINDOW[1])))

    def _build_header(self):
        bar = ttk.Frame(self, padding=(px(12), px(8)))
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(2, weight=1)
        ttk.Button(bar, text="Open folder…", command=self.open_folder).grid(row=0, column=0)
        ttk.Button(bar, text="Open file…", command=self.open_file).grid(
            row=0, column=1, padx=(px(6), 0))
        layouts = ttk.Frame(bar)
        layouts.grid(row=0, column=2)
        ttk.Label(layouts, text="Layout", style="Muted.TLabel").pack(side="left", padx=(0, px(8)))
        segmented(layouts, self.run_layout, LAYOUT_CHOICES, self.replot_overlay).pack(side="left")
        reset = ttk.Button(bar, text="Reset\u2026", command=self.reset_setup)
        reset.grid(row=0, column=3, padx=(0, px(6)))
        Tooltip(reset, "Put names, colours, panels, orders and figure settings back to what the "
                       "log's own file says")
        toggle = ttk.Checkbutton(bar, text="Settings", style="Toggle.Toolbutton",
                                 variable=self.inspector_shown, command=self._apply_inspector,
                                 takefocus=False)
        toggle.grid(row=0, column=4, padx=(0, px(6)))
        Tooltip(toggle, f"Show or hide the settings on the right ({self.keys.label}+\\)")
        export = ttk.Button(bar, text="Export…", style="Accent.TButton",
                            command=self.save_figure)
        export.grid(row=0, column=5)
        Tooltip(export, f"Save the figure as PNG, PDF, SVG or EPS ({self.keys.label}+E)")
        divider(self).grid(row=1, column=0, sticky="ew")

    def _build_status(self):
        divider(self).grid(row=3, column=0, sticky="ew")
        self.status = ttk.Label(self, text="", foreground=INK_2, padding=(px(12), px(4)),
                                font="TkSmallCaptionFont")
        self.status.grid(row=4, column=0, sticky="ew")

    def _place_sashes(self, _event=None):
        """Give the panes their widths once on screen. Before that there is nothing to divide.

        From here the sashes belong to the user, so this runs only once.
        """
        self.split.unbind("<Map>")
        self.update_idletasks()
        self.split.sashpos(0, self.sidebar_width)
        self._place_inspector_sash()

    def _place_inspector_sash(self):
        if self.inspector_shown.get():
            self.split.sashpos(1, self.split.winfo_width() - self.inspector_width)

    def _apply_inspector(self):
        """Show or hide the settings pane; the plot takes the room."""
        shown = str(self.inspector) in self.split.panes()
        if self.inspector_shown.get() and not shown:
            self.split.add(self.inspector, weight=0)
            # The pane comes back with no width, and a sash can only move once it is laid out.
            self.update_idletasks()
            self._place_inspector_sash()
        elif not self.inspector_shown.get() and shown:
            self.inspector_width = self.split.winfo_width() - self.split.sashpos(1)
            self.split.forget(self.inspector)

    def _show_inspector_tab(self, name):
        self.inspector_shown.set(True)
        self._apply_inspector()
        self.inspector_tab.set(name)
        self._raise_inspector_tab()

    def _raise_inspector_tab(self):
        self.inspector_tabs[self.inspector_tab.get()].tkraise()

    # The left pane: what to plot.

    def _build_sidebar(self):
        side = ttk.PanedWindow(self.split, orient="vertical", width=px(SIDEBAR_WIDTH))
        self.split.add(side, weight=0)
        runs = ttk.Frame(side, padding=(px(12), px(10), px(8), px(6)))
        signals = ttk.Frame(side, padding=(px(12), px(10), px(8), px(6)))
        side.add(runs, weight=3)
        side.add(signals, weight=2)
        self._build_run_list(runs)
        self._build_signal_list(signals)

    def _build_run_list(self, frame):
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)
        head = ttk.Frame(frame)
        head.grid(row=0, column=0, sticky="ew")
        head.columnconfigure(1, weight=1)
        heading(head, "Runs").grid(row=0, column=0, sticky="w", padx=(0, px(8)))
        self.folder_label = ttk.Label(head, text="", style="Muted.TLabel")
        self.folder_label.grid(row=0, column=1, sticky="ew")
        Tooltip(self.folder_label, lambda _e: self.runs_folder.get())
        rescan = ttk.Button(head, text="Rescan", style="Ghost.TButton", command=self.scan_runs,
                            takefocus=False)
        rescan.grid(row=0, column=2)
        Tooltip(rescan, f"Look for new logs in this folder ({self.keys.label}+R)")

        self.filter_entry = ttk.Entry(frame, textvariable=self.run_filter)
        self.filter_entry.grid(row=1, column=0, sticky="ew", pady=px(6))
        add_placeholder(self.filter_entry, self.run_filter, "Filter runs")
        self.filter_entry.bind("<Escape>", lambda _e: self.run_filter.set(""))

        holder, self.run_tree = scrolling_tree(frame)
        holder.grid(row=2, column=0, sticky="nsew")
        self.run_tree.bind("<<TreeviewSelect>>", lambda _e: self.schedule_run_selection())
        self.run_tree.bind("<Up>", lambda _e: self.step_run(forward=False))
        self.run_tree.bind("<Down>", lambda _e: self.step_run(forward=True))
        self.run_tree.bind("<Shift-Button-1>", self._toggle_item)
        self.run_tree.bind("<Button-1>", self._click_run_row)
        Tooltip(self.run_tree, self._run_tip)
        self.no_folder = ttk.Label(frame, text="No folder open", style="Muted.TLabel")
        self.no_folder.grid(row=2, column=0)

        foot = ttk.Frame(frame)
        foot.grid(row=3, column=0, sticky="ew", pady=(px(4), 0))
        foot.columnconfigure(3, weight=1)
        for column, (text, command) in enumerate((("All", self.select_all_runs),
                                                  ("None", self.select_no_runs),
                                                  ("Invert", self.invert_runs))):
            ttk.Button(foot, text=text, style="Ghost.TButton", command=command,
                       takefocus=False).grid(row=0, column=column)
        self.run_count = ttk.Label(foot, text="", style="Small.TLabel", anchor="e")
        self.run_count.grid(row=0, column=3, sticky="ew")
        modifier = "⌘" if self.keys.modifier == "Command" else "Ctrl"
        ttk.Label(frame, text=f"{modifier}-click to compare runs  ·  ↑↓ to step",
                  style="Small.TLabel").grid(row=4, column=0, sticky="w", pady=(px(2), 0))

    def _run_tip(self, event):
        run = self.run_items.get(self.run_tree.identify_row(event.y))
        return run.name if run else ""

    def _build_signal_list(self, frame):
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        head = ttk.Frame(frame)
        head.grid(row=0, column=0, sticky="ew", pady=(0, px(4)))
        head.columnconfigure(0, weight=1)
        heading(head, "Signals").grid(row=0, column=0, sticky="w")
        ttk.Button(head, text="All", style="Ghost.TButton", command=self.check_all_signals,
                   takefocus=False).grid(row=0, column=1)
        ttk.Button(head, text="None", style="Ghost.TButton", command=self.check_no_signals,
                   takefocus=False).grid(row=0, column=2)
        self.signal_list = Checklist(frame, self.on_signal_toggle, self._pick_listed_color,
                                     self.on_signal_reorder,
                                     "Drag to reorder. Higher in the list is drawn in front, "
                                     "and gets a higher panel.")
        self.signal_list.grid(row=1, column=0, sticky="nsew")

    # The middle pane: the plot.

    def _build_plot(self):
        holder = ttk.Frame(self.split)
        self.split.add(holder, weight=1)
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)
        self.figure = Figure(figsize=PLOT_MIN_SIZE_INCHES, facecolor=SURFACE)
        self.canvas = FigureCanvasTkAgg(self.figure, master=holder)
        widget = self.canvas.get_tk_widget()
        widget.configure(background=SURFACE, highlightthickness=0)
        widget.grid(row=0, column=0, sticky="nsew")
        self.toolbar = PlotToolbar(self.canvas, holder)
        self.toolbar.build_bar(holder).grid(row=1, column=0, sticky="ew")
        self.crosshair = Crosshair(self.canvas)
        self.gestures = PlotGestures(self.canvas, self.toolbar)
        self.views = ViewMemory()
        self.canvas.mpl_connect("resize_event", self._schedule_relayout)
        self.empty_state = ttk.Frame(holder)
        self.empty_state.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.empty_content = ttk.Frame(self.empty_state)
        self.empty_content.place(relx=0.5, rely=0.42, anchor="center")
        self._fill_empty_state()

    def _fill_empty_state(self):
        """What the plot area offers before anything is plotted."""
        for widget in self.empty_content.winfo_children():
            widget.destroy()
        if self.runs:
            ttk.Label(self.empty_content, text="Pick a run",
                      style="Display.TLabel").pack(pady=(0, px(4)))
            ttk.Label(self.empty_content, text="Choose a run from the list on the left to plot "
                                               "it.", style="Muted.TLabel").pack()
            return
        ttk.Label(self.empty_content, text="Plot your MATLAB logs",
                  style="Display.TLabel").pack(pady=(0, px(4)))
        ttk.Label(self.empty_content, text="Open a folder to browse and compare every run in "
                                           "it, or a single .mat file.",
                  style="Muted.TLabel").pack(pady=(0, px(14)))
        buttons = ttk.Frame(self.empty_content)
        buttons.pack()
        ttk.Button(buttons, text="Open folder\u2026", style="Accent.TButton",
                   command=self.open_folder).pack(side="left", padx=px(3))
        ttk.Button(buttons, text="Open file\u2026", command=self.open_file).pack(
            side="left", padx=px(3))
        recent = prefs.existing_recent(self.prefs)
        if recent:
            ttk.Label(self.empty_content, text="Recent", style="Small.TLabel").pack(
                pady=(px(20), px(2)))
            for path in recent[:EMPTY_STATE_RECENT]:
                ttk.Button(self.empty_content, text=os.path.basename(path) or path,
                           style="Ghost.TButton", command=lambda p=path: self.open_path(p)).pack()

    def _schedule_relayout(self, _event):
        if self._pending_relayout:
            self.after_cancel(self._pending_relayout)
        self._pending_relayout = self.after(RELAYOUT_DELAY_MS, self._relayout)

    def _relayout(self):
        self._pending_relayout = None
        if self.figure.axes:
            figure_builder.relayout(self.figure)
            self.canvas.draw_idle()

    # The right pane: how it looks.

    def _build_inspector(self):
        self.inspector = ttk.Frame(self.split, padding=(px(12), px(10)),
                                   width=px(INSPECTOR_WIDTH))
        self.split.add(self.inspector, weight=0)
        self.inspector.columnconfigure(0, weight=1)
        self.inspector.rowconfigure(1, weight=1)
        builders = zip(INSPECTOR_TABS, (self._tab_signals, self._tab_panels, self._tab_lines,
                                        self._tab_figure, self._tab_data))
        segmented(self.inspector, self.inspector_tab,
                  [(name, name, None) for name in INSPECTOR_TABS],
                  self._raise_inspector_tab).grid(row=0, column=0, sticky="ew", pady=(0, px(10)))
        self.inspector_tabs = {}
        for name, builder in builders:
            frame = ttk.Frame(self.inspector)
            frame.grid(row=1, column=0, sticky="nsew")
            frame.columnconfigure(0, weight=1)
            builder(frame)
            self.inspector_tabs[name] = frame
        self._raise_inspector_tab()

    def _tab_data(self, frame):
        heading(frame, "File").grid(row=0, column=0, sticky="w")
        box = ttk.Frame(frame)
        box.grid(row=1, column=0, sticky="ew", pady=(px(6), 0))
        box.columnconfigure(1, weight=1)
        self.file_label = wrapping_label(box, text="No file loaded", style="Muted.TLabel")
        self.file_label.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, px(6)))

        ttk.Label(box, text="Variable", style="Muted.TLabel").grid(row=1, column=0, sticky="w",
                                                                   padx=(0, px(8)))
        self.variable_box = ttk.Combobox(box, textvariable=self.variable, state="readonly")
        self.variable_box.grid(row=1, column=1, sticky="ew", pady=px(2))
        self.variable_box.bind("<<ComboboxSelected>>", lambda _e: self.select_variable())

        ttk.Label(box, text="Signals in", style="Muted.TLabel").grid(row=2, column=0, sticky="w",
                                                                     padx=(0, px(8)))
        orient = ttk.Frame(box)
        orient.grid(row=2, column=1, sticky="w", pady=px(2))
        for text in ("rows", "columns"):
            ttk.Radiobutton(orient, text=text, value=text, variable=self.orientation,
                            command=self._orientation_chosen).pack(side="left", padx=(0, px(10)))

        ttk.Label(box, text="Time from", style="Muted.TLabel").grid(row=3, column=0, sticky="w",
                                                                    padx=(0, px(8)))
        self.time_box = ttk.Combobox(box, textvariable=self.time_source, state="readonly")
        self.time_box.grid(row=3, column=1, sticky="ew", pady=px(2))
        self.time_box.bind("<<ComboboxSelected>>", lambda _e: self._time_chosen())

        self.shape_label = ttk.Label(box, text="", style="Small.TLabel")
        self.shape_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(px(6), 0))

    def _tab_signals(self, frame):
        frame.rowconfigure(1, weight=1)
        buttons = ttk.Frame(frame)
        buttons.grid(row=0, column=0, sticky="ew")
        derived = ttk.Button(buttons, text="+ Derived signal", command=self.add_derived)
        derived.pack(side="left")
        Tooltip(derived, "A new signal computed from the others, for example 2 * ch1 - ch2")
        ttk.Button(buttons, text="One panel each", command=self.one_panel_each).pack(
            side="left", padx=px(6))
        holder, self.signal_frame = scrollable(frame)
        holder.grid(row=1, column=0, sticky="nsew", pady=(px(8), 0))
        self.signal_frame.columnconfigure(1, weight=1)
        self.expression_help = wrapping_label(frame, text="", style="Small.TLabel")
        self.expression_help.grid(row=2, column=0, sticky="ew", pady=(px(6), 0))
        self.names_label = wrapping_label(frame, text="", style="Small.TLabel")
        self.names_label.grid(row=3, column=0, sticky="ew", pady=(px(6), 0))
        names = ttk.Frame(frame)
        names.grid(row=4, column=0, sticky="ew", pady=(px(4), 0))
        ttk.Button(names, text="Save names…", style="Ghost.TButton",
                   command=self.save_names).pack(side="left")
        ttk.Button(names, text="Load names…", style="Ghost.TButton",
                   command=self.load_names).pack(side="left", padx=px(4))

    def _tab_panels(self, frame):
        frame.rowconfigure(1, weight=1)
        head = ttk.Frame(frame)
        head.grid(row=0, column=0, sticky="ew")
        ttk.Label(head, text="Panels", style="Muted.TLabel").pack(side="left")
        ttk.Spinbox(head, from_=1, to=MAX_PANELS, width=4, textvariable=self.panel_count,
                    command=self.set_panel_count).pack(side="left", padx=(px(6), px(14)))
        ttk.Label(head, text="Columns", style="Muted.TLabel").pack(side="left")
        ttk.Spinbox(head, from_=1, to=4, width=4, textvariable=self.columns,
                    command=self.draw).pack(side="left", padx=px(6))
        holder, self.panel_frame = scrollable(frame)
        holder.grid(row=1, column=0, sticky="nsew", pady=(px(8), 0))
        self.panel_frame.columnconfigure(0, weight=1)

    def _tab_lines(self, frame):
        frame.rowconfigure(2, weight=1)
        head = ttk.Frame(frame)
        head.grid(row=0, column=0, sticky="ew")
        head.columnconfigure(0, weight=1)
        heading(head, "Legend and line style").grid(row=0, column=0, sticky="w")
        ttk.Button(head, text="Reset all", style="Ghost.TButton", command=self.reset_lines).grid(
            row=0, column=1)
        wrapping_label(frame, text="Clear a line's text to leave it out of the legend.",
                       style="Small.TLabel").grid(row=1, column=0, sticky="ew", pady=(px(2), 0))
        holder, self.line_frame = scrollable(frame)
        holder.grid(row=2, column=0, sticky="nsew", pady=(px(8), 0))

    def _range_row(self, parent, row, text, auto, low, high, current):
        """An axis range: automatic, or two limits filled from `current()` when turned off."""
        boxes = ttk.Frame(parent)
        boxes.grid(row=row, column=1, sticky="w", pady=px(2))
        low_entry = ttk.Entry(boxes, textvariable=low, width=9)
        low_entry.pack(side="left")
        ttk.Label(boxes, text="to", style="Muted.TLabel").pack(side="left", padx=px(5))
        high_entry = ttk.Entry(boxes, textvariable=high, width=9)
        high_entry.pack(side="left")

        def refresh():
            state = "disabled" if auto.get() else "normal"
            low_entry.configure(state=state)
            high_entry.configure(state=state)

        def toggled():
            limits = current()
            if not auto.get() and not low.get() and not high.get() and limits:
                low.set(f"{limits[0]:.6g}")
                high.set(f"{limits[1]:.6g}")
            refresh()
            self.draw()

        ttk.Checkbutton(parent, text=text, variable=auto, command=toggled).grid(
            row=row, column=0, sticky="w", padx=(0, px(8)))
        refresh()
        return refresh

    def _current_x_limits(self):
        return self.figure.axes[0].get_xlim() if self.figure.axes else None

    def _tab_figure(self, frame):
        frame.rowconfigure(0, weight=1)
        holder, body = scrollable(frame)
        holder.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        heading(body, "Figure").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, px(6)))
        labelled_entry(body, 1, "Title", self.title)
        add_placeholder(labelled_entry(body, 2, "X label", self.xlabel), self.xlabel,
                        "From the time signal")
        ttk.Label(body, text="Line width", style="Muted.TLabel").grid(row=3, column=0, sticky="w")
        ttk.Entry(body, textvariable=self.linewidth, width=6).grid(row=3, column=1, sticky="w",
                                                                   pady=px(2))
        self._refresh_x_range = self._range_row(body, 4, "X auto", self.auto_x, self.xmin,
                                                self.xmax, self._current_x_limits)
        ttk.Checkbutton(body, text="Linked x axes", variable=self.link_x,
                        command=self.draw).grid(row=5, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(body, text="Cursor readout", variable=self.crosshair_on,
                        command=self.toggle_crosshair).grid(row=6, column=0, columnspan=2,
                                                            sticky="w")

        heading(body, "Export").grid(row=7, column=0, columnspan=2, sticky="w",
                                     pady=(px(18), px(6)))
        ttk.Label(body, text="Size", style="Muted.TLabel").grid(row=8, column=0, sticky="w")
        preset = ttk.Combobox(body, textvariable=self.export_preset, state="readonly",
                              values=list(EXPORT_PRESETS))
        preset.grid(row=8, column=1, sticky="ew", pady=px(2))
        preset.bind("<<ComboboxSelected>>", lambda _e: self._apply_export_preset())
        size = ttk.Frame(body)
        size.grid(row=9, column=1, sticky="w", pady=px(2))
        self.export_width_entry = ttk.Entry(size, textvariable=self.export_width, width=6)
        self.export_width_entry.pack(side="left")
        ttk.Label(size, text="×", style="Muted.TLabel").pack(side="left", padx=px(4))
        self.export_height_entry = ttk.Entry(size, textvariable=self.export_height, width=6)
        self.export_height_entry.pack(side="left")
        ttk.Label(size, text="cm", style="Muted.TLabel").pack(side="left", padx=px(4))
        ttk.Label(body, text="PNG dpi", style="Muted.TLabel").grid(row=10, column=0, sticky="w")
        ttk.Combobox(body, textvariable=self.export_dpi, values=EXPORT_DPIS, width=6).grid(
            row=10, column=1, sticky="w", pady=px(2))
        self._apply_export_preset()
        ttk.Button(body, text="Export figure…", style="Accent.TButton",
                   command=self.save_figure).grid(row=11, column=0, columnspan=2, sticky="ew",
                                                  pady=(px(8), px(2)))
        ttk.Button(body, text="Export CSV…", command=self.export_csv).grid(
            row=12, column=0, columnspan=2, sticky="ew", pady=px(2))

        heading(body, "Settings file").grid(row=13, column=0, columnspan=2, sticky="w",
                                            pady=(px(18), px(6)))
        files = ttk.Frame(body)
        files.grid(row=14, column=0, columnspan=2, sticky="ew")
        files.columnconfigure((0, 1), weight=1, uniform="files")
        ttk.Button(files, text="Save…", command=self.save_settings).grid(
            row=0, column=0, sticky="ew", padx=(0, px(3)))
        ttk.Button(files, text="Load…", command=self.load_settings).grid(
            row=0, column=1, sticky="ew", padx=(px(3), 0))

    def _apply_export_preset(self):
        """A named size fills in the numbers; only Custom lets them be typed."""
        size = EXPORT_PRESETS.get(self.export_preset.get())
        if size:
            self.export_width.set(f"{size[0]:g}")
            self.export_height.set(f"{size[1]:g}")
        state = "normal" if self.export_preset.get() == EXPORT_CUSTOM else "disabled"
        self.export_width_entry.configure(state=state)
        self.export_height_entry.configure(state=state)

    # Menus and keys.

    def _build_menu(self):
        bar = tk.Menu(self.master)
        self.master.configure(menu=bar)
        files = tk.Menu(bar, tearoff=False)
        bar.add_cascade(label="File", menu=files)
        files.add_command(label="Open Folder…", accelerator=self.keys.text("Shift+O"),
                          command=self.open_folder)
        files.add_command(label="Open File…", accelerator=self.keys.text("O"),
                          command=self.open_file)
        self.recent_menu = tk.Menu(files, tearoff=False, postcommand=self._fill_recent_menu)
        files.add_cascade(label="Open Recent", menu=self.recent_menu)
        files.add_separator()
        files.add_command(label="Export Figure…", accelerator=self.keys.text("E"),
                          command=self.save_figure)
        files.add_command(label="Export CSV…", command=self.export_csv)
        files.add_separator()
        files.add_command(label="Save Settings…", accelerator=self.keys.text("S"),
                          command=self.save_settings)
        files.add_command(label="Load Settings…", command=self.load_settings)
        if self.keys.modifier != "Command":
            files.add_separator()
            files.add_command(label="Quit", accelerator=self.keys.text("Q"), command=self.quit_app)

        view = tk.Menu(bar, tearoff=False)
        bar.add_cascade(label="View", menu=view)
        for position, (value, text, _tip) in enumerate(LAYOUT_CHOICES, start=1):
            view.add_radiobutton(label=text, value=value, variable=self.run_layout,
                                 accelerator=self.keys.text(str(position)),
                                 command=self.replot_overlay)
        view.add_separator()
        view.add_checkbutton(label="Settings Pane", variable=self.inspector_shown,
                             accelerator=self.keys.text("\\"), command=self._apply_inspector)
        view.add_command(label="Reset Zoom", accelerator="Double-click plot",
                         command=self.toolbar.home)
        view.add_command(label="Rescan Folder", accelerator=self.keys.text("R"),
                         command=self.scan_runs)
        view.add_separator()
        view.add_command(label="Reset Setup\u2026", command=self.reset_setup)

        helping = tk.Menu(bar, tearoff=False)
        bar.add_cascade(label="Help", menu=helping)
        helping.add_command(label="Mouse and Keyboard", command=self._show_shortcuts)

    def _fill_recent_menu(self):
        self.recent_menu.delete(0, "end")
        recent = prefs.existing_recent(self.prefs)
        for path in recent:
            self.recent_menu.add_command(label=path, command=lambda p=path: self.open_path(p))
        if not recent:
            self.recent_menu.add_command(label="Nothing yet", state="disabled")

    def _bind_keys(self):
        root = self.master
        for key, command in (("o", self.open_file), ("O", self.open_folder),
                             ("e", self.save_figure), ("s", self.save_settings),
                             ("r", self.scan_runs), ("f", self.filter_entry.focus_set),
                             ("q", self.quit_app), ("backslash", self._toggle_inspector)):
            root.bind(f"<{self.keys.modifier}-{key}>",
                      lambda _e, c=command: (c(), "break")[1])
        for position, (value, _text, _tip) in enumerate(LAYOUT_CHOICES, start=1):
            root.bind(f"<{self.keys.modifier}-Key-{position}>",
                      lambda _e, v=value: self._choose_layout(v))
        root.bind("<Up>", lambda e: self._arrow_key(e, forward=False))
        root.bind("<Down>", lambda e: self._arrow_key(e, forward=True))
        root.protocol("WM_DELETE_WINDOW", self.quit_app)
        if self.keys.modifier == "Command":
            # Cmd-Q goes through this rather than the window's close button.
            root.createcommand("::tk::mac::Quit", self.quit_app)

    def _toggle_inspector(self):
        self.inspector_shown.set(not self.inspector_shown.get())
        self._apply_inspector()

    def _choose_layout(self, value):
        self.run_layout.set(value)
        self.replot_overlay()

    def _arrow_key(self, event, forward):
        """Up and Down step through the runs from anywhere but a field that uses them."""
        widget = event.widget
        # Tk's combobox dropdown is not a tkinter object, and event.widget is then a string.
        if isinstance(widget, str) or widget.winfo_class() in TEXT_WIDGET_CLASSES:
            return None
        return self.step_run(forward)

    def _show_shortcuts(self):
        key = self.keys.text
        messagebox.showinfo("Mouse and keyboard", "\n".join((
            "Plot",
            "  Scroll: zoom time around the pointer",
            "  Shift + scroll: zoom the y axis",
            "  Double-click: reset the zoom",
            "  Hover a line: read its value",
            "  The zoom is kept while stepping through runs.",
            "",
            "Runs",
            "  ↑ ↓: step through the runs",
            f"  {self.keys.label}-click or Shift-click: add or drop a run",
            "  Click a folder: open or close it",
            f"  {self.keys.label}-click a folder: select every run in it",
            f"  {key('F')}: filter the runs, Esc clears it",
            f"  {key('1')}…{key('4')}: choose the layout",
            "",
            "Files",
            f"  {key('O')}: open a file    {key('Shift+O')}: open a folder",
            f"  {key('E')}: export the figure    {key('S')}: save settings",
            f"  {key('R')}: rescan the folder    {key(chr(92))}: settings pane",
            "",
            "Order",
            "  Drag a signal's handle to reorder it. Higher is drawn in front.",
            "  Compared runs are reordered at the top of the Lines tab.")))

    # Remembering the session.

    def _load_prefs(self):
        """The saved preferences. A damaged file costs the settings, not the session."""
        try:
            return prefs.load(), None
        except ValueError as exc:
            return {}, f"Preferences not loaded: {exc}"

    def _remember(self, **values):
        self.prefs.update(values)
        self._save_prefs()

    def _save_prefs(self):
        try:
            prefs.save(self.prefs)
        except OSError as exc:
            self.status.configure(text=f"Preferences not saved: {exc}", foreground=ERROR)

    def _remember_recent(self, path):
        self._remember(recent=prefs.with_recent(prefs.existing_recent(self.prefs), path))

    def quit_app(self):
        root = self.master
        self.prefs.update(
            geometry=root.geometry(),
            sidebar_width=self.split.sashpos(0), inspector_shown=self.inspector_shown.get(),
            inspector_tab=self.inspector_tab.get(), export_preset=self.export_preset.get(),
            export_width=self.export_width.get(), export_height=self.export_height.get(),
            export_dpi=self.export_dpi.get())
        if self.inspector_shown.get():
            self.prefs["inspector_width"] = self.split.winfo_width() - self.split.sashpos(1)
        else:
            self.prefs["inspector_width"] = self.inspector_width
        try:
            prefs.save(self.prefs)
        except OSError as exc:
            # The window is closing, so stderr is the only place left to say so.
            print(f"Preferences not saved: {exc}", file=sys.stderr)
        root.destroy()

    def _report_exception(self, kind, value, trace):
        """Show errors from event handlers: a windowed exe has no console to print them on."""
        traceback.print_exception(kind, value, trace)
        self.status.configure(text=f"Unexpected error: {value}", foreground=ERROR)

    # ---------- loading ----------

    def open_path(self, path):
        """Open a recent entry, whichever kind it is."""
        if os.path.isdir(path):
            self.open_folder(path)
        else:
            self.open_file(path)

    def open_file(self, path=None):
        path = path or filedialog.askopenfilename(
            title="Open MATLAB file", filetypes=[("MATLAB files", "*.mat"), ("All files", "*")])
        if not path:
            return
        try:
            log = data.load_log(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Cannot read file", f"{path}\n\n{exc}")
            return
        overlaid = self.overlay is not None
        ticked = set(self.signal_list.checked())
        self.forget_runs()
        self.file_run = runs_module.Run(path, os.path.dirname(path))
        self._remember_recent(path)
        with self._one_redraw():
            self._show_log(log, path, self.file_run.label)
            if overlaid:
                self._back_to_single_view(ticked)
        self.draw()

    def _show_log(self, log, path, title):
        """Make this log the current one. Everything the user has set up stays."""
        self.overlay = None
        self.overlay_layout = None
        self.run_matrices = {}
        self.arrays = log.arrays
        self.log_names = log.names
        self.path = path
        self._show_file_name(path)
        self.variable_box.configure(values=list(log.arrays))
        if self.variable.get() not in log.arrays:
            self.variable.set(next(iter(log.arrays)))
        self._set_auto_title(title)
        self.select_variable()

    def _set_auto_title(self, title):
        """Set the figure title, unless the user has typed their own."""
        if self.title.get() == self.auto_title:
            self.title.set(title)
        self.auto_title = title

    def _show_file_name(self, path):
        name = os.path.basename(path)
        self.file_label.configure(text=path)
        self.master.title(f"{name} \u2014 {APP_TITLE}")

    def select_variable(self):
        """Point at a variable and orient it so the short dimension holds the channels."""
        array = self.arrays[self.variable.get()]
        self.orientation.set(self.orientation_forced or data.natural_orientation(array))
        self.rebuild_channels()

    def _orientation_chosen(self):
        self.orientation_forced = self.orientation.get()
        self.rebuild_channels()

    def _time_chosen(self):
        self.time_chosen = True
        self.draw()

    def matrix(self):
        return data.orient(self.arrays[self.variable.get()], self.orientation.get())

    @contextmanager
    def _one_redraw(self):
        """Let several steps each ask for a redraw, without drawing until the caller does."""
        held = self._draw_held
        self._draw_held = True
        try:
            yield
        finally:
            self._draw_held = held

    def rebuild_channels(self):
        """Fit the signals to the current log, keeping whatever is set up for them."""
        if not self.arrays or not self.variable.get():
            return
        matrix = self.matrix()
        if matrix.shape[0] > data.MAX_CHANNELS:
            messagebox.showwarning(
                "Too many channels",
                f"'{self.variable.get()}' read with signals in {self.orientation.get()} gives "
                f"{matrix.shape[0]} channels; the limit is {data.MAX_CHANNELS}.\n\n"
                f"The other orientation gives {matrix.shape[1]} channels.")
            self.orientation.set(self.applied_orientation)
            return
        self.applied_orientation = self.orientation.get()

        fresh = not self.channels
        before = len(self.raw_channels())
        added = self._fit_channels(matrix.shape[0])
        self.apply_names_for(self.path)
        self.refresh_time_sources()
        if not self.time_chosen:
            self._detect_time(matrix)
        self.shape_label.configure(
            text=f"{matrix.shape[0]} channels \u00d7 {matrix.shape[1]} samples")
        if fresh:
            self.one_panel_each()
            return
        for channel in added:
            if self._plots_by_default(channel):
                self._give_panel(channel)
        if added or before != matrix.shape[0]:
            self.draw_panel_rows()
            self.draw_signal_rows()
        self.draw()

    def _fit_channels(self, count):
        """Make self.channels cover `count` logged signals. Returns those never seen before."""
        added = []
        for index in range(count):
            if index not in self.known_channels:
                channel = Channel("", palette_color(index), index=index,
                                  expression=f"channel {index}", panel=HIDDEN)
                self._adopt(channel)
                self.known_channels[index] = channel
                added.append(channel)
        derived = [c for c in self.channels if c.derived]
        self.channels = [self.known_channels[index] for index in range(count)] + derived
        return added

    def _every_channel(self):
        """The signals of this log and the ones waiting for a log that has them."""
        return list(self.known_channels.values()) + [c for c in self.channels if c.derived]

    def _detect_time(self, matrix):
        row = data.time_row(matrix, [c.name.get() for c in self.raw_channels()])
        self.time_source.set(self.time_box.cget("values")[0 if row is None else row + 1])

    def _plots_by_default(self, channel):
        """Not the time vector. If some signals are named, a blank name marks an unused input."""
        any_named = any(c.name.get().strip() for c in self.raw_channels())
        return channel.index != self.time_index() and (
            channel.name.get().strip() or channel.derived or not any_named)

    def refresh_time_sources(self):
        # Track the choice by channel index: the labels change whenever signals are renamed.
        keep = self.time_index()
        sources = ["Sample index"] + [f"{c.index}: {c.display_name()}"
                                      for c in self.raw_channels()]
        self.time_box.configure(values=sources)
        self.time_source.set(sources[keep + 1] if keep is not None and keep + 1 < len(sources)
                             else sources[0])

    # ---------- runs folder ----------

    def open_folder(self, folder=None):
        folder = folder or filedialog.askdirectory(
            title="Folder of run logs", initialdir=self.runs_folder.get() or os.getcwd())
        if not folder:
            return
        self.runs_folder.set(folder)
        self.run_tree.selection_set(())
        if self.scan_runs():
            self._remember_recent(folder)

    def scan_runs(self):
        """Look through the folder again. Returns whether it held any runs."""
        folder = self.runs_folder.get()
        if not folder:
            self.status.configure(text="No folder is open.", foreground=INK_2)
            return False
        try:
            self.runs = runs_module.discover(folder)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Cannot read run folder", str(exc))
            return False
        # The files may have changed on disk, so the selection is loaded afresh.
        self.shown_runs = ()
        self.run_matrices = {}
        self.fill_run_tree()
        self.no_folder.grid_remove()
        self._fill_empty_state()
        self.folder_label.configure(text=os.path.basename(os.path.normpath(folder)))
        folders = len({run.folder for run in self.runs})
        self.status.configure(text=f"{len(self.runs)} runs in {folders} folders under {folder}",
                              foreground=INK_2)
        return True

    def fill_run_tree(self):
        """The runs the filter lets through, under their folders, keeping the selection."""
        tree = self.run_tree
        kept = tree.selection()
        text = self.run_filter.get().strip()
        # A filter opens every folder to show its matches, which is not the user's choice.
        if not self.filter_was_on:
            self.open_folders = {item for item in self._tree_order()
                                 if item.startswith(FOLDER_PREFIX) and tree.item(item, "open")}
        self.filter_was_on = bool(text)
        tree.delete(*tree.get_children())
        self.run_items = {}
        for run in self.runs:
            if text and not run.matches(text):
                continue
            tree.insert(self._folder_item(run.folder), "end", iid=run.path, text=run.name)
            self.run_items[run.path] = run
        tree.selection_set([item for item in kept if tree.exists(item)])
        self._count_folder_runs()
        self._show_run_count()

    def _count_folder_runs(self):
        """Put the number of runs below each folder after its name."""
        for item in self._tree_order():
            if item.startswith(FOLDER_PREFIX):
                below = sum(1 for child in self._tree_order(item) if child in self.run_items)
                name = item[len(FOLDER_PREFIX):].rpartition("/")[2]
                self.run_tree.item(item, text=f"{name}  ({below})")

    def _show_run_count(self):
        selected = len(self.selected_runs())
        listed = len(self.run_items)
        if selected > 1:
            text = f"{selected} of {listed} selected"
        elif listed != len(self.runs):
            text = f"{listed} of {len(self.runs)} runs"
        else:
            text = f"{listed} runs"
        self.run_count.configure(text=text if self.runs else "")

    def _folder_item(self, folder):
        """The tree item for a folder, made along with its parents when missing."""
        if not folder:
            return ""
        item = FOLDER_PREFIX + folder
        if not self.run_tree.exists(item):
            parent, _slash, name = folder.rpartition("/")
            self.run_tree.insert(self._folder_item(parent), "end", iid=item, text=name,
                                 open=self.filter_was_on or item in self.open_folders)
        return item

    def _click_run_row(self, event):
        """A click on a folder opens or closes it; adding it to the selection takes a modifier."""
        tree = self.run_tree
        item = tree.identify_row(event.y)
        if not item.startswith(FOLDER_PREFIX) or event.state & self.keys.add_to_selection_mask:
            return None
        tree.item(item, open=not tree.item(item, "open"))
        tree.focus(item)
        return "break"

    def _tree_order(self, item=""):
        """Every item below `item`, in the order the tree shows them."""
        order = []
        for child in self.run_tree.get_children(item):
            order.append(child)
            order.extend(self._tree_order(child))
        return order

    def selected_runs(self):
        """The selected runs plus every run in a selected folder, in list order."""
        picked = set()
        for item in self.run_tree.selection():
            picked.update([item] + self._tree_order(item))
        return [run for item, run in self.run_items.items() if item in picked]

    def select_all_runs(self):
        self.run_tree.selection_set(list(self.run_items))

    def select_no_runs(self):
        self.run_tree.selection_set(())

    def invert_runs(self):
        chosen = {run.path for run in self.selected_runs()}
        self.run_tree.selection_set([item for item in self.run_items if item not in chosen])

    def step_run(self, forward):
        """Move to the next run in the list, skipping folders."""
        order = self._tree_order()
        # Selections made by the buttons or the filter leave no focus; start from them.
        focus = self.run_tree.focus() or next(iter(self.run_tree.selection()), "")
        if focus in order:
            position = order.index(focus)
            ahead = order[position + 1:] if forward else reversed(order[:position])
        else:
            ahead = order
        target = next((item for item in ahead if item in self.run_items), None)
        if target is not None:
            self.run_tree.selection_set(target)
            self.run_tree.focus(target)
            self.run_tree.see(target)
        return "break"

    def schedule_run_selection(self):
        if self._pending_select:
            self.after_cancel(self._pending_select)
        self._pending_select = self.after(SELECT_DELAY_MS, self.apply_run_selection)

    def apply_run_selection(self):
        """Plot what the run list selects: one run on its own, several overlaid."""
        self._pending_select = None
        self._show_run_count()
        chosen = self.selected_runs()
        if chosen:
            self.file_run = None
        elif self.file_run:
            chosen = [self.file_run]
        paths = tuple(run.path for run in chosen)
        if not chosen or paths == self.shown_runs:
            return
        if len(chosen) > 1:
            shown = self.plot_overlay(chosen)
        elif self.run_layout.get() != OVERLAY:
            # Loading first gives the run its names and the layout to return to.
            with self._one_redraw():
                loaded = self.load_run(chosen[0])
            shown = loaded and self.plot_overlay(chosen)
        else:
            shown = self.load_run(chosen[0])
        if shown:
            self.shown_runs = paths

    def forget_runs(self):
        """Leave the run list behind, for a file opened or settings loaded directly."""
        self.overlay = None
        self.overlay_layout = None
        self.run_matrices = {}
        self.shown_runs = ()
        self.current_run = None
        self.file_run = None
        self.views.forget()
        self.run_tree.selection_set(())

    def load_run(self, run):
        """Show one run on its own, as set up so far. Returns whether it could be read."""
        try:
            log = data.load_log(run.path)
        except (OSError, ValueError) as exc:
            self.status.configure(text=f"Cannot load {run.label}: {exc}", foreground=ERROR)
            return False
        variable = self.variable.get() if self.variable.get() in log.arrays else next(
            iter(log.arrays))
        array = log.arrays[variable]
        rows = data.orient(array, self.orientation_forced
                           or data.natural_orientation(array)).shape[0]
        if rows > data.MAX_CHANNELS:
            self.status.configure(text=f"Cannot load {run.label}: '{variable}' has {rows} "
                                       f"channels, the limit is {data.MAX_CHANNELS}.",
                                  foreground=ERROR)
            return False
        overlaid = self.overlay is not None
        ticked = set(self.signal_list.checked())
        self.current_run = run
        self.variable.set(variable)
        with self._one_redraw():
            self._show_log(log, run.path, run.label)
            if overlaid:
                self._back_to_single_view(ticked)
        self.draw()
        return True

    def _back_to_single_view(self, ticked):
        """Leave a comparison. The ticks stay as they are, so the same signals stay on screen."""
        self.show_single_layout()
        if ticked:
            self._plot_ticked(ticked)

    def show_single_layout(self):
        """Put back the panels in use before the runs were overlaid. Nothing else changes."""
        if not self.single_layout:
            self.one_panel_each()
            return
        assignments, panels, columns = self.single_layout
        self.columns.set(columns)
        self._resize_panels(len(panels))
        for panel, saved in zip(self.panels, panels):
            panel.restore(saved)
        for channel in self._every_channel():
            number, label = assignments.get(channel.uid, (HIDDEN, ""))
            channel.panel.set(number)
            # A rename made while overlaid has to reach the titles coming back.
            if number != HIDDEN and self.panels[int(number) - 1].title.get() == label:
                self.panels[int(number) - 1].title.set(channel.label())
        if self._panels_follow_order:
            self._arrange_panels_by_order()
            self._panels_follow_order = False
        self.draw_panel_rows()
        self.draw_signal_rows()
        self.draw()

    def refresh_signal_list(self):
        """The signal list, keeping the ticks while runs are overlaid."""
        kept = set(self.signal_list.checked())
        self.signal_list.set_items([(str(c.index), c.label(), c.color.get())
                                    for c in self.ordered_raw_channels()])
        self.signal_list.set_checked(kept if self.overlay else self._plotted_keys())

    def _plotted_keys(self):
        return {str(c.index) for c in self.raw_channels() if c.panel.get() != HIDDEN}

    def overlay_signals(self):
        """The ticked signals. With none ticked, the ones plotted right now."""
        by_key = {str(c.index): c for c in self.raw_channels()}
        chosen = [by_key[key] for key in self.signal_list.checked()]
        if chosen or self.overlay:
            return chosen
        time_index = self.time_index()
        chosen = [c for c in by_key.values()
                  if c.panel.get() != HIDDEN and c.index != time_index]
        self.signal_list.set_checked({str(c.index) for c in chosen})
        return chosen

    @staticmethod
    def _toggle_item(event):
        """Shift-click adds or drops just the clicked row, not the range up to it."""
        tree = event.widget
        item = tree.identify_row(event.y)
        if item:
            tree.selection_toggle(item)
            tree.focus(item)
        return "break"

    def on_signal_toggle(self):
        """A tick was clicked: plot exactly the ticked signals, in whichever view is up."""
        ticked = set(self.signal_list.checked())
        if self.overlay:
            if {int(key) for key in ticked} != set(self.overlay_layout[0]):
                self.plot_overlay(self.overlay[0])
        else:
            self._plot_ticked(ticked)

    def check_all_signals(self):
        time_index = self.time_index()
        self.signal_list.set_checked({str(c.index) for c in self.raw_channels()
                                      if c.index != time_index})
        self.on_signal_toggle()

    def check_no_signals(self):
        self.signal_list.set_checked(())
        self.on_signal_toggle()

    def _plot_ticked(self, ticked):
        """Give each newly ticked signal a panel of its own and take unticked ones away.

        Signals already sharing a panel keep it, so a layout set up in the Signals tab
        survives ticking something else.
        """
        for channel in self.raw_channels():
            wanted = str(channel.index) in ticked
            shown = channel.panel.get() != HIDDEN
            if shown and not wanted:
                channel.panel.set(HIDDEN)
            elif wanted and not shown and not self._give_panel(channel):
                self.status.configure(text=f"Only {MAX_PANELS} panels fit; "
                                           f"{channel.display_name()} was left out.",
                                      foreground=ERROR)
        self._trim_panels()
        self.draw_panel_rows()
        self.draw_signal_rows()
        self.draw()

    def _give_panel(self, channel):
        """Put the channel on the first unused panel. Returns False when none can be added."""
        used = {c.panel.get() for c in self._every_channel()}
        panel = next((p for p in self.panels if str(p.number) not in used), None)
        if panel is None:
            if len(self.panels) >= MAX_PANELS:
                return False
            self._resize_panels(len(self.panels) + 1)
            panel = self.panels[-1]
        panel.title.set(channel.label())
        channel.panel.set(str(panel.number))
        return True

    def _trim_panels(self):
        """Drop unused panels from the end, so the Panels tab lists what is on screen."""
        used = {c.panel.get() for c in self._every_channel()}
        count = len(self.panels)
        while count > 1 and str(count) not in used:
            count -= 1
        self._resize_panels(count)

    def on_signal_reorder(self, keys):
        """A signal was dragged: it changes what is in front, and the order of the panels."""
        self.signal_order = [int(key) for key in keys]
        if self.overlay:
            self._panels_follow_order = True
            self.plot_overlay(self.overlay[0])
        else:
            self._arrange_panels_by_order()
            self.draw_panel_rows()
            self.draw()
        self.draw_signal_rows()

    def _arrange_panels_by_order(self):
        """Put the panels in the order of the first signal listed on each."""
        numbers = []
        for channel in self.ordered_channels():
            number = channel.panel.get()
            if number != HIDDEN and number not in numbers:
                numbers.append(number)
        by_number = {str(panel.number): panel for panel in self.panels}
        unused = [panel for number, panel in by_number.items() if number not in numbers]
        arranged = [by_number[number] for number in numbers] + unused
        renumbered = {str(panel.number): str(position)
                      for position, panel in enumerate(arranged, start=1)}
        for channel in self._every_channel():
            if channel.panel.get() != HIDDEN:
                channel.panel.set(renumbered[channel.panel.get()])
        for position, panel in enumerate(arranged, start=1):
            panel.number = position
        self.panels = arranged

    @staticmethod
    def _valid_order(order, count):
        """Whether `order` lists each of `count` channels once. It may come from a file."""
        return (isinstance(order, list) and all(type(i) is int for i in order)
                and sorted(order) == list(range(count)))

    def _pick_listed_color(self, key):
        self.pick_color(next(c for c in self.channels if str(c.index) == key and not c.derived))

    def plot_overlay(self, chosen):
        """Lay the selected signals of these runs out. Returns whether it plotted."""
        # The signal names and panels come from a loaded log, so the first run sets them up.
        if not self.channels and not self.load_run(chosen[0]):
            return False
        chosen = self._ordered_runs(chosen)
        signals = self.overlay_signals()
        layout = self.run_layout.get()
        panel_count = {OVERLAY: len(signals), MERGED: 1, GRID: len(signals) * len(chosen),
                       SIDE_BY_SIDE: len(chosen)}[layout]
        try:
            if not signals:
                raise ValueError("Select at least one signal to overlay.")
            if panel_count > MAX_PANELS:
                raise ValueError(f"that takes {panel_count} panels; the limit is {MAX_PANELS}. "
                                 "Select fewer signals or runs, or merge them into one panel.")
            matrices = {run.path: (self.run_matrices[run.path] if run.path in self.run_matrices
                                   else self._run_matrix(run))
                        for run in chosen}
        except (OSError, ValueError) as exc:
            self.status.configure(text=f"Cannot overlay runs: {exc}", foreground=ERROR)
            return False
        if not self.overlay:
            self.single_layout = ({c.uid: (c.panel.get(), c.label())
                                   for c in self._every_channel()},
                                  [p.state() for p in self.panels], int(self.columns.get()))
        self.run_matrices = matrices
        self._give_runs_colors(chosen)
        # Compared logs can hold different numbers of signals; the list shows the most.
        rows = max(matrix.shape[0] for matrix in matrices.values())
        if rows != len(self.raw_channels()):
            self._fit_channels(rows)
            self.draw_signal_rows()
        self.overlay = (chosen, signals)
        self._set_auto_title(chosen[0].label if len(chosen) == 1 else overlay_title(chosen))
        # Grid and side by side have a column per run, so there the runs shape the panels too.
        shape = (tuple(c.index for c in signals), layout,
                 tuple(run.path for run in chosen) if layout in (GRID, SIDE_BY_SIDE) else ())
        # Only a new shape relays the panels, so titles and limits typed for the overlay
        # survive adding or dropping runs.
        if shape != self.overlay_layout:
            self.overlay_layout = shape
            self._lay_out(layout, chosen, signals)
            self.draw_panel_rows()
        self.draw()
        return True

    def _lay_out(self, layout, chosen, signals):
        """Size and title the panels for the run layout."""
        short = runs_module.short_labels(chosen)
        if layout == GRID:
            self.columns.set(len(chosen))
            self._resize_panels(len(signals) * len(chosen))
            # Row-major: each signal's row holds one panel per run.
            cells = [(channel, run) for channel in signals for run in chosen]
            for panel, (channel, run) in zip(self.panels, cells):
                panel.span.set(False)
                panel.legend.set(False)
                panel.title.set(channel.label() if len(chosen) == 1
                                else f"{channel.label()} \u2014 {short[run.path]}")
            return
        if layout == SIDE_BY_SIDE:
            self.columns.set(len(chosen))
            self._resize_panels(len(chosen))
            for panel, run in zip(self.panels, chosen):
                panel.span.set(False)
                panel.legend.set(True)
                panel.title.set(merged_title(signals) if len(chosen) == 1 else short[run.path])
            return
        self.columns.set(self.single_layout[2])
        if layout == MERGED:
            self._resize_panels(1)
            self.panels[0].title.set(merged_title(signals))
            self.panels[0].legend.set(True)
        else:
            self._resize_panels(len(signals))
            for position, (panel, channel) in enumerate(zip(self.panels, signals)):
                panel.title.set(channel.label())
                # Every panel has the same runs, so one legend says it for all of them.
                panel.legend.set(position == 0)

    def _ordered_runs(self, chosen):
        """These runs as ordered in the Lines tab. Runs not yet moved keep their list order."""
        rank = {path: position for position, path in enumerate(self.run_rank)}
        return sorted(chosen, key=lambda run: rank.get(run.path, len(rank)))

    def _give_runs_colors(self, chosen):
        """A run keeps its colour when others join or leave the comparison."""
        taken = {self.run_colors[run.path] for run in chosen if run.path in self.run_colors}
        free = [color for color in PALETTE if color not in taken]
        for run in chosen:
            if run.path not in self.run_colors:
                self.run_colors[run.path] = (free.pop(0) if free
                                             else palette_color(len(self.run_colors)))

    def on_run_reorder(self, paths):
        """A compared run was dragged: higher is drawn in front, and comes first in the legend."""
        self.run_rank = paths + [path for path in self.run_rank if path not in paths]
        self.plot_overlay(self.overlay[0])

    def _pick_run_color(self, path):
        chosen = colorchooser.askcolor(color=self.run_colors[path], title="Run colour")[1]
        if chosen:
            self.run_colors[path] = chosen
            self.draw()

    def replot_overlay(self):
        """The layout decides the panels, and for a single run whether it is overlaid at all."""
        self.shown_runs = ()
        self.apply_run_selection()

    def _run_matrix(self, run):
        try:
            arrays = data.load_log(run.path).arrays
        except ValueError as exc:
            raise ValueError(f"{run.label}: {exc}")
        variable = self.variable.get()
        array = arrays[variable if variable in arrays else next(iter(arrays))]
        return data.orient(array, self.orientation_forced or data.natural_orientation(array))

    # ---------- signals tab ----------

    def draw_signal_rows(self):
        self.refresh_signal_list()
        for widget in self.signal_frame.winfo_children():
            widget.destroy()
        for column, text in enumerate(("", "Name", "Unit", "Panel", "Scale", "Offset", "")):
            ttk.Label(self.signal_frame, text=text, style="Small.TLabel").grid(
                row=0, column=column, padx=px(2), sticky="w")
        choices = [HIDDEN] + [str(p.number) for p in self.panels]
        self.expression_entries = {}
        row = 1
        for channel in self.ordered_channels():
            swatch(self.signal_frame, channel.color.get(),
                   lambda c=channel: self.pick_color(c)).grid(row=row, column=0, padx=(0, px(4)))
            name = ttk.Entry(self.signal_frame, textvariable=channel.name, width=8)
            name.grid(row=row, column=1, padx=px(1), pady=px(1), sticky="ew")
            add_placeholder(name, channel.name, channel.display_name())
            ttk.Entry(self.signal_frame, textvariable=channel.unit, width=5).grid(
                row=row, column=2, padx=px(1))
            ttk.Combobox(self.signal_frame, textvariable=channel.panel, values=choices,
                         width=6, state="readonly").grid(row=row, column=3, padx=px(1))
            ttk.Entry(self.signal_frame, textvariable=channel.scale, width=4).grid(
                row=row, column=4, padx=px(1))
            ttk.Entry(self.signal_frame, textvariable=channel.offset, width=4).grid(
                row=row, column=5, padx=px(1))
            row += 1
            if channel.derived:
                ttk.Label(self.signal_frame, text="=", style="Muted.TLabel").grid(
                    row=row, column=0, sticky="e", padx=(0, px(4)))
                entry = ttk.Entry(self.signal_frame, textvariable=channel.expression,
                                  font="TkFixedFont")
                entry.grid(row=row, column=1, columnspan=5, sticky="ew", padx=px(1),
                           pady=(0, px(4)))
                self.expression_entries[channel.uid] = entry
                ttk.Button(self.signal_frame, text="\u00d7", style="Ghost.TButton", width=2,
                           command=lambda c=channel: self.remove_channel(c), takefocus=False).grid(
                    row=row, column=6)
                row += 1
        self._show_expression_help()

    def _show_expression_help(self):
        """The names an expression can use, only once there is an expression to write."""
        if not any(c.derived for c in self.channels):
            self.expression_help.configure(text="")
            self.expression_help.grid_remove()
            return
        named = [expressions.identifier(c.name.get()) for c in self.raw_channels()
                 if c.name.get().strip()]
        count = len(self.raw_channels())
        usable = ", ".join(["t", f"ch0 to ch{count - 1}"] + named)
        self.expression_help.grid()
        self.expression_help.configure(
            text=f"Expressions can use {usable}, and sin cos tan exp log sqrt abs clip where "
                 "cumsum deg rad deriv(x) smooth(x, n).")

    def pick_color(self, channel):
        chosen = colorchooser.askcolor(color=channel.color.get(),
                                       title=channel.display_name())[1]
        if chosen:
            channel.color.set(chosen)
            self.draw_signal_rows()
            self.draw()

    def add_derived(self):
        if not self.channels:
            messagebox.showinfo("No file", "Open a .mat file first.")
            return
        position = len(self.channels)
        channel = Channel("", palette_color(position), panel=HIDDEN)
        self._adopt(channel)
        self.channels.append(channel)
        if not self.overlay:
            # Otherwise typing the expression would show nothing.
            self._give_panel(channel)
            self.draw_panel_rows()
        self.draw_signal_rows()
        self.draw()
        self._show_inspector_tab("Signals")
        entry = self.expression_entries[channel.uid]
        entry.focus_set()
        self.status.configure(text="Type an expression for the new signal. It plots once you "
                                   "stop typing.", foreground=INK_2)

    def remove_channel(self, channel):
        self.channels.remove(channel)
        self._trim_panels()
        self.draw_panel_rows()
        self.draw_signal_rows()
        self.draw()

    def one_panel_each(self):
        """Give every plottable signal its own panel."""
        plotted = [c for c in self.ordered_channels() if self._plots_by_default(c)]
        self.panel_count.set(max(1, min(len(plotted), MAX_PANELS)))
        self.set_panel_count()
        for channel in self._every_channel():
            channel.panel.set(HIDDEN)
        for position, channel in enumerate(plotted[:MAX_PANELS]):
            channel.panel.set(str(position + 1))
            self.panels[position].title.set(channel.label())
        self.draw_signal_rows()
        self.draw()

    def raw_channels(self):
        return [c for c in self.channels if not c.derived]

    def ordered_raw_channels(self):
        """The logged signals in the order the signal list shows them."""
        rank = {index: position for position, index in enumerate(self.signal_order)}
        return sorted(self.raw_channels(), key=lambda c: rank.get(c.index, len(rank) + c.index))

    def ordered_channels(self):
        """Every signal in list order. Derived ones are not listed, and come last."""
        return self.ordered_raw_channels() + [c for c in self.channels if c.derived]

    def apply_names_for(self, path):
        """Name the signals from the signals.json nearest above `path`, else from the log itself.

        Neither one has names for a log? Then the ones already showing stay. A name typed by
        hand always stays.
        """
        problem = ""
        found = names_module.find(os.path.dirname(path))
        if found:
            try:
                pairs = names_module.load(found)
                self._check_name_count(found, pairs)
            except (OSError, ValueError) as exc:
                problem = f"Not applied: {exc}"
            else:
                self._follow_names(pairs)
                self.names_path = found
                self.names_label.configure(text=f"Names from {found}", foreground=INK_2)
                return
        embedded = self.log_names.get(self.variable.get())
        self.names_path = None
        if embedded and len(embedded) == len(self.raw_channels()):
            self._follow_names(embedded)
            self.names_label.configure(text=problem or "Names from the log file.",
                                       foreground=ERROR if problem else INK_2)
            return
        self.names_label.configure(
            text=problem or "This log holds no signal names. Type them above; Save names\u2026 "
                            f"as {names_module.NAMES_FILE} keeps them for the folder.",
            foreground=ERROR if problem else INK_2)

    def _follow_names(self, pairs):
        for channel, (name, unit) in zip(self.raw_channels(), pairs):
            channel.take_file_name(name, unit)

    def _check_name_count(self, path, pairs):
        count = len(self.raw_channels())
        if len(pairs) != count:
            raise ValueError(f"{path} names {len(pairs)} signals, this log has {count}")

    def _set_names(self, pairs):
        for channel, (name, unit) in zip(self.raw_channels(), pairs):
            channel.force_name(name, unit)

    def _names_folder(self):
        """Where Save names… starts: the file in use, else the run's experiment folder."""
        if self.names_path:
            return os.path.dirname(self.names_path)
        if self.current_run and self.current_run.folder:
            return os.path.join(self.runs_folder.get(), self.current_run.folder.split("/")[0])
        return os.path.dirname(self.path) if self.path else os.getcwd()

    def save_names(self):
        if not self.channels:
            messagebox.showinfo("No file", "Open a .mat file first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save signal names", initialdir=self._names_folder(),
            initialfile=names_module.NAMES_FILE, defaultextension=".json",
            filetypes=[("Signal names", "*.json")])
        if not path:
            return
        names_module.save(path, [(c.name.get(), c.unit.get()) for c in self.raw_channels()])
        found = names_module.find(os.path.dirname(self.path))
        if found and os.path.samefile(found, path):
            self.names_path = found
            self.names_label.configure(text=f"Names from {path}", foreground=INK_2)
        else:
            self.names_label.configure(
                text=f"Saved {path}, but runs only pick up a file named "
                     f"{names_module.NAMES_FILE} in their own folder or one above it.",
                foreground=ERROR)

    def load_names(self):
        if not self.channels:
            messagebox.showinfo("No file", "Open a .mat file first.")
            return
        path = filedialog.askopenfilename(title="Load signal names",
                                          initialdir=self._names_folder(),
                                          filetypes=[("Signal names", "*.json")])
        if not path:
            return
        try:
            pairs = names_module.load(path)
            self._check_name_count(path, pairs)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Cannot load names", str(exc))
            return
        self._set_names(pairs)
        self.names_path = os.path.abspath(path)
        self.names_label.configure(text=f"Names from {path}", foreground=INK_2)
        self.draw()

    # ---------- panels tab ----------

    def set_panel_count(self):
        self._resize_panels(int(self.panel_count.get()))
        self.draw_panel_rows()
        self.draw_signal_rows()
        self.draw()

    def _resize_panels(self, count):
        count = max(1, min(count, MAX_PANELS))
        self.panel_count.set(count)
        while len(self.panels) < count:
            panel = Panel(len(self.panels) + 1)
            self._watch(panel.variables())
            self.panels.append(panel)
        del self.panels[count:]
        for channel in self._every_channel():
            if channel.panel.get() != HIDDEN and int(channel.panel.get()) > count:
                channel.panel.set(HIDDEN)

    def draw_panel_rows(self):
        for widget in self.panel_frame.winfo_children():
            widget.destroy()
        for row, panel in enumerate(self.panels):
            box = ttk.Frame(self.panel_frame, padding=(0, 0, 0, px(14)))
            box.grid(row=row, column=0, sticky="ew")
            box.columnconfigure(1, weight=1)
            heading(box, f"Panel {panel.number}").grid(row=0, column=0, columnspan=4, sticky="w",
                                                       pady=(0, px(4)))
            labelled_entry(box, 1, "Title", panel.title)
            labelled_entry(box, 2, "Y label", panel.ylabel)
            self._range_row(box, 3, "Y auto", panel.auto_y, panel.ymin, panel.ymax,
                            lambda p=panel: self._current_y_limits(p))
            options = ttk.Frame(box)
            options.grid(row=4, column=0, columnspan=4, sticky="w", pady=(px(2), 0))
            for text, variable in (("Legend", panel.legend), ("Grid", panel.grid),
                                   ("Full width", panel.span)):
                ttk.Checkbutton(options, text=text, variable=variable,
                                command=self.draw).pack(side="left", padx=(0, px(12)))
            ttk.Label(box, text="Time axis", style="Muted.TLabel").grid(row=5, column=0, sticky="w")
            ttk.Combobox(box, textvariable=panel.xlabels, values=XLABEL_MODES, width=8,
                         state="readonly").grid(row=5, column=1, sticky="w", pady=px(2))

    def _current_y_limits(self, panel):
        ax = self.panel_axes.get(id(panel))
        return ax.get_ylim() if ax is not None else None

    # ---------- drawing ----------

    def time_index(self):
        if not self.time_source.get() or self.time_source.get().startswith("Sample"):
            return None
        return int(self.time_source.get().split(":")[0])

    def time_vector(self, matrix):
        index = self.time_index()
        return np.arange(matrix.shape[1], dtype=float) if index is None else matrix[index]

    def computed(self):
        """Every channel's plotted values, expressions resolved in order."""
        matrix = self.matrix()
        t = self.time_vector(matrix)
        namespace = expressions.make_namespace(t, {})
        for channel in self.raw_channels():
            namespace[f"ch{channel.index}"] = matrix[channel.index]
            if channel.name.get().strip():
                namespace[expressions.identifier(channel.name.get())] = matrix[channel.index]
        values = {}
        for channel in self.channels:
            raw = (matrix[channel.index] if not channel.derived
                   else self._derived_values(channel, namespace, t))
            if channel.derived and channel.name.get().strip():
                namespace[expressions.identifier(channel.name.get())] = raw
            values[id(channel)] = channel.transform(raw)
        return t, values

    @staticmethod
    def _derived_values(channel, namespace, t):
        """A derived signal with no expression yet plots nothing, rather than failing."""
        if not channel.expression.get().strip():
            return np.full(len(t), np.nan)
        return expressions.evaluate(channel.expression.get(), namespace, channel.display_name())

    def schedule_draw(self, *_trace):
        if self._pending_draw:
            self.after_cancel(self._pending_draw)
        self._pending_draw = self.after(DRAW_DELAY_MS, self.draw)

    def draw(self):
        if self._pending_draw:
            self.after_cancel(self._pending_draw)
            self._pending_draw = None
        if self._draw_held or not self.channels:
            return
        self.empty_state.grid_remove()
        previous_lines = self.drawn_lines
        self.drawn_lines = []
        self.compared_runs = []
        try:
            self._draw_overlay() if self.overlay else self._draw()
        except ValueError as exc:
            # The last good plot stays up, so a half-typed expression does not blank it.
            self.drawn_lines = previous_lines
            self.status.configure(text=str(exc), foreground=ERROR)
            return
        self.canvas.draw()

    def _draw(self):
        t, values = self.computed()
        series = {id(p): [] for p in self.panels}
        for depth, channel in enumerate(self.ordered_channels()):
            if channel.panel.get() == HIDDEN:
                continue
            panel = self.panels[int(channel.panel.get()) - 1]
            line = self._line(panel, ("", channel.uid), channel.label(), channel.color.get(),
                              "-", t, values[id(channel)], depth)
            if line is not None:
                series[id(panel)].append(line)
        self.signal_list.set_checked(self._plotted_keys())
        drawn = self._render(series)
        if not drawn:
            return
        step = np.diff(t)
        self.status.configure(
            text=f"{sum(len(series[id(p)]) for p in drawn)} signals in {len(drawn)} panels, "
                 f"{len(t)} samples" + (f", step {step.mean():.4g}" if step.size else ""),
            foreground=INK_2)

    def _draw_overlay(self):
        """Every selected run drawn on the same panels, coloured and labelled by run."""
        chosen, signals = self.overlay
        layout = self.run_layout.get()
        merged = layout == MERGED
        self.compared_runs = chosen if len(chosen) > 1 else []
        # One run has no other runs to tell apart, so its lines keep their signal colours.
        single = len(chosen) == 1
        index = self.time_index()
        short = runs_module.short_labels(chosen)
        # By channel, not list position: dragging a signal must not change its dash pattern.
        dash_rank = {c.index: rank
                     for rank, c in enumerate(sorted(signals, key=lambda c: c.index))}
        series = {id(p): [] for p in self.panels}
        for position, run in enumerate(chosen):
            matrix = self.run_matrices[run.path]
            if index is not None and index >= matrix.shape[0]:
                raise ValueError(f"run {run.name} has only {matrix.shape[0]} channels, "
                                 f"time was asked for from channel {index}")
            t = np.arange(matrix.shape[1], dtype=float) if index is None else matrix[index]
            for order, channel in enumerate(signals):
                # Compared logs can differ in length; a shorter one has no line for this signal.
                if channel.index >= matrix.shape[0]:
                    continue
                panel = self.panels[{OVERLAY: order, MERGED: 0,
                                     GRID: order * len(chosen) + position,
                                     SIDE_BY_SIDE: position}[layout]]
                # Side by side, the panel already names the run, and every panel colours
                # the same signal alike.
                if single or layout == SIDE_BY_SIDE:
                    label, color, style = channel.display_name(), channel.color.get(), "-"
                else:
                    label = (short[run.path] if layout == OVERLAY
                             else f"{short[run.path]} \u00b7 {channel.display_name()}")
                    color = self.run_colors[run.path]
                    style = line_style(dash_rank[channel.index]) if merged else "-"
                key = ("" if single else run.path, channel.uid)
                line = self._line(panel, key, label, color, style, t,
                                  channel.transform(matrix[channel.index]),
                                  order + position / len(chosen))
                if line is not None:
                    series[id(panel)].append(line)
        drawn = self._render(series)
        if not drawn:
            return
        self.status.configure(
            text=(f"{len(signals)} signals" + (" merged" if merged else "") if single
                  else f"{len(chosen)} runs \u00d7 {len(signals)} signals"
                       + {GRID: " in a grid", SIDE_BY_SIDE: " side by side"}.get(layout, "")),
            foreground=INK_2)

    def _render(self, series):
        """Lay the non-empty panels out and draw them. Returns the panels drawn."""
        drawn = [p for p in self.panels if series[id(p)]]
        # Everything that can be mistyped is read first, so a bad value leaves the plot up.
        auto_x = self.auto_x.get()
        settings = {
            "title": self.title.get(),
            "xlabel": self.xlabel.get().strip() or self._time_axis_label(),
            "linewidth": parse_float(self.linewidth.get(), "Line width"),
            "link_x": self.link_x.get(), "auto_x": auto_x,
            "xmin": parse_limit(self.xmin.get(), "X min") if not auto_x else None,
            "xmax": parse_limit(self.xmax.get(), "X max") if not auto_x else None,
        }
        for panel in drawn:
            if not panel.auto_y.get():
                panel.ymin_value()
                panel.ymax_value()
        columns = self._column_count()

        self.views.capture()
        self.figure.clear()
        self.crosshair.attach([])
        self.panel_axes = {}
        if not drawn:
            self.figure.text(0.5, 0.5, "Tick a signal on the left to plot it.", ha="center",
                             va="center", color=INK_2)
            self.status.configure(text="No signal is assigned to a panel.", foreground=INK_2)
            self.refresh_line_rows()
            return []
        placements, rows = figure_builder.place(drawn, columns)
        axes = figure_builder.draw(self.figure, placements, rows, columns, series, settings)
        self.panel_axes = axes
        # Before the zoom goes back on, as the crosshair's lines can move an automatic axis.
        self.crosshair.attach([(axes[id(p)], series[id(p)]) for p in drawn],
                              settings["linewidth"])
        self.views.reapply({self._view_key(p): axes[id(p)] for p in drawn}, self.toolbar)
        self.refresh_line_rows()
        return drawn

    def _time_axis_label(self):
        index = self.time_index()
        if index is None:
            return SAMPLE_AXIS_LABEL
        channel = self.known_channels.get(index)
        return channel.label() if channel and channel.name.get().strip() else ""

    def _column_count(self):
        try:
            return max(1, int(self.columns.get()))
        except tk.TclError:
            raise ValueError("Columns: type a whole number")

    def _view_key(self, panel):
        """A zoom holds for this panel only while nothing was typed that overrules it."""
        return (id(panel), panel.title.get(), self.auto_x.get(), self.xmin.get(), self.xmax.get(),
                panel.auto_y.get(), panel.ymin.get(), panel.ymax.get())

    def _line(self, panel, key, auto_label, color, auto_style, t, values, depth):
        """One Series, with whatever legend text, style and colour the user gave this line.

        None for a line unticked in the Lines tab. It still gets its row there, to tick it back.
        """
        look = self.line_looks.get(key)
        if look is None:
            look = self.line_looks[key] = LineLook(auto_label)
            self._watch(look.variables())
        legend, style, color = look.resolve(auto_label, auto_style, color)
        self.drawn_lines.append((panel, look, color))
        if not look.shown.get():
            return None
        return figure_builder.Series(auto_label, legend, color, style, t, values, depth)

    def refresh_line_rows(self):
        """One row per plotted line in the Lines tab, under its panel."""
        runs = [(run.path, self.run_colors[run.path]) for run in self.compared_runs]
        layout = ([(id(panel), id(look)) for panel, look, _color in self.drawn_lines], runs)
        if layout == self.line_rows_shown:
            for _panel, look, color in self.drawn_lines:
                self.line_swatches[id(look)].configure(background=color)
            return
        self.line_rows_shown = layout
        for widget in self.line_frame.winfo_children():
            widget.destroy()
        self.line_swatches = {}
        self.line_frame.columnconfigure(2, weight=1)
        # One run's lines are ticked on and off in the signal list already.
        tickable = bool(self.compared_runs)
        row = self._show_run_order()
        for panel in self.panels:
            lines = [(look, color) for drawn, look, color in self.drawn_lines if drawn is panel]
            if not lines:
                continue
            head = ttk.Frame(self.line_frame)
            head.grid(row=row, column=0, columnspan=4, sticky="ew",
                      pady=(px(12) if row else 0, px(2)))
            heading(head, f"Panel {panel.number}").pack(side="left")
            ttk.Label(head, textvariable=panel.title, style="Muted.TLabel").pack(
                side="left", padx=px(6))
            ttk.Checkbutton(head, text="Legend", variable=panel.legend,
                            command=self.draw).pack(side="right")
            row += 1
            for look, color in lines:
                if tickable:
                    shown = ttk.Checkbutton(self.line_frame, variable=look.shown,
                                            command=self.draw, takefocus=False)
                    shown.grid(row=row, column=0, padx=(0, px(2)), pady=px(1))
                    Tooltip(shown, "Untick to leave this line out of the plot")
                patch = swatch(self.line_frame, color, lambda k=look: self.pick_line_color(k))
                patch.grid(row=row, column=1, padx=(0, px(4)), pady=px(1))
                self.line_swatches[id(look)] = patch
                ttk.Entry(self.line_frame, textvariable=look.label, width=10).grid(
                    row=row, column=2, sticky="ew", pady=px(1))
                style = ttk.Combobox(self.line_frame, textvariable=look.style,
                                     values=list(LINE_STYLES), width=8, state="readonly")
                style.grid(row=row, column=3, padx=(px(4), 0), pady=px(1))
                style.bind("<<ComboboxSelected>>", lambda _e: self.draw())
                row += 1

    def _show_run_order(self):
        """The compared runs, draggable, above the lines. Returns the next free grid row."""
        if not self.compared_runs:
            return 0
        heading(self.line_frame, "Run order").grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Label(self.line_frame, text="Higher is drawn in front.", style="Small.TLabel").grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(0, px(2)))
        order = DragRows(self.line_frame, self._pick_run_color, self.on_run_reorder,
                         "Drag to reorder. Higher is drawn in front and comes first in the "
                         "legend.", scrolling=False)
        order.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(0, px(10)))
        short = runs_module.short_labels(self.compared_runs)
        order.set_items([(run.path, short[run.path], self.run_colors[run.path])
                         for run in self.compared_runs])
        return 3

    def pick_line_color(self, look):
        current = self.line_swatches[id(look)].cget("background")
        chosen = colorchooser.askcolor(color=current, title=look.label.get())[1]
        if chosen:
            look.color.set(chosen)
            self.draw()

    def reset_lines(self):
        for _panel, look, _color in self.drawn_lines:
            look.reset()
        self.draw()

    def toggle_crosshair(self):
        self.crosshair.enabled = self.crosshair_on.get()
        if not self.crosshair.enabled:
            self.crosshair.hide()

    # ---------- output ----------

    def visible_window(self):
        if not self.figure.axes:
            raise ValueError("nothing is plotted")
        return self.figure.axes[0].get_xlim()

    def _export_size(self):
        """(width, height) in cm for the chosen export size, None for as shown."""
        if self.export_preset.get() == EXPORT_AS_SHOWN:
            return None
        width = parse_float(self.export_width.get(), "Export width")
        height = parse_float(self.export_height.get(), "Export height")
        if width <= 0 or height <= 0:
            raise ValueError("Export size: width and height must be above zero")
        return width, height

    def _export_dpi(self):
        dpi = parse_float(self.export_dpi.get(), "Export dpi")
        if dpi <= 0:
            raise ValueError("Export dpi must be above zero")
        return dpi

    def _export_folder(self):
        saved = self.prefs.get("export_folder")
        if isinstance(saved, str) and os.path.isdir(saved):
            return saved
        return os.path.dirname(self.path) if self.path else os.getcwd()

    def _initial_export_format(self):
        saved = self.prefs.get("export_format")
        return saved if saved in dict(FIGURE_FORMATS) else FIGURE_FORMATS[0][0]

    def save_figure(self):
        if not self.figure.axes:
            messagebox.showinfo("Nothing to save", "Plot something first.")
            return
        try:
            size, dpi = self._export_size(), self._export_dpi()
        except ValueError as exc:
            self._show_inspector_tab("Figure")
            self.status.configure(text=str(exc), foreground=ERROR)
            return
        # No defaultextension: Tk's Linux dialog would add it whatever format is chosen,
        # saving a PNG when EPS was asked for.
        chosen = tk.StringVar(value=self._initial_export_format())
        typed = filedialog.asksaveasfilename(
            title="Export figure", filetypes=FIGURE_FORMATS, typevariable=chosen,
            initialdir=self._export_folder(), initialfile=export_file_name(self.title.get()))
        if not typed:
            return
        path = with_format_extension(typed, chosen.get())
        # The dialog only asked about overwriting the name it returned, not this one.
        if path != typed and os.path.exists(path) and not messagebox.askyesno(
                "Overwrite?", f"{os.path.basename(path)} already exists. Replace it?"):
            return
        try:
            self._write_figure(path, size, dpi)
        except (OSError, ValueError, RuntimeError) as exc:
            messagebox.showerror("Export failed", f"{path}\n\n{exc}")
            return
        self._remember(export_folder=os.path.dirname(os.path.abspath(path)),
                       export_format=chosen.get())
        shown_size = f" at {size[0]:g} \u00d7 {size[1]:g} cm" if size else ""
        self.status.configure(text=f"Saved {path}{shown_size}", foreground=INK_2)

    def _write_figure(self, path, size, dpi):
        undo = (figure_builder.flatten_alpha(self.figure, SURFACE)
                if path.lower().endswith(".eps") else None)
        # A fixed size is what was asked for, so it must not be cropped to the content.
        crop = "tight" if size is None else None
        try:
            with figure_builder.sized_for_export(self.figure, size):
                self.figure.savefig(path, dpi=dpi, bbox_inches=crop, facecolor=SURFACE)
        finally:
            if undo:
                undo()
            self.canvas.draw_idle()

    def export_csv(self):
        if self.overlay:
            messagebox.showinfo("Overlay plotted",
                                "CSV export writes one run in the Overlay layout. Select a single "
                                "run with Overlay chosen first.")
            return
        path = filedialog.asksaveasfilename(title="Export CSV", defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")],
                                            initialdir=self._export_folder(),
                                            initialfile=export_file_name(self.title.get()))
        if not path:
            return
        try:
            t, values = self.computed()
            columns = [(c.display_name(), values[id(c)]) for c in self.channels
                       if c.panel.get() != HIDDEN]
            written = store.export_csv(path, t, columns, self.visible_window())
        except ValueError as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        self.status.configure(text=f"wrote {written} rows to {path}", foreground=INK_2)

    def state(self):
        return dict(path=self.path, variable=self.variable.get(),
                    orientation=self.orientation.get(), time_source=self.time_source.get(),
                    title=self.title.get(), xlabel=self.xlabel.get(),
                    columns=int(self.columns.get()), linewidth=self.linewidth.get(),
                    auto_x=self.auto_x.get(), xmin=self.xmin.get(), xmax=self.xmax.get(),
                    link_x=self.link_x.get(), crosshair=self.crosshair_on.get(),
                    channels=[c.state() for c in self.channels],
                    panels=[p.state() for p in self.panels],
                    lines=self._line_states(), signal_order=self.signal_order,
                    export=dict(preset=self.export_preset.get(), width=self.export_width.get(),
                                height=self.export_height.get(), dpi=self.export_dpi.get()))

    def _line_states(self):
        """The single-run lines given their own legend, style or colour, by signal position."""
        position = {c.uid: i for i, c in enumerate(self.channels)}
        return [dict(signal=position[uid], label=look.label.get(), style=look.style.get(),
                     color=look.color.get())
                for (run, uid), look in self.line_looks.items()
                if run == "" and uid in position and look.edited()]

    def save_settings(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("Plot settings", "*.json")])
        if not path:
            return
        store.save_config(path, self.state())
        self.status.configure(text=f"settings saved to {path}", foreground=INK_2)

    def load_settings(self):
        path = filedialog.askopenfilename(filetypes=[("Plot settings", "*.json")])
        if not path:
            return
        try:
            self.restore(store.load_config(path))
        except (OSError, KeyError, ValueError) as exc:
            messagebox.showerror("Cannot load settings", f"{path}\n\n{exc}")
            return
        self.status.configure(text=f"settings loaded from {path}", foreground=INK_2)

    def restore(self, state):
        self.forget_runs()
        self.single_layout = None
        self.names_path = None
        self.names_label.configure(text="Names from the loaded settings.", foreground=INK_2)
        if state["path"] and state["path"] != self.path:
            log = data.load_log(state["path"])
            self.arrays = log.arrays
            self.log_names = log.names
            self.path = state["path"]
            self.file_run = runs_module.Run(self.path, os.path.dirname(self.path))
            self._show_file_name(self.path)
            self.variable_box.configure(values=list(self.arrays))
        self.variable.set(state["variable"])
        self.orientation.set(state["orientation"])
        self.applied_orientation = state["orientation"]

        self.panels = [Panel(i + 1) for i in range(len(state["panels"]))]
        for panel, saved in zip(self.panels, state["panels"]):
            panel.restore(saved)
            self._watch(panel.variables())
        self.panel_count.set(len(self.panels))

        self.channels = [Channel("", "#000000") for _ in state["channels"]]
        for channel, saved in zip(self.channels, state["channels"]):
            channel.restore(saved)
            self._adopt(channel)
        self.known_channels = {c.index: c for c in self.raw_channels()}
        # Everything in a settings file was chosen, so new logs must leave it alone.
        self.time_chosen = True
        self.orientation_forced = state["orientation"]
        self.auto_title = None
        # Settings saved before signals could be reordered have no "signal_order".
        raw_count = len(self.raw_channels())
        saved_order = state.get("signal_order")
        self.signal_order = (saved_order if self._valid_order(saved_order, raw_count)
                             else list(range(raw_count)))
        self.line_looks = {}
        # Settings saved before legends could be edited have no "lines".
        for saved in state.get("lines", []):
            # Settings saved before line colours could be picked have no "color".
            look = LineLook(label=saved["label"], style=saved["style"],
                            color=saved.get("color", ""))
            self._watch(look.variables())
            self.line_looks[("", self.channels[saved["signal"]].uid)] = look

        self.refresh_time_sources()
        self.time_source.set(state["time_source"])
        for name in ("title", "xlabel", "linewidth", "xmin", "xmax"):
            getattr(self, name).set(state[name])
        self.columns.set(state["columns"])
        self.auto_x.set(state["auto_x"])
        self.link_x.set(state["link_x"])
        self.crosshair_on.set(state["crosshair"])
        self.toggle_crosshair()
        self._refresh_x_range()
        # Settings saved before the export size could be chosen have no "export".
        export = state.get("export")
        if export:
            self.export_preset.set(export["preset"])
            self.export_width.set(export["width"])
            self.export_height.set(export["height"])
            self.export_dpi.set(export["dpi"])
            self._apply_export_preset()
        matrix = self.matrix()
        self.shape_label.configure(
            text=f"{matrix.shape[0]} channels × {matrix.shape[1]} samples")
        self.draw_panel_rows()
        self.draw_signal_rows()
        self.draw()

    # ---------- reset ----------

    def reset_setup(self):
        if not messagebox.askyesno(
                "Reset setup",
                "Put signal names, colours, panels, line styles, orders and figure settings back "
                "to what the log's own files say?\n\nThis cannot be undone. The open folder and "
                "the selected runs stay."):
            return
        self._clear_setup()
        if self.selected_runs() or self.file_run:
            self.apply_run_selection()
        elif self.arrays:
            self.select_variable()
        else:
            self.draw_panel_rows()
            self.draw_signal_rows()
            self.refresh_line_rows()
            self.empty_state.grid()
        self.status.configure(text="Setup reset.", foreground=INK_2)

    def _clear_setup(self):
        """Forget everything set up for the signals. Which logs are open stays."""
        self.known_channels = {}
        self.channels = []
        self.panels = []
        self.signal_order = []
        self.run_rank = []
        self.run_colors = {}
        self.line_looks = {}
        self.drawn_lines = []
        self.compared_runs = []
        self.line_rows_shown = None
        self.single_layout = None
        self.overlay = None
        self.overlay_layout = None
        self.run_matrices = {}
        self.shown_runs = ()
        self.names_path = None
        self.time_chosen = False
        self.orientation_forced = None
        self.views.forget()
        self.auto_title = ""
        self.title.set("")
        self.xlabel.set("")
        self.columns.set(1)
        self.linewidth.set(DEFAULT_LINE_WIDTH)
        self.auto_x.set(True)
        self.xmin.set("")
        self.xmax.set("")
        self.link_x.set(True)
        self.crosshair_on.set(True)
        self.toggle_crosshair()
        self._refresh_x_range()
        self.run_layout.set(OVERLAY)
        self.figure.clear()
        self.canvas.draw()
