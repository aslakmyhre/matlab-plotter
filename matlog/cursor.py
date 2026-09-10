"""Crosshair that reads every plotted signal at the hovered time."""
import numpy as np

from .figure import INK, INK_2, SURFACE


class Crosshair:
    """A vertical marker plus a per-panel value box, drawn by blitting."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.enabled = True
        self.background = None
        self.entries = []
        canvas.mpl_connect("draw_event", self._on_draw)
        canvas.mpl_connect("motion_notify_event", self._on_move)
        canvas.mpl_connect("axes_leave_event", lambda _e: self.hide())

    def attach(self, axes_series):
        """Rebuild the overlay artists. `axes_series` is [(ax, [(label, t, values)])]."""
        self.entries = []
        for ax, series in axes_series:
            line = ax.axvline(0, color=INK_2,
                              linewidth=0.8, alpha=0.6, animated=True, visible=False)
            text = ax.text(0.99, 0.96, "", transform=ax.transAxes, ha="right", va="top",
                           fontsize=8, color=INK, animated=True, visible=False,
                           bbox=dict(boxstyle="round,pad=0.3", facecolor=SURFACE,
                                     edgecolor=INK_2, alpha=0.85, linewidth=0.5))
            self.entries.append((ax, line, text, series))
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
        for ax, line, text, series in self.entries:
            line.set_xdata([x, x])
            text.set_text("\n".join([f"t = {x:.4g}"]
                                    + [_reading(label, t, values, x)
                                       for label, t, values in series]))
            line.set_visible(True)
            text.set_visible(True)
            ax.draw_artist(line)
            ax.draw_artist(text)
        self.canvas.blit(self.canvas.figure.bbox)

    def hide(self):
        for _ax, line, text, _series in self.entries:
            line.set_visible(False)
            text.set_visible(False)
        if self.background is not None:
            self.canvas.restore_region(self.background)
            self.canvas.blit(self.canvas.figure.bbox)


def _reading(label, t, values, x):
    """One line of the readout, blank where this series does not reach."""
    if len(t) == 0 or x < t[0] or x > t[-1]:
        return f"{label} = \u2013"
    index = int(np.clip(np.searchsorted(t, x), 0, len(t) - 1))
    return f"{label} = {values[index]:.4g}"
