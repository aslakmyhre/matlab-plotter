"""Signal names and units, kept in a signals….json beside the logs they describe.

A To File log stores only numbers, so the names have to live outside it. The files
nearest above a log apply to it, which lets one file cover a whole experiment
folder while a subfolder logged another way carries its own. Any .json whose name
starts with "signals" counts, so one folder can hold several sets to choose from.
"""
import json

from . import nearby

NAMES_FILE = "signals.json"
NAMES_PREFIX = "signals"


def is_names_file(name):
    return nearby.is_json(name) and name.lower().startswith(NAMES_PREFIX)


def find(folder):
    """The names files in folder or the nearest folder above that has any, [] if none."""
    return nearby.nearest(folder, is_names_file)


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
