"""The MAT log plotter window."""
import os
import posixpath
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from . import (data, expressions, figure as figure_builder, names as names_module,
               runs as runs_module, store)
from .cursor import Crosshair
from .figure import INK, INK_2, SURFACE
from .models import (HIDDEN, LINE_STYLES, XLABEL_MODES, Channel, LineLook, Panel, line_style,
                     palette_color, parse_float)
from .widgets import labelled_entry, scrollable, scrolling_tree

MAX_PANELS = 16
# Starting width of the settings pane; the sash moves it from there.
TABS_WIDTH = 660
# Edits redraw on their own once typing pauses this long.
DRAW_DELAY_MS = 400
# Holding an arrow key in the run list loads only the run it stops on.
SELECT_DELAY_MS = 120
ERROR = "#e34948"
FOLDER_PREFIX = "dir:"


def merged_title(signals):
    """Name every merged signal, with the unit once if they all share it."""
    units = {c.unit.get().strip() for c in signals}
    unit = units.pop() if len(units) == 1 else ""
    names = " \u00b7 ".join(c.name.get() for c in signals)
    return f"{names}  [{unit}]" if unit else names


def overlay_title(chosen):
    """How many runs, and the deepest folder holding all of them."""
    # Run folders always use "/", so posixpath splits them on every platform.
    shared = posixpath.commonpath([run.folder for run in chosen])
    return f"{len(chosen)} runs in {shared}" if shared else f"{len(chosen)} runs"


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=6)
        self.grid(row=0, column=0, sticky="nsew")
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.arrays = {}
        self.path = None
        # The signals.json the signal names came from, None when typed or defaulted.
        self.names_path = None
        self.channels = []
        self.panels = []
        self.applied_orientation = "rows"
        self.runs = []
        # Tree item id -> Run, for the runs the filter lets through.
        self.run_items = {}
        # Paths of the runs plotted from the run list, so a repeated selection is a no-op.
        self.shown_runs = ()
        # Set while several runs are plotted together: (runs, channels overlaid).
        self.overlay = None
        # What the overlay panels were laid out for: (channel indices, merged).
        self.overlay_layout = None
        # Matrices of the overlaid runs, by path, so adding one run loads only that run.
        self.run_matrices = {}
        # The panel layout in use before that, so one run can be shown again.
        self.single_layout = None
        self.current_run = None
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

        self._make_variables()
        self.split = ttk.PanedWindow(self, orient="horizontal")
        self.split.grid(row=0, column=0, sticky="nsew")
        self._build_tabs()
        self._build_figure()
        self.split.bind("<Map>", self._place_sash)
        self.bind_all("<Return>", lambda _e: self.draw())
        self._watch((self.title, self.xlabel, self.linewidth, self.xmin, self.xmax,
                     self.columns))
        if self.runs_folder.get():
            self.scan_runs()

    def _make_variables(self):
        self.variable = tk.StringVar()
        self.orientation = tk.StringVar(value="rows")
        self.time_source = tk.StringVar()
        self.title = tk.StringVar()
        self.xlabel = tk.StringVar(value="Time [s]")
        self.columns = tk.IntVar(value=1)
        self.panel_count = tk.IntVar(value=1)
        self.linewidth = tk.StringVar(value="1.4")
        self.auto_x = tk.BooleanVar(value=True)
        self.xmin = tk.StringVar()
        self.xmax = tk.StringVar()
        self.link_x = tk.BooleanVar(value=True)
        self.crosshair_on = tk.BooleanVar(value=True)
        self.merge_signals = tk.BooleanVar(value=False)
        default = os.path.join(os.getcwd(), "runs")
        self.runs_folder = tk.StringVar(value=default if os.path.isdir(default) else "")
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
            if self.signal_tree.exists(str(channel.index)):
                self.signal_tree.item(str(channel.index), text=new)

    def _watch(self, variables):
        """Redraw whenever one of these changes, once the edits pause."""
        for variable in variables:
            variable.trace_add("write", self.schedule_draw)

    # ---------- window ----------

    def _build_tabs(self):
        book = ttk.Notebook(self.split, width=TABS_WIDTH)
        self.split.add(book, weight=0)
        for builder, title in ((self._tab_source, "Source"), (self._tab_runs, "Runs"),
                               (self._tab_signals, "Signals"), (self._tab_panels, "Panels"),
                               (self._tab_lines, "Lines"), (self._tab_figure, "Figure")):
            frame = ttk.Frame(book, padding=6)
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(1, weight=1)
            builder(frame)
            book.add(frame, text=title)
        self.status = ttk.Label(self, text="Open a .mat file to start.", foreground=INK_2,
                                wraplength=600, justify="left")
        self.status.grid(row=1, column=0, sticky="ew", pady=(6, 0))

    def _place_sash(self, _event):
        """Start the sash at the tabs' usual width, once the panes are on screen.

        Before that the paned window has no size to divide. From here the sash
        belongs to the user, so this runs only once.
        """
        self.split.unbind("<Map>")
        self.split.sashpos(0, TABS_WIDTH)

    def _build_figure(self):
        holder = ttk.Frame(self.split, padding=(8, 0, 0, 0))
        self.split.add(holder, weight=1)
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)
        self.figure = Figure(figsize=(9, 7.5), facecolor=SURFACE)
        self.canvas = FigureCanvasTkAgg(self.figure, master=holder)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        NavigationToolbar2Tk(self.canvas, holder, pack_toolbar=False).grid(
            row=1, column=0, sticky="ew")
        self.crosshair = Crosshair(self.canvas)

    def _tab_source(self, frame):
        box = ttk.LabelFrame(frame, text="File", padding=6)
        box.grid(row=0, column=0, sticky="ew")
        box.columnconfigure(1, weight=1)
        ttk.Button(box, text="Open .mat…", command=self.open_file).grid(row=0, column=0, sticky="w")
        self.file_label = ttk.Label(box, text="no file loaded", foreground=INK_2)
        self.file_label.grid(row=0, column=1, columnspan=3, sticky="w", padx=6)

        ttk.Label(box, text="Variable").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.variable_box = ttk.Combobox(box, textvariable=self.variable, state="readonly")
        self.variable_box.grid(row=1, column=1, columnspan=3, sticky="ew", pady=(6, 0))
        self.variable_box.bind("<<ComboboxSelected>>", lambda _e: self.select_variable())

        ttk.Label(box, text="Signals in").grid(row=2, column=0, sticky="w", pady=(6, 0))
        orient = ttk.Frame(box)
        orient.grid(row=2, column=1, columnspan=3, sticky="w", pady=(6, 0))
        for text in ("rows", "columns"):
            ttk.Radiobutton(orient, text=text, value=text, variable=self.orientation,
                            command=self.rebuild_channels).pack(side="left")

        ttk.Label(box, text="Time from").grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.time_box = ttk.Combobox(box, textvariable=self.time_source, state="readonly")
        self.time_box.grid(row=3, column=1, columnspan=3, sticky="ew", pady=(6, 0))
        self.time_box.bind("<<ComboboxSelected>>", lambda _e: self.draw())

        self.shape_label = ttk.Label(box, text="", foreground=INK_2)
        self.shape_label.grid(row=4, column=0, columnspan=4, sticky="w", pady=(6, 0))

        help_text = ("Expressions in the Signals tab may use t, the other signal names,\n"
                     "and sin cos exp log sqrt abs deg rad deriv(x) smooth(x, n).\n"
                     "Example:  deg(pitch) - deg(pitch_c)")
        ttk.Label(frame, text=help_text, foreground=INK_2, justify="left").grid(
            row=1, column=0, sticky="nw", pady=(8, 0))

    def _tab_runs(self, frame):
        box = ttk.LabelFrame(frame, text="Run folder (subfolders included)", padding=6)
        box.grid(row=0, column=0, sticky="ew")
        box.columnconfigure(0, weight=1)
        folder = ttk.Entry(box, textvariable=self.runs_folder)
        folder.grid(row=0, column=0, sticky="ew")
        folder.bind("<Return>", lambda _e: self.scan_runs())
        ttk.Button(box, text="Choose\u2026", command=self.choose_runs_folder).grid(
            row=0, column=1, padx=4)
        ttk.Button(box, text="Rescan", command=self.scan_runs).grid(row=0, column=2)

        body = ttk.Frame(frame)
        body.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(2, weight=1)

        ttk.Label(body, text="Runs").grid(row=0, column=0, sticky="w")
        search = ttk.Frame(body)
        search.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(2, 4))
        search.columnconfigure(1, weight=1)
        ttk.Label(search, text="Filter").grid(row=0, column=0, padx=(0, 4))
        ttk.Entry(search, textvariable=self.run_filter).grid(row=0, column=1, sticky="ew")
        self.run_count = ttk.Label(search, text="", foreground=INK_2)
        self.run_count.grid(row=0, column=2, padx=(4, 0))
        holder, self.run_tree = scrolling_tree(body)
        holder.grid(row=2, column=0, sticky="nsew", padx=(0, 6))
        self.run_tree.bind("<<TreeviewSelect>>", lambda _e: self.schedule_run_selection())
        self.run_tree.bind("<Up>", lambda _e: self.step_run(forward=False))
        self.run_tree.bind("<Down>", lambda _e: self.step_run(forward=True))
        self.run_tree.bind("<Shift-Button-1>", self._toggle_item)
        self._list_buttons(body, 0, (("All", self.select_all_runs), ("None", self.select_no_runs),
                                     ("Invert", self.invert_runs)))

        ttk.Label(body, text="Signals to overlay").grid(row=0, column=1, sticky="w")
        holder, self.signal_tree = scrolling_tree(body)
        holder.grid(row=2, column=1, sticky="nsew")
        self.signal_tree.bind("<<TreeviewSelect>>", lambda _e: self.on_signal_select())
        self.signal_tree.bind("<Shift-Button-1>", self._toggle_item)
        self._list_buttons(body, 1, (
            ("All", lambda: self.signal_tree.selection_set(self.signal_tree.get_children())),
            ("None", lambda: self.signal_tree.selection_set(()))))

        ttk.Checkbutton(frame, text="Merge signals into one panel",
                        variable=self.merge_signals, command=self.replot_overlay).grid(
            row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Label(frame, text="Click a run to plot it. Shift- or ctrl/\u2318-click adds or drops "
                             "one run,\na folder selects every run in it. Several runs are "
                             "overlaid: one panel\nper selected signal, one line per run. "
                             "Up/Down steps through the runs.\nMerged, the selected signals "
                             "share one panel, for a single run too:\ncolour is the run, dash "
                             "is the signal (one run: the signal's own colour).",
                  foreground=INK_2, justify="left").grid(row=3, column=0, sticky="w", pady=(6, 0))

    @staticmethod
    def _list_buttons(parent, column, buttons):
        row = ttk.Frame(parent)
        row.grid(row=3, column=column, sticky="w", pady=(4, 0))
        for text, command in buttons:
            ttk.Button(row, text=text, command=command, width=6).pack(side="left", padx=(0, 4))

    def _tab_signals(self, frame):
        buttons = ttk.Frame(frame)
        buttons.grid(row=0, column=0, sticky="ew")
        ttk.Button(buttons, text="Add derived signal", command=self.add_derived).pack(
            side="left")
        ttk.Button(buttons, text="One panel each", command=self.one_panel_each).pack(
            side="left", padx=4)
        ttk.Button(buttons, text="Save names\u2026", command=self.save_names).pack(side="left")
        ttk.Button(buttons, text="Load names\u2026", command=self.load_names).pack(
            side="left", padx=4)
        self.names_label = ttk.Label(frame, text="", foreground=INK_2, wraplength=600,
                                     justify="left")
        self.names_label.grid(row=2, column=0, sticky="w", pady=(6, 0))
        holder, self.signal_frame = scrollable(frame, horizontal=True)
        holder.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

    def _tab_panels(self, frame):
        head = ttk.Frame(frame)
        head.grid(row=0, column=0, sticky="ew")
        ttk.Label(head, text="Panels").pack(side="left")
        ttk.Spinbox(head, from_=1, to=MAX_PANELS, width=4, textvariable=self.panel_count,
                    command=self.set_panel_count).pack(side="left", padx=6)
        ttk.Label(head, text="Columns").pack(side="left")
        ttk.Spinbox(head, from_=1, to=4, width=4, textvariable=self.columns,
                    command=self.draw).pack(side="left", padx=6)
        holder, self.panel_frame = scrollable(frame)
        holder.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

    def _tab_lines(self, frame):
        head = ttk.Frame(frame)
        head.grid(row=0, column=0, sticky="ew")
        ttk.Button(head, text="Reset all", command=self.reset_lines).pack(side="left")
        ttk.Label(head, text="Every plotted line. Empty text leaves a line out of the legend.",
                  foreground=INK_2).pack(side="left", padx=8)
        holder, self.line_frame = scrollable(frame)
        holder.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

    def _tab_figure(self, frame):
        box = ttk.LabelFrame(frame, text="Figure", padding=6)
        box.grid(row=0, column=0, sticky="ew")
        box.columnconfigure(1, weight=1)
        labelled_entry(box, 0, "Title", self.title)
        labelled_entry(box, 1, "X label", self.xlabel)

        ttk.Checkbutton(box, text="X range auto", variable=self.auto_x,
                        command=self.draw).grid(row=2, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(box, textvariable=self.xmin, width=9).grid(row=2, column=1, sticky="w",
                                                             pady=(4, 0))
        ttk.Label(box, text="to").grid(row=2, column=2, pady=(4, 0))
        ttk.Entry(box, textvariable=self.xmax, width=9).grid(row=2, column=3, sticky="w",
                                                             pady=(4, 0))

        ttk.Label(box, text="Line width").grid(row=3, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(box, textvariable=self.linewidth, width=6).grid(row=3, column=1, sticky="w",
                                                                  pady=(4, 0))
        ttk.Checkbutton(box, text="Linked x axes", variable=self.link_x,
                        command=self.draw).grid(row=4, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(box, text="Cursor readout", variable=self.crosshair_on,
                        command=self.toggle_crosshair).grid(row=4, column=2, columnspan=2,
                                                            sticky="w")

        actions = ttk.LabelFrame(frame, text="Output", padding=6)
        actions.grid(row=1, column=0, sticky="new", pady=(8, 0))
        actions.columnconfigure((0, 1), weight=1)
        for position, (text, command) in enumerate([
                ("Redraw", self.draw), ("Save figure…", self.save_figure),
                ("Export CSV…", self.export_csv), ("Save settings…", self.save_settings),
                ("Load settings…", self.load_settings)]):
            ttk.Button(actions, text=text, command=command).grid(
                row=position // 2, column=position % 2, sticky="ew", padx=2, pady=2)

    # ---------- loading ----------

    def open_file(self, path=None):
        path = path or filedialog.askopenfilename(
            title="Open MATLAB file", filetypes=[("MATLAB files", "*.mat"), ("All files", "*")])
        if not path:
            return
        try:
            self.arrays = data.load_arrays(path)
        except Exception as exc:
            messagebox.showerror("Cannot read file", f"{path}\n\n{exc}")
            return
        self.path = path
        self.forget_runs()
        self.file_label.configure(text=os.path.basename(path))
        self.variable_box.configure(values=list(self.arrays))
        self.variable.set(next(iter(self.arrays)))
        self.title.set(os.path.basename(path))
        self.select_variable()

    def select_variable(self):
        """Point at a variable and orient it so the short dimension holds the channels."""
        self.orientation.set(data.natural_orientation(self.arrays[self.variable.get()]))
        self.rebuild_channels()

    def matrix(self):
        return data.orient(self.arrays[self.variable.get()], self.orientation.get())

    def rebuild_channels(self):
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

        self.channels = [Channel(f"Signal {i}", palette_color(i), index=i)
                         for i in range(matrix.shape[0])]
        # Looks belong to the channels just replaced.
        self.line_looks = {}
        for channel in self.channels:
            self._adopt(channel)
        self.refresh_time_sources()
        first_is_time = len(self.channels) > 1 and data.is_time_like(matrix[0])
        self.time_source.set(self.time_box.cget("values")[1 if first_is_time else 0])
        self.shape_label.configure(
            text=f"{matrix.shape[0]} channels × {matrix.shape[1]} samples")
        # The channels were just made with default names, so whatever file named the
        # old ones no longer applies.
        self.names_path = None
        self.apply_names_for(self.path)
        self.one_panel_each()

    def refresh_time_sources(self):
        # Track the choice by channel index: the labels change whenever signals are renamed.
        keep = self.time_index()
        sources = ["Sample index"] + [f"{i}: {c.name.get()}"
                                      for i, c in enumerate(self.channels) if not c.derived]
        self.time_box.configure(values=sources)
        self.time_source.set(sources[keep + 1] if keep is not None and keep + 1 < len(sources)
                             else sources[0])

    # ---------- runs folder ----------

    def choose_runs_folder(self):
        folder = filedialog.askdirectory(title="Folder of run logs",
                                         initialdir=self.runs_folder.get() or os.getcwd())
        if folder:
            self.runs_folder.set(folder)
            self.scan_runs()

    def scan_runs(self):
        folder = self.runs_folder.get()
        try:
            self.runs = runs_module.discover(folder)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Cannot read run folder", str(exc))
            return
        # The files may have changed on disk, so the selection is loaded afresh.
        self.shown_runs = ()
        self.run_matrices = {}
        self.fill_run_tree()
        folders = len({run.folder for run in self.runs})
        self.status.configure(text=f"{len(self.runs)} runs in {folders} folders under {folder}",
                              foreground=INK_2)

    def fill_run_tree(self):
        """The runs the filter lets through, under their folders, keeping the selection."""
        tree = self.run_tree
        kept = tree.selection()
        tree.delete(*tree.get_children())
        text = self.run_filter.get().strip()
        self.run_items = {}
        for run in self.runs:
            if text and not run.matches(text):
                continue
            tree.insert(self._folder_item(run.folder), "end", iid=run.path, text=run.name)
            self.run_items[run.path] = run
        tree.selection_set([item for item in kept if tree.exists(item)])
        self.run_count.configure(text=f"{len(self.run_items)} of {len(self.runs)}")

    def _folder_item(self, folder):
        """The tree item for a folder, made along with its parents when missing."""
        if not folder:
            return ""
        item = FOLDER_PREFIX + folder
        if not self.run_tree.exists(item):
            parent, _slash, name = folder.rpartition("/")
            self.run_tree.insert(self._folder_item(parent), "end", iid=item, text=f"{name}/",
                                 open=True)
        return item

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
        chosen = self.selected_runs()
        paths = tuple(run.path for run in chosen)
        if not chosen or paths == self.shown_runs:
            return
        if len(chosen) > 1:
            shown = self.plot_overlay(chosen)
        elif self.merge_signals.get():
            # Loading first gives the run its names and the layout to return to unmerged.
            shown = self.load_run(chosen[0]) and self.plot_overlay(chosen)
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
        self.run_tree.selection_set(())

    def load_run(self, run):
        """Show one run on its own. Returns whether it could be read."""
        try:
            arrays = data.load_arrays(run.path)
        except (OSError, ValueError) as exc:
            self.status.configure(text=f"Cannot load {run.label}: {exc}", foreground=ERROR)
            return False
        variable = next(iter(arrays))
        matrix = data.orient(arrays[variable], data.natural_orientation(arrays[variable]))
        # Stepping through runs keeps the names, panels and expressions already set up,
        # as long as the new log has the same channels.
        keep = bool(self.channels) and matrix.shape[0] == sum(
            1 for c in self.channels if not c.derived)

        leaving_overlay = self.overlay is not None
        self.arrays = arrays
        self.path = run.path
        self.current_run = run
        self.overlay = None
        self.overlay_layout = None
        self.run_matrices = {}
        self.file_label.configure(text=os.path.basename(run.path))
        self.variable_box.configure(values=list(arrays))
        self.variable.set(variable)
        self.title.set(run.label)
        if keep:
            self.orientation.set(data.natural_orientation(arrays[variable]))
            self.applied_orientation = self.orientation.get()
            self.shape_label.configure(
                text=f"{matrix.shape[0]} channels \u00d7 {matrix.shape[1]} samples")
            if leaving_overlay:
                self.show_single_layout()
            # Another folder may hold another signals.json, logged with another layout.
            self.apply_names_for(run.path)
            self.draw()
        else:
            self.select_variable()
        return True

    def show_single_layout(self):
        """Put back the panels that were in use before the runs were overlaid."""
        if not self.single_layout or len(self.single_layout[0]) != len(self.channels):
            self.one_panel_each()
            return
        channels, panels = self.single_layout
        self._resize_panels(len(panels))
        for panel, saved in zip(self.panels, panels):
            panel.restore(saved)
        for channel, saved in zip(self.channels, channels):
            channel.restore(saved)
        self.draw_panel_rows()
        self.draw_signal_rows()
        self.draw()

    def refresh_signal_list(self):
        """The overlay signal list, keeping whatever was already selected."""
        tree = self.signal_tree
        kept = tree.selection()
        tree.delete(*tree.get_children())
        for channel in self.channels:
            if not channel.derived:
                tree.insert("", "end", iid=str(channel.index), text=channel.label())
        tree.selection_set([item for item in kept if tree.exists(item)])

    def overlay_signals(self):
        """The selected overlay signals. With none selected, the ones plotted right now."""
        by_item = {str(c.index): c for c in self.channels if not c.derived}
        chosen = [by_item[item] for item in self.signal_tree.get_children()
                  if item in self.signal_tree.selection()]
        if chosen or self.overlay:
            return chosen
        time_index = self.time_index()
        chosen = [c for c in by_item.values()
                  if c.panel.get() != HIDDEN and c.index != time_index]
        self.signal_tree.selection_set([str(c.index) for c in chosen])
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

    def on_signal_select(self):
        if not self.overlay:
            return
        indices = tuple(int(item) for item in self.signal_tree.selection())
        if sorted(indices) != sorted(self.overlay_layout[0]):
            self.plot_overlay(self.overlay[0])

    def plot_overlay(self, chosen):
        """One panel per selected signal, one line per run. Returns whether it plotted."""
        # The signal names and panels come from a loaded log, so the first run sets them up.
        if not self.channels and not self.load_run(chosen[0]):
            return False
        signals = self.overlay_signals()
        merged = self.merge_signals.get()
        try:
            if not signals:
                raise ValueError("Select at least one signal to overlay.")
            if not merged and len(signals) > MAX_PANELS:
                raise ValueError(f"{len(signals)} signals selected; the limit is {MAX_PANELS} "
                                 "unless they are merged into one panel.")
            matrices = {run.path: (self.run_matrices[run.path] if run.path in self.run_matrices
                                   else self._run_matrix(run))
                        for run in chosen}
        except (OSError, ValueError) as exc:
            self.status.configure(text=f"Cannot overlay runs: {exc}", foreground=ERROR)
            return False
        if not self.overlay:
            self.single_layout = ([c.state() for c in self.channels],
                                  [p.state() for p in self.panels])
        self.run_matrices = matrices
        self.overlay = (chosen, signals)
        self.title.set(chosen[0].label if len(chosen) == 1 else overlay_title(chosen))
        layout = (tuple(c.index for c in signals), merged)
        # Only a new set of signals relays the panels, so titles and limits typed for
        # the overlay survive adding or dropping runs.
        if layout != self.overlay_layout:
            self.overlay_layout = layout
            if merged:
                self._resize_panels(1)
                self.panels[0].title.set(merged_title(signals))
            else:
                self._resize_panels(len(signals))
                for panel, channel in zip(self.panels, signals):
                    panel.title.set(channel.label())
            self.draw_panel_rows()
        self.draw()
        return True

    def replot_overlay(self):
        """Merging changes the layout, and for a single run whether it is overlaid at all."""
        self.shown_runs = ()
        self.apply_run_selection()

    def _run_matrix(self, run):
        try:
            arrays = data.load_arrays(run.path)
        except ValueError as exc:
            raise ValueError(f"{run.label}: {exc}")
        array = arrays[next(iter(arrays))]
        return data.orient(array, data.natural_orientation(array))

    # ---------- signals tab ----------

    def draw_signal_rows(self):
        self.refresh_signal_list()
        for widget in self.signal_frame.winfo_children():
            widget.destroy()
        headers = ["name", "unit", "expression", "scale", "offset", "colour", "panel", ""]
        for column, text in enumerate(headers):
            ttk.Label(self.signal_frame, text=text, foreground=INK_2).grid(
                row=0, column=column, padx=2, sticky="w")
        choices = [HIDDEN] + [str(p.number) for p in self.panels]
        for row, channel in enumerate(self.channels, start=1):
            ttk.Entry(self.signal_frame, textvariable=channel.name, width=12).grid(
                row=row, column=0, padx=1)
            ttk.Entry(self.signal_frame, textvariable=channel.unit, width=6).grid(
                row=row, column=1, padx=1)
            expression = ttk.Entry(self.signal_frame, textvariable=channel.expression, width=16)
            expression.grid(row=row, column=2, padx=1)
            if not channel.derived:
                channel.expression.set(f"channel {channel.index}")
                expression.configure(state="disabled")
            ttk.Entry(self.signal_frame, textvariable=channel.scale, width=5).grid(
                row=row, column=3, padx=1)
            ttk.Entry(self.signal_frame, textvariable=channel.offset, width=5).grid(
                row=row, column=4, padx=1)
            swatch = tk.Button(self.signal_frame, background=channel.color.get(), width=2,
                               relief="flat")
            swatch.configure(command=lambda c=channel, b=swatch: self.pick_color(c, b))
            swatch.grid(row=row, column=5, padx=3)
            ttk.Combobox(self.signal_frame, textvariable=channel.panel, values=choices,
                         width=6, state="readonly").grid(row=row, column=6, padx=1)
            if channel.derived:
                ttk.Button(self.signal_frame, text="×", width=2,
                           command=lambda c=channel: self.remove_channel(c)).grid(
                    row=row, column=7, padx=1)

    def pick_color(self, channel, button):
        chosen = colorchooser.askcolor(color=channel.color.get(), title=channel.name.get())[1]
        if chosen:
            channel.color.set(chosen)
            button.configure(background=chosen)
            self.draw()

    def add_derived(self):
        if not self.channels:
            messagebox.showinfo("No file", "Open a .mat file first.")
            return
        position = len(self.channels)
        channel = Channel(f"Derived {position}", palette_color(position),
                          expression="t * 0", panel=HIDDEN)
        self._adopt(channel)
        self.channels.append(channel)
        self.draw_signal_rows()
        self.draw()
        self.status.configure(text="Type an expression for the new signal, then press Return.",
                              foreground=INK_2)

    def remove_channel(self, channel):
        self.channels.remove(channel)
        self.draw_signal_rows()
        self.draw()

    def one_panel_each(self):
        """Give every plottable signal its own panel — the default view."""
        time_index = self.time_index()
        plotted = [c for c in self.channels if c.index != time_index]
        self.panel_count.set(max(1, min(len(plotted), MAX_PANELS)))
        self.set_panel_count()
        for channel in self.channels:
            channel.panel.set(HIDDEN)
        for position, channel in enumerate(plotted[:MAX_PANELS]):
            channel.panel.set(str(position + 1))
            self.panels[position].title.set(channel.label())
        self.draw_signal_rows()
        self.draw()

    def raw_channels(self):
        return [c for c in self.channels if not c.derived]

    def apply_names_for(self, path):
        """Name the logged signals from the signals.json nearest above `path`."""
        found = names_module.find(os.path.dirname(path))
        if found is None:
            # Names read from a file that does not cover this log describe another layout.
            if self.names_path:
                self._set_names([(f"Signal {c.index}", "") for c in self.raw_channels()])
                self.names_path = None
            self.names_label.configure(
                text=f"No {names_module.NAMES_FILE} at or above this log. Name the signals "
                     "below and use Save names\u2026 to keep them.", foreground=INK_2)
            return
        if found == self.names_path:
            return
        try:
            pairs = names_module.load(found)
            self._check_name_count(found, pairs)
        except (OSError, ValueError) as exc:
            self.names_label.configure(text=f"Not applied: {exc}", foreground=ERROR)
            return
        self._set_names(pairs)
        self.names_path = found
        self.names_label.configure(text=f"Names from {found}", foreground=INK_2)

    def _check_name_count(self, path, pairs):
        count = len(self.raw_channels())
        if len(pairs) != count:
            raise ValueError(f"{path} names {len(pairs)} signals, this log has {count}")

    def _set_names(self, pairs):
        for channel, (name, unit) in zip(self.raw_channels(), pairs):
            channel.name.set(name)
            channel.unit.set(unit)

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
        for channel in self.channels:
            if channel.panel.get() != HIDDEN and int(channel.panel.get()) > count:
                channel.panel.set(HIDDEN)

    def draw_panel_rows(self):
        for widget in self.panel_frame.winfo_children():
            widget.destroy()
        for row, panel in enumerate(self.panels):
            box = ttk.LabelFrame(self.panel_frame, text=f"Panel {panel.number}", padding=4)
            box.grid(row=row, column=0, sticky="ew", pady=2)
            box.columnconfigure(1, weight=1)
            labelled_entry(box, 0, "Title", panel.title)
            labelled_entry(box, 1, "Y label", panel.ylabel)
            ttk.Checkbutton(box, text="Y auto", variable=panel.auto_y,
                            command=self.draw).grid(row=2, column=0, sticky="w")
            ttk.Entry(box, textvariable=panel.ymin, width=8).grid(row=2, column=1, sticky="w")
            ttk.Label(box, text="to").grid(row=2, column=2)
            ttk.Entry(box, textvariable=panel.ymax, width=8).grid(row=2, column=3, sticky="w")
            ttk.Checkbutton(box, text="Legend", variable=panel.legend,
                            command=self.draw).grid(row=3, column=0, sticky="w")
            ttk.Checkbutton(box, text="Grid", variable=panel.grid,
                            command=self.draw).grid(row=3, column=1, sticky="w")
            ttk.Checkbutton(box, text="Full width", variable=panel.span,
                            command=self.draw).grid(row=3, column=2, columnspan=2, sticky="w")
            ttk.Label(box, text="Time axis").grid(row=4, column=0, sticky="w")
            ttk.Combobox(box, textvariable=panel.xlabels, values=XLABEL_MODES, width=8,
                         state="readonly").grid(row=4, column=1, sticky="w")

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
        for channel in self.channels:
            if not channel.derived:
                namespace[expressions.identifier(channel.name.get())] = matrix[channel.index]
        values = {}
        for channel in self.channels:
            raw = (matrix[channel.index] if not channel.derived
                   else expressions.evaluate(channel.expression.get(), namespace,
                                             channel.name.get()))
            if channel.derived:
                namespace[expressions.identifier(channel.name.get())] = raw
            values[id(channel)] = channel.transform(raw)
        return t, values

    def schedule_draw(self, *_trace):
        if self._pending_draw:
            self.after_cancel(self._pending_draw)
        self._pending_draw = self.after(DRAW_DELAY_MS, self.draw)

    def draw(self):
        if self._pending_draw:
            self.after_cancel(self._pending_draw)
            self._pending_draw = None
        self.figure.clear()
        self.crosshair.attach([])
        self.drawn_lines = []
        if not self.channels:
            self.canvas.draw()
            return
        try:
            self._draw_overlay() if self.overlay else self._draw()
        except ValueError as exc:
            self.figure.clear()
            self.status.configure(text=str(exc), foreground=ERROR)
        self.canvas.draw()

    def _draw(self):
        t, values = self.computed()
        series = {id(p): [] for p in self.panels}
        for channel in self.channels:
            if channel.panel.get() == HIDDEN:
                continue
            panel = self.panels[int(channel.panel.get()) - 1]
            series[id(panel)].append(self._line(
                panel, ("", channel.uid), channel.label(), channel.color.get(), "-",
                t, values[id(channel)]))
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
        merged = self.merge_signals.get()
        # One run has no other runs to tell apart, so its lines keep their signal colours.
        single = len(chosen) == 1
        index = self.time_index()
        series = {id(p): [] for p in self.panels}
        for position, run in enumerate(chosen):
            matrix = self.run_matrices[run.path]
            needed = max([c.index for c in signals] + ([index] if index is not None else []))
            if needed >= matrix.shape[0]:
                raise ValueError(f"run {run.name} has only {matrix.shape[0]} channels, "
                                 f"channel {needed} was asked for")
            t = np.arange(matrix.shape[1], dtype=float) if index is None else matrix[index]
            for order, channel in enumerate(signals):
                panel = self.panels[0 if merged else order]
                if single:
                    label, color, style = channel.name.get(), channel.color.get(), "-"
                else:
                    label = f"{run.label} \u00b7 {channel.name.get()}" if merged else run.label
                    color = palette_color(position)
                    style = line_style(order) if merged else "-"
                key = ("" if single else run.path, channel.uid)
                series[id(panel)].append(self._line(
                    panel, key, label, color, style, t, channel.transform(matrix[channel.index])))
        drawn = self._render(series)
        if not drawn:
            return
        self.status.configure(
            text=(f"{len(signals)} signals merged" if single
                  else f"{len(chosen)} runs \u00d7 {len(signals)} signals"),
            foreground=INK_2)

    def _render(self, series):
        """Lay the non-empty panels out and draw them. Returns the panels drawn."""
        drawn = [p for p in self.panels if series[id(p)]]
        if not drawn:
            self.status.configure(text="No signal is assigned to a panel.", foreground=INK_2)
            return []
        settings = {
            "title": self.title.get(), "xlabel": self.xlabel.get(),
            "linewidth": parse_float(self.linewidth.get(), "Line width"),
            "link_x": self.link_x.get(), "auto_x": self.auto_x.get(),
            "xmin": parse_float(self.xmin.get(), "X min") if not self.auto_x.get() else None,
            "xmax": parse_float(self.xmax.get(), "X max") if not self.auto_x.get() else None,
        }
        columns = max(1, int(self.columns.get()))
        placements, rows = figure_builder.place(drawn, columns)
        axes = figure_builder.draw(self.figure, placements, rows, columns, series, settings)
        self.crosshair.attach([(axes[id(p)], series[id(p)]) for p in drawn],
                              settings["linewidth"])
        self.refresh_line_rows()
        return drawn

    def _line(self, panel, key, auto_label, color, auto_style, t, values):
        """One Series, with whatever legend text and style the user gave this line."""
        look = self.line_looks.get(key)
        if look is None:
            look = self.line_looks[key] = LineLook(auto_label)
            self._watch((look.label, look.style))
        legend, style = look.resolve(auto_label, auto_style)
        self.drawn_lines.append((panel, look, color))
        return figure_builder.Series(auto_label, legend, color, style, t, values)

    def refresh_line_rows(self):
        """One row per plotted line in the Lines tab, under its panel."""
        layout = [(id(panel), id(look)) for panel, look, _color in self.drawn_lines]
        if layout == self.line_rows_shown:
            for _panel, look, color in self.drawn_lines:
                self.line_swatches[id(look)].configure(background=color)
            return
        self.line_rows_shown = layout
        for widget in self.line_frame.winfo_children():
            widget.destroy()
        self.line_swatches = {}
        self.line_frame.columnconfigure(1, weight=1)
        row = 0
        for panel in self.panels:
            lines = [(look, color) for drawn, look, color in self.drawn_lines if drawn is panel]
            if not lines:
                continue
            head = ttk.Frame(self.line_frame)
            head.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(8 if row else 0, 2))
            ttk.Label(head, text=f"Panel {panel.number}", foreground=INK_2).pack(side="left")
            ttk.Label(head, textvariable=panel.title).pack(side="left", padx=6)
            ttk.Checkbutton(head, text="Legend", variable=panel.legend,
                            command=self.draw).pack(side="right")
            row += 1
            for look, color in lines:
                swatch = tk.Label(self.line_frame, background=color, width=2)
                swatch.grid(row=row, column=0, padx=(0, 4), pady=1)
                self.line_swatches[id(look)] = swatch
                ttk.Entry(self.line_frame, textvariable=look.label).grid(
                    row=row, column=1, sticky="ew", pady=1)
                style = ttk.Combobox(self.line_frame, textvariable=look.style,
                                     values=list(LINE_STYLES), width=8, state="readonly")
                style.grid(row=row, column=2, padx=(4, 0), pady=1)
                style.bind("<<ComboboxSelected>>", lambda _e: self.draw())
                row += 1

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

    def save_figure(self):
        if not self.figure.axes:
            messagebox.showinfo("Nothing to save", "Plot something first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg"),
                       ("EPS", "*.eps")])
        if not path:
            return
        undo = (figure_builder.flatten_alpha(self.figure, SURFACE)
                if path.lower().endswith(".eps") else None)
        try:
            self.figure.savefig(path, dpi=160, bbox_inches="tight", facecolor=SURFACE)
        finally:
            if undo:
                undo()
                self.canvas.draw_idle()
        self.status.configure(text=f"saved {path}", foreground=INK_2)

    def export_csv(self):
        if self.overlay:
            messagebox.showinfo("Overlay plotted",
                                "CSV export writes one unmerged run. Select a single run and untick "
                                "Merge first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            t, values = self.computed()
            columns = [(c.name.get(), values[id(c)]) for c in self.channels
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
                    lines=self._line_states())

    def _line_states(self):
        """The single-run lines given their own legend or style, by signal position."""
        position = {c.uid: i for i, c in enumerate(self.channels)}
        return [dict(signal=position[uid], label=look.label.get(), style=look.style.get())
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
            self.arrays = data.load_arrays(state["path"])
            self.path = state["path"]
            self.file_label.configure(text=os.path.basename(self.path))
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
        self.line_looks = {}
        # Settings saved before legends could be edited have no "lines".
        for saved in state.get("lines", []):
            look = LineLook(label=saved["label"], style=saved["style"])
            self._watch((look.label, look.style))
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
        matrix = self.matrix()
        self.shape_label.configure(
            text=f"{matrix.shape[0]} channels × {matrix.shape[1]} samples")
        self.draw_panel_rows()
        self.draw_signal_rows()
        self.draw()
