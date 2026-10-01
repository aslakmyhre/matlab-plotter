"""Turning the panel configuration into matplotlib axes."""
from collections import namedtuple

import matplotlib.colors as mcolors

# One plotted line. Each carries its own time vector: overlaid runs are separate
# logs and rarely share a sample count. `label` names the line on hover; `legend` is
# what the legend shows, empty to leave the line out of it.
Series = namedtuple("Series", "label legend color style t values")

SURFACE, INK, INK_2 = "#fcfcfb", "#0b0b0b", "#52514e"

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
                    linewidth=settings["linewidth"], label=line.legend or "_nolegend_")
        _style(ax, panel, settings)
        _label_x(ax, panel, settings, id(panel) in bottom)
        if panel.legend.get() and any(line.legend for line in series[id(panel)]):
            ax.legend(loc="best", fontsize=8, frameon=False)
    if settings["title"]:
        figure.suptitle(settings["title"], x=0.02, ha="left", fontsize=12, color=INK)
    figure.subplots_adjust(hspace=0.4, wspace=0.24)
    return axes


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
