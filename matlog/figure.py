"""Turning the panel configuration into matplotlib axes."""
import math
import re
from collections import namedtuple
from contextlib import contextmanager

import matplotlib.colors as mcolors

# One plotted line. Each carries its own time vector: overlaid runs are separate
# logs and rarely share a sample count. `label` names the line on hover; `legend` is
# what the legend shows, empty to leave the line out of it. `depth` is the signal's place in
# the signal list: 0 is drawn in front of everything.
Series = namedtuple("Series", "label legend color style t values depth")

SURFACE, INK, INK_2 = "#ffffff", "#0b0b0b", "#52514e"

CM_PER_INCH = 2.54
LEGEND_FONT_PT = 8
# Height of one legend row, as a multiple of its font size.
LEGEND_ROW_FONTS = 1.7
# loc="best" tests every sample against the legend box, which stalls on long logs.
BEST_LEGEND_MAX_SAMPLES = 50000
# Lines stack between these, above the grid and the zero line, below the legend.
LINE_ZORDER_BACK, LINE_ZORDER_FRONT = 2.0, 2.5
TITLE_FONT_PT = 12
TITLE_MIN_FONT_PT = 7
# The share of the figure's width a title may take, leaving its left margin clear.
TITLE_MAX_WIDTH = 0.96
# Where a panel title may wrap: after the "·" between merged signal names if it has
# them, so no name is split, otherwise at any space.
SIGNAL_BREAK = re.compile("(?<= ·) ")
WORD_BREAK = re.compile(" ")

_COLOUR_ACCESSORS = (("get_color", "set_color"),
                     ("get_edgecolor", "set_edgecolor"),
                     ("get_facecolor", "set_facecolor"))


def place(panels, columns):
    """Walk the panels left to right, wrapping at the column count.

    A panel marked span takes the whole row, which is what gives layouts like
    two small plots on top of one wide one.
    """
    placements, row, col = [], 0, 0
    for panel in panels:
        span = columns if panel.span.get() else 1
        if col + span > columns:
            row, col = row + 1, 0
        placements.append((panel, row, col, span))
        col += span
        if col >= columns:
            row, col = row + 1, 0
    rows = row + 1 if col else row
    return placements, max(rows, 1)


def bottom_placements(placements):
    """The placements that sit lowest in every column they cover."""
    lowest = {}
    for _panel, row, col, span in placements:
        for c in range(col, col + span):
            lowest[c] = max(lowest.get(c, row), row)
    return {id(panel) for panel, row, col, span in placements
            if all(lowest[c] == row for c in range(col, col + span))}


def draw(figure, placements, rows, columns, series, settings):
    """Draw every panel. `series` maps a panel to its list of Series."""
    grid = figure.add_gridspec(rows, columns)
    bottom = bottom_placements(placements)
    axes, first = {}, None
    for panel, row, col, span in placements:
        ax = figure.add_subplot(grid[row, col:col + span],
                                sharex=first if settings["link_x"] else None)
        first = first or ax
        axes[id(panel)] = ax
        for line in series[id(panel)]:
            ax.plot(line.t, line.values, color=line.color, linestyle=line.style,
                    linewidth=settings["linewidth"], label=line.legend or "_nolegend_",
                    zorder=_line_zorder(line.depth))
        _style(ax, panel, settings)
        _label_x(ax, panel, settings, id(panel) in bottom)
    if settings["title"]:
        figure.suptitle(settings["title"], x=0.02, ha="left", fontsize=TITLE_FONT_PT, color=INK)
    relayout(figure)
    # After the layout, because a legend's columns depend on the height its panel ended up with.
    for panel, _row, _col, _span in placements:
        if panel.legend.get() and any(line.legend for line in series[id(panel)]):
            _legend(axes[id(panel)], series[id(panel)])
    return axes


def _line_zorder(depth):
    """Further down the list, further back. Lines of equal depth keep their drawing order."""
    return LINE_ZORDER_BACK + (LINE_ZORDER_FRONT - LINE_ZORDER_BACK) / (depth + 1)


def relayout(figure):
    """Fit everything to the figure's present size.

    A panel title wider than its panel, like a merged panel naming every signal, would
    make tight_layout squeeze the panel sideways to fit it. So the panels are laid out
    without their titles first, then each title wraps to its panel's width and the
    second pass only makes room for its height.
    """
    _fit_title(figure)
    titles = [ax._left_title for ax in figure.axes if ax._left_title.get_text()]
    for title in titles:
        title.set_text(title.get_text().replace("\n", " "))
        title.set_visible(False)
    figure.tight_layout()
    renderer = figure.canvas.get_renderer()
    for title in titles:
        # Hidden text measures as empty.
        title.set_visible(True)
        _wrap_to_panel(title, renderer)
    figure.tight_layout()


