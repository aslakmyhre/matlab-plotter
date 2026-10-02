"""The editable objects behind the Signals, Panels and Lines tabs."""
import itertools
import tkinter as tk

# Fixed categorical order, validated for colourblind separation.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
           "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
# Merged panels colour by run, so the dash pattern is what separates the signals.
LINESTYLES = ["-", "--", ":", "-."]

# What the Lines tab offers, as matplotlib line styles. "auto" leaves the choice to the view.
LINE_STYLES = {"auto": None, "solid": "-", "dashed": "--", "dotted": ":", "dash-dot": "-."}

HIDDEN = "hidden"
_channel_ids = itertools.count()
XLABEL_MODES = ["auto", "always", "never"]


def parse_float(text, field):
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"{field}: {text!r} is not a number")


def palette_color(position):
    return PALETTE[position % len(PALETTE)]


def line_style(position):
    return LINESTYLES[position % len(LINESTYLES)]


class Channel:
    """One signal: a matrix row, or an expression over the other signals."""

    def __init__(self, name, color, index=None, expression="", unit="", panel="1"):
        self.index = index
        # Stable across renames and reorders, so a line's legend and style stay with it.
        self.uid = next(_channel_ids)
        self.name = tk.StringVar(value=name)
        self.unit = tk.StringVar(value=unit)
        self.expression = tk.StringVar(value=expression)
        self.scale = tk.StringVar(value="1")
        self.offset = tk.StringVar(value="0")
        self.color = tk.StringVar(value=color)
        self.panel = tk.StringVar(value=panel)
        # The label panels were last told about, so a rename can find the titles to update.
        self.shown_label = self.label()

    @property
    def derived(self):
        return self.index is None

    def label(self):
        unit = self.unit.get().strip()
        return f"{self.name.get()}  [{unit}]" if unit else self.name.get()

    def transform(self, raw):
        scale = parse_float(self.scale.get(), f"{self.name.get()} scale")
        offset = parse_float(self.offset.get(), f"{self.name.get()} offset")
        return raw * scale + offset

    def variables(self):
        return (self.name, self.unit, self.expression, self.scale, self.offset,
                self.color, self.panel)

    def state(self):
        return dict(index=self.index, name=self.name.get(), unit=self.unit.get(),
                    expression=self.expression.get(), scale=self.scale.get(),
                    offset=self.offset.get(), color=self.color.get(), panel=self.panel.get())

    def restore(self, state):
        self.index = state["index"]
        for key in ("name", "unit", "expression", "scale", "offset", "color", "panel"):
            getattr(self, key).set(state[key])
        self.shown_label = self.label()


class LineLook:
    """The legend text, style and colour the user gave one plotted line.

    The text starts as the automatic label and keeps following it until edited, so
    renaming a signal still reaches legends nobody has touched.
    """

    def __init__(self, auto_label=None, label="", style="auto", color=""):
        self.auto_label = auto_label
        self.label = tk.StringVar(value=auto_label if auto_label is not None else label)
        self.style = tk.StringVar(value=style)
        # Empty leaves the colour to the view.
        self.color = tk.StringVar(value=color)

    def variables(self):
        return (self.label, self.style, self.color)

    def edited(self):
        return (self.label.get() != self.auto_label or self.style.get() != "auto"
                or bool(self.color.get()))

    def resolve(self, auto_label, auto_style, auto_color):
        """(legend text, matplotlib style, colour) for this draw."""
        # Writing only on a real change keeps the variable trace from redrawing forever.
        if auto_label != self.auto_label and self.label.get() == self.auto_label:
            self.label.set(auto_label)
        self.auto_label = auto_label
        return (self.label.get(), LINE_STYLES[self.style.get()] or auto_style,
                self.color.get() or auto_color)

    def reset(self):
        self.label.set(self.auto_label or "")
        self.style.set("auto")
        self.color.set("")


class Panel:
    """One subplot and everything the user can set on it."""

    def __init__(self, number):
        self.number = number
        self.title = tk.StringVar(value="")
        self.ylabel = tk.StringVar(value="")
        self.auto_y = tk.BooleanVar(value=True)
        self.ymin = tk.StringVar(value="")
        self.ymax = tk.StringVar(value="")
        self.legend = tk.BooleanVar(value=False)
        self.grid = tk.BooleanVar(value=True)
        self.span = tk.BooleanVar(value=False)
        self.xlabels = tk.StringVar(value="auto")

    def ymin_value(self):
        return parse_float(self.ymin.get(), f"Panel {self.number} y min")

    def ymax_value(self):
        return parse_float(self.ymax.get(), f"Panel {self.number} y max")

    def variables(self):
        return (self.title, self.ylabel, self.auto_y, self.ymin, self.ymax,
                self.legend, self.grid, self.span, self.xlabels)

    def state(self):
        return dict(title=self.title.get(), ylabel=self.ylabel.get(),
                    auto_y=self.auto_y.get(), ymin=self.ymin.get(), ymax=self.ymax.get(),
                    legend=self.legend.get(), grid=self.grid.get(), span=self.span.get(),
                    xlabels=self.xlabels.get())

    def restore(self, state):
        for key, var in (("title", self.title), ("ylabel", self.ylabel),
                         ("ymin", self.ymin), ("ymax", self.ymax),
                         ("xlabels", self.xlabels), ("auto_y", self.auto_y),
                         ("legend", self.legend), ("grid", self.grid), ("span", self.span)):
            var.set(state[key])
