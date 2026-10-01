"""Crosshair that picks out and reads the plotted line under the pointer."""
import numpy as np

from .figure import INK, INK_2, SURFACE

# How close, in screen pixels, the pointer must come to a line to pick it out.
HOVER_PIXELS = 8
# The picked line is redrawn this much wider than the others.
HIGHLIGHT_WIDTH = 2.0


class Crosshair:
    """A vertical marker, drawn by blitting, plus a tag on the line under the pointer.

    The line nearest the pointer is redrawn wide and tagged with its label and value,
    so one run can be picked out of an overlay without matching legend colours.
    """

    def __init__(self, canvas):
        self.canvas = canvas
        self.enabled = True
        self.background = None
        self.entries = []
        canvas.mpl_connect("draw_event", self._on_draw)
        canvas.mpl_connect("motion_notify_event", self._on_move)
        canvas.mpl_connect("axes_leave_event", lambda _e: self.hide())

    def attach(self, axes_series, linewidth=1.0):
        """Rebuild the overlay artists. `axes_series` is [(ax, [Series])]."""
        self.entries = []
        for ax, series in axes_series:
            line = ax.axvline(0, color=INK_2,
                              linewidth=0.8, alpha=0.6, animated=True, visible=False)
            highlight = ax.plot([], [], linewidth=linewidth + HIGHLIGHT_WIDTH,
                                animated=True, visible=False)[0]
            tag = ax.annotate("", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
                              fontsize=8, color=INK, animated=True, visible=False,
                              bbox=dict(boxstyle="round,pad=0.3", facecolor=SURFACE,
                                        edgecolor=INK_2, linewidth=0.5))
            self.entries.append((ax, line, highlight, tag, series))
        self.background = None

    def _on_draw(self, _event):
        self.background = self.canvas.copy_from_bbox(self.canvas.figure.bbox)

    def _on_move(self, event):
        if not self.enabled or event.inaxes is None or not self.entries:
            return
        if self.background is None:
            self.background = self.canvas.copy_from_bbox(self.canvas.figure.bbox)
        x = event.xdata
        self.canvas.restore_region(self.background)
        for ax, line, highlight, tag, series in self.entries:
            line.set_xdata([x, x])
            line.set_visible(True)
            ax.draw_artist(line)
            picked = _nearest(ax, series, x, event.y) if ax is event.inaxes else None
            highlight.set_visible(picked is not None)
            tag.set_visible(picked is not None)
            if picked is not None:
                chosen, y = picked
                highlight.set_data(chosen.t, chosen.values)
                highlight.set_color(chosen.color)
                highlight.set_linestyle(chosen.style)
                tag.xy = (x, y)
                tag.set_text(f"{chosen.legend or chosen.label}\n{y:.4g} at t = {x:.4g}")
                ax.draw_artist(highlight)
                ax.draw_artist(tag)
        self.canvas.blit(self.canvas.figure.bbox)

    def hide(self):
        for _ax, line, highlight, tag, _series in self.entries:
            for artist in (line, highlight, tag):
                artist.set_visible(False)
        if self.background is not None:
            self.canvas.restore_region(self.background)
            self.canvas.blit(self.canvas.figure.bbox)


def _value_at(series, x):
    """The series value at time x, or None where the series does not reach."""
    t = series.t
    if len(t) == 0 or x < t[0] or x > t[-1]:
        return None
    return series.values[int(np.clip(np.searchsorted(t, x), 0, len(t) - 1))]


def _nearest(ax, series, x, pointer_y):
    """The (series, value) drawn closest above or below the pointer, if near enough."""
    best, best_distance = None, HOVER_PIXELS
    for line in series:
        value = _value_at(line, x)
        if value is None or not np.isfinite(value):
            continue
        distance = abs(ax.transData.transform((x, value))[1] - pointer_y)
        if distance <= best_distance:
            best, best_distance = (line, value), distance
    return best
