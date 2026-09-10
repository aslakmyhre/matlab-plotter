"""The MAT log plotter window."""
import os
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from . import data, expressions, figure as figure_builder, runs as runs_module, store
from .cursor import Crosshair
from .figure import INK, INK_2, SURFACE
from .models import (HIDDEN, XLABEL_MODES, Channel, Panel, line_style, palette_color,
                     parse_float)
from .widgets import labelled_entry, scrollable

# Outport order of the "Heli 3D" subsystem in init/heli_q8.slx.
HELI_PRESET = [("Time", "s"), ("Travel", "rad"), ("Travel rate", "rad/s"),
               ("Pitch", "rad"), ("Pitch rate", "rad/s"),
               ("Elevation", "rad"), ("Elevation rate", "rad/s")]
MAX_PANELS = 16


def merged_title(signals):
    """Name every merged signal, with the unit once if they all share it."""
    units = {c.unit.get().strip() for c in signals}
    unit = units.pop() if len(units) == 1 else ""
    names = " \u00b7 ".join(c.name.get() for c in signals)
    return f"{names}  [{unit}]" if unit else names


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=6)
        self.grid(row=0, column=0, sticky="nsew")
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.arrays = {}
        self.path = None
        self.channels = []
        self.panels = []
        self.applied_orientation = "rows"
        self.runs = []
        self.run_ticks = []
        self.signal_ticks = []
        # Set while several runs are plotted together: (runs, channels overlaid).
        self.overlay = None
        self.run_matrices = {}
        # The panel layout in use before that, so one run can be shown again.
        self.single_layout = None
        self.current_run = None

        self._make_variables()
        self._build_tabs()
        self._build_figure()
        self.bind_all("<Return>", lambda _e: self.draw())
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

    # ---------- window ----------

    def _build_tabs(self):
        book = ttk.Notebook(self, width=660)
        book.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        book.grid_propagate(False)
        for builder, title in ((self._tab_source, "Source"), (self._tab_runs, "Runs"),
                               (self._tab_signals, "Signals"), (self._tab_panels, "Panels"),
                               (self._tab_figure, "Figure")):
            frame = ttk.Frame(book, padding=6)
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(1, weight=1)
            builder(frame)
            book.add(frame, text=title)
        self.status = ttk.Label(self, text="Open a .mat file to start.", foreground=INK_2,
                                wraplength=600, justify="left")
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    def _build_figure(self):
        holder = ttk.Frame(self)
        holder.grid(row=0, column=1, sticky="nsew")
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
        box = ttk.LabelFrame(frame, text=f"Run folder ({runs_module.VALUES_FILE})", padding=6)
        box.grid(row=0, column=0, sticky="ew")
        box.columnconfigure(0, weight=1)
        ttk.Entry(box, textvariable=self.runs_folder).grid(row=0, column=0, sticky="ew")
        ttk.Button(box, text="Choose\u2026", command=self.choose_runs_folder).grid(
            row=0, column=1, padx=4)
        ttk.Button(box, text="Scan", command=self.scan_runs).grid(row=0, column=2)

        body = ttk.Frame(frame)
        body.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        body.columnconfigure((0, 1), weight=1)
        body.rowconfigure(1, weight=1)
        ttk.Label(body, text="Runs \u2014 \u25b6 shows one, the tick box overlays it").grid(
            row=0, column=0, sticky="w")
        holder, self.run_rows = scrollable(body)
        holder.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        ttk.Label(body, text="Signals to overlay").grid(row=0, column=1, sticky="w")
        holder, self.signal_rows = scrollable(body)
        holder.grid(row=1, column=1, sticky="nsew")

        actions = ttk.Frame(frame)
        actions.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        for text, command in (("Overlay ticked runs", self.plot_overlay),
                              ("Back to one run", self.clear_overlay),
                              ("Tick all runs", self.tick_all_runs),
                              ("Untick all", self.untick_all)):
            ttk.Button(actions, text=text, command=command).pack(side="left", padx=(0, 4))
        ttk.Checkbutton(frame, text="Merge signals into one panel",
                        variable=self.merge_signals, command=self.replot_overlay).grid(
            row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Label(frame, text="Overlay draws one panel per ticked signal, one line per ticked\n"
                             "run. Merged, every line shares one panel: colour is the run,\n"
                             "dash pattern is the signal.",
                  foreground=INK_2, justify="left").grid(row=4, column=0, sticky="w", pady=(6, 0))

    def _tab_signals(self, frame):
        buttons = ttk.Frame(frame)
        buttons.grid(row=0, column=0, sticky="ew")
        ttk.Button(buttons, text="Helicopter names", command=self.apply_heli_preset).pack(
            side="left")
        ttk.Button(buttons, text="Add derived signal", command=self.add_derived).pack(
            side="left", padx=4)
        ttk.Button(buttons, text="One panel each", command=self.one_panel_each).pack(side="left")
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
        self.current_run = None
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
        self.refresh_time_sources()
        first_is_time = len(self.channels) > 1 and data.is_time_like(matrix[0])
        self.time_source.set(self.time_box.cget("values")[1 if first_is_time else 0])
        self.shape_label.configure(
            text=f"{matrix.shape[0]} channels × {matrix.shape[1]} samples")
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
        self.run_ticks = [(run, tk.BooleanVar(value=False)) for run in self.runs]
        self.draw_run_rows()
        untitled = [run.letter for run in self.runs if not run.description]
        self.status.configure(
            text=f"{len(self.runs)} runs in {folder}"
                 + (f"; no {runs_module.VALUES_FILE} line for {', '.join(untitled)}"
                    if untitled else ""),
            foreground=INK_2)

    def draw_run_rows(self):
        """One line per run: a button that shows it, a box that ticks it for overlay."""
        for widget in self.run_rows.winfo_children():
            widget.destroy()
        self.run_rows.columnconfigure(1, weight=1)
        for row, (run, ticked) in enumerate(self.run_ticks):
            ttk.Button(self.run_rows, text="\u25b6", width=2,
                       command=lambda r=run: self.load_run(r)).grid(row=row, column=0, pady=1)
            ttk.Checkbutton(self.run_rows, text=run.listing(), variable=ticked).grid(
                row=row, column=1, sticky="w", padx=4)

    def ticked_runs(self):
        chosen = [run for run, ticked in self.run_ticks if ticked.get()]
        if not chosen:
            raise ValueError("Tick at least one run in the Runs tab.")
        return chosen

    def tick_all_runs(self):
        for _run, ticked in self.run_ticks:
            ticked.set(True)

    def untick_all(self):
        for _item, ticked in self.run_ticks + self.signal_ticks:
            ticked.set(False)

    def load_run(self, run):
        """Show one run on its own, titled by its values.md line."""
        try:
            arrays = data.load_arrays(run.path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Cannot load run", str(exc))
            return
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
        self.run_matrices = {}
        self.file_label.configure(text=os.path.basename(run.path))
        self.variable_box.configure(values=list(arrays))
        self.variable.set(variable)
        self.title.set(run.title())
        if keep:
            self.orientation.set(data.natural_orientation(arrays[variable]))
            self.applied_orientation = self.orientation.get()
            self.shape_label.configure(
                text=f"{matrix.shape[0]} channels \u00d7 {matrix.shape[1]} samples")
            if leaving_overlay:
                self.show_single_layout()
            else:
                self.draw()
        else:
            self.select_variable()

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
        """The overlay signal boxes, keeping whatever was already ticked."""
        kept = {channel.label() for channel, ticked in self.signal_ticks if ticked.get()}
        for widget in self.signal_rows.winfo_children():
            widget.destroy()
        self.signal_ticks = [(c, tk.BooleanVar(value=c.label() in kept))
                             for c in self.channels if not c.derived]
        for row, (channel, ticked) in enumerate(self.signal_ticks):
            ttk.Checkbutton(self.signal_rows, text=channel.label(), variable=ticked).grid(
                row=row, column=0, sticky="w", pady=1)

    def plot_overlay(self):
        """One panel per selected signal, one line per selected run."""
        try:
            chosen = self.ticked_runs()
            signals = [channel for channel, ticked in self.signal_ticks if ticked.get()]
            if not signals:
                raise ValueError("Tick at least one signal to overlay.")
            if not self.merge_signals.get() and len(signals) > MAX_PANELS:
                raise ValueError(f"{len(signals)} signals ticked; the limit is {MAX_PANELS} "
                                 "unless they are merged into one panel.")
            self.run_matrices = {run.path: self._run_matrix(run) for run in chosen}
        except (OSError, ValueError) as exc:
            messagebox.showerror("Cannot overlay runs", str(exc))
            return
        if not self.overlay:
            self.single_layout = ([c.state() for c in self.channels],
                                  [p.state() for p in self.panels])
        self.overlay = (chosen, signals)
        self.title.set("Runs " + ", ".join(run.letter for run in chosen))
        if self.merge_signals.get():
            self._resize_panels(1)
            self.panels[0].title.set(merged_title(signals))
        else:
            self._resize_panels(len(signals))
            for panel, channel in zip(self.panels, signals):
                panel.title.set(channel.label())
        self.draw_panel_rows()
        self.draw()

    def replot_overlay(self):
        """Merging changes the layout, so it only means something once runs are overlaid."""
        if self.overlay:
            self.plot_overlay()

    def _run_matrix(self, run):
        arrays = data.load_arrays(run.path)
        array = arrays[next(iter(arrays))]
        return data.orient(array, data.natural_orientation(array))

    def clear_overlay(self):
        self.overlay = None
        self.run_matrices = {}
        if self.current_run:
            self.title.set(self.current_run.title())
        elif self.path:
            self.title.set(os.path.basename(self.path))
        self.show_single_layout()

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
        self.channels.append(Channel(f"Derived {position}", palette_color(position),
                                     expression="t * 0", panel=HIDDEN))
        self.draw_signal_rows()
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

    def apply_heli_preset(self):
        """Name as many channels as the preset covers; leave any extras alone."""
        if not self.channels:
            return
        matrix = self.matrix()
        names = HELI_PRESET if data.is_time_like(matrix[0]) else HELI_PRESET[1:]
        applied = 0
        for channel, (name, unit) in zip([c for c in self.channels if not c.derived], names):
            channel.name.set(name)
            channel.unit.set(unit)
            applied += 1
        self.refresh_time_sources()
        self.one_panel_each()
        extra = len(self.channels) - applied
        self.status.configure(
            text=f"Named {applied} channels" + (f", {extra} left unnamed" if extra else "")
                 + ("" if names is HELI_PRESET else " (no time channel found)"),
            foreground=INK_2)

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
            self.panels.append(Panel(len(self.panels) + 1))
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

    def draw(self):
        self.figure.clear()
        self.crosshair.attach([])
        if not self.channels:
            self.canvas.draw()
            return
        try:
            self._draw_overlay() if self.overlay else self._draw()
        except ValueError as exc:
            self.figure.clear()
            self.status.configure(text=str(exc), foreground="#e34948")
        self.canvas.draw()

    def _draw(self):
        t, values = self.computed()
        series = {id(p): [] for p in self.panels}
        for channel in self.channels:
            if channel.panel.get() == HIDDEN:
                continue
            panel = self.panels[int(channel.panel.get()) - 1]
            series[id(panel)].append(figure_builder.Series(
                channel.label(), channel.color.get(), "-", t, values[id(channel)]))
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
        index = self.time_index()
        series = {id(p): [] for p in self.panels}
        for position, run in enumerate(chosen):
            matrix = self.run_matrices[run.path]
            needed = max([c.index for c in signals] + ([index] if index is not None else []))
            if needed >= matrix.shape[0]:
                raise ValueError(f"run {run.letter} has only {matrix.shape[0]} channels, "
                                 f"channel {needed} was asked for")
            t = np.arange(matrix.shape[1], dtype=float) if index is None else matrix[index]
            for order, channel in enumerate(signals):
                panel = self.panels[0 if merged else order]
                label = (f"{run.legend_label()} \u00b7 {channel.name.get()}" if merged
                         else run.legend_label())
                series[id(panel)].append(figure_builder.Series(
                    label, palette_color(position), line_style(order) if merged else "-",
                    t, channel.transform(matrix[channel.index])))
        drawn = self._render(series)
        if not drawn:
            return
        self.status.configure(
            text=f"{len(chosen)} runs \u00d7 {len(signals)} signals: "
                 + ", ".join(run.letter for run in chosen),
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
        self.crosshair.attach([(axes[id(p)], [(x.label, x.t, x.values) for x in series[id(p)]])
                               for p in drawn])
        return drawn

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
                                "CSV export writes one run. Load a single run first.")
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
                    panels=[p.state() for p in self.panels])

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
        self.overlay = None
        self.single_layout = None
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
        self.panel_count.set(len(self.panels))

        self.channels = [Channel("", "#000000") for _ in state["channels"]]
        for channel, saved in zip(self.channels, state["channels"]):
            channel.restore(saved)

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