def _wrap_to_panel(title, renderer):
    """Break the title at spaces so each line fits its panel's width.

    Only spaces become line breaks, so joining the lines with spaces gives the title back.
    """
    room = title.axes.get_window_extent(renderer).width
    text = title.get_text()
    words = (SIGNAL_BREAK if SIGNAL_BREAK.search(text) else WORD_BREAK).split(text)
    lines = [words[0]]
    for word in words[1:]:
        title.set_text(f"{lines[-1]} {word}")
        if title.get_window_extent(renderer).width > room:
            lines.append(word)
        else:
            lines[-1] = f"{lines[-1]} {word}"
    title.set_text("\n".join(lines))


def _fit_title(figure):
    """Log names can be wider than the figure, so a long title gets smaller, not clipped."""
    title = figure._suptitle
    if title is None:
        return
    title.set_fontsize(TITLE_FONT_PT)
    width = title.get_window_extent(figure.canvas.get_renderer()).width
    room = figure.bbox.width * TITLE_MAX_WIDTH
    if width > room:
        title.set_fontsize(max(TITLE_MIN_FONT_PT, TITLE_FONT_PT * room / width))


def _legend(ax, lines):
    """A legend that stays inside its panel: more entries than fit go into more columns."""
    entries = sum(1 for line in lines if line.legend)
    samples = sum(len(line.t) for line in lines)
    row_pixels = LEGEND_FONT_PT * LEGEND_ROW_FONTS * ax.figure.dpi / 72
    rows_that_fit = max(1, int(ax.get_window_extent().height / row_pixels))
    ax.legend(loc="best" if samples <= BEST_LEGEND_MAX_SAMPLES else "upper right",
              fontsize=LEGEND_FONT_PT, ncols=math.ceil(entries / rows_that_fit),
              frameon=True, framealpha=0.85, facecolor=SURFACE, edgecolor="none",
              borderpad=0.3, handlelength=1.6, columnspacing=1.0)


@contextmanager
def sized_for_export(figure, size_cm):
    """Lay the figure out at this physical size while saving. None keeps the window's size."""
    if size_cm is None:
        yield
        return
    original = figure.get_size_inches().copy()
    figure.set_size_inches(size_cm[0] / CM_PER_INCH, size_cm[1] / CM_PER_INCH, forward=False)
    relayout(figure)
    try:
        yield
    finally:
        figure.set_size_inches(original, forward=False)
        relayout(figure)


def _style(ax, panel, settings):
    ax.set_facecolor(SURFACE)
    ax.grid(panel.grid.get(), color=INK_2, alpha=0.15, linewidth=0.6)
    ax.tick_params(colors=INK_2, labelsize=8)
    ax.axhline(0, color=INK_2, linewidth=0.6, alpha=0.35)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_2)
        ax.spines[side].set_alpha(0.4)
    if panel.title.get():
        ax.set_title(panel.title.get(), loc="left", fontsize=10, color=INK, pad=6)
    if panel.ylabel.get():
        ax.set_ylabel(panel.ylabel.get(), fontsize=9, color=INK_2)
    if not panel.auto_y.get():
        ax.set_ylim(panel.ymin_value(), panel.ymax_value())
    if not settings["auto_x"]:
        ax.set_xlim(settings["xmin"], settings["xmax"])


def _label_x(ax, panel, settings, is_bottom):
    mode = panel.xlabels.get()
    show = is_bottom if mode == "auto" else mode == "always"
    ax.tick_params(labelbottom=show)
    if show:
        ax.set_xlabel(settings["xlabel"], fontsize=9, color=INK_2)


def flatten_alpha(figure, background):
    """Blend every artist's alpha into its own colours, over `background`.

    PostScript has no alpha channel, so an EPS export would otherwise draw the
    grid, the zero line and the spines fully opaque. Returns a callable that
    puts the original colours back once the file is written.
    """
    base = mcolors.to_rgb(background)
    restore = []
    for artist in figure.findobj():
        alpha = artist.get_alpha()
        if alpha is None or alpha >= 1:
            continue
        for getter, setter in _COLOUR_ACCESSORS:
            read = getattr(artist, getter, None)
            if read is None:
                continue
            colour = read()
            if not mcolors.is_color_like(colour):
                continue
            write = getattr(artist, setter)
            restore.append((write, colour))
            write(_over(colour, alpha, base))
        restore.append((artist.set_alpha, alpha))
        artist.set_alpha(None)

    def undo():
        for write, value in reversed(restore):
            write(value)

    return undo


def _over(colour, alpha, base):
    return tuple(alpha * c + (1 - alpha) * b
                 for c, b in zip(mcolors.to_rgb(colour), base))
