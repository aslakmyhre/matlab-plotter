"""Signal names and units, kept in a signals.json beside the logs they describe.

A To File log stores only numbers, so the names have to live outside it. The file
nearest above a log applies to it, which lets one file cover a whole experiment
folder while a subfolder logged another way carries its own.
"""
import json
import os

NAMES_FILE = "signals.json"


def find(folder):
    """The signals.json in folder or the nearest folder above it, else None."""
    folder = os.path.abspath(folder)
    while True:
        candidate = os.path.join(folder, NAMES_FILE)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(folder)
        if parent == folder:
            return None
        folder = parent


def load(path):
    """[(name, unit)] in row order."""
    with open(path, encoding="utf-8") as handle:
        content = json.load(handle)
    signals = content.get("signals") if isinstance(content, dict) else None
    if not isinstance(signals, list) or not all(
            isinstance(s, dict) and isinstance(s.get("name"), str)
            and isinstance(s.get("unit", ""), str) for s in signals):
        raise ValueError(f"{path} needs a \"signals\" list of {{\"name\", \"unit\"}} entries")
    return [(s["name"], s.get("unit", "")) for s in signals]


def save(path, pairs):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"signals": [{"name": name, "unit": unit} for name, unit in pairs]},
                  handle, indent=2, ensure_ascii=False)
