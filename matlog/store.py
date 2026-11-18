"""Saving what the user set up: plot configuration and the plotted data."""
import csv
import json

import numpy as np

from . import nearby

# A .json whose name holds this is offered when logs beside it or below it are opened.
SETTINGS_PART = "settings"


def is_settings_file(name):
    return nearby.is_json(name) and SETTINGS_PART in name.lower()


def find_settings(folder):
    """The settings files in folder or the nearest folder above that has any, [] if none."""
    return nearby.nearest(folder, is_settings_file)


def save_config(path, state):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def load_config(path):
    with open(path, encoding="utf-8") as handle:
        state = json.load(handle)
    if not isinstance(state, dict):
        raise ValueError(f"{path} does not hold plot settings")
    return state


def export_csv(path, t, columns, window):
    """Write the plotted signals over the visible time window."""
    low, high = window
    mask = (t >= low) & (t <= high)
    if not mask.any():
        raise ValueError(f"no samples between {low:.4g} and {high:.4g}")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time"] + [name for name, _values in columns])
        rows = np.column_stack([t[mask]] + [values[mask] for _name, values in columns])
        writer.writerows(rows)
    return int(mask.sum())
