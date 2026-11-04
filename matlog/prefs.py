"""What the app remembers between sessions, in the user's config folder."""
import json
import os
import re
import sys

APP_FOLDER = "MatLogPlotter"
PREFS_FILE = "prefs.json"
MAX_RECENT = 8
_GEOMETRY = re.compile(r"(\d+)x(\d+)([+-]-?\d+)([+-]-?\d+)$")


def config_folder():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, APP_FOLDER)


def prefs_path():
    return os.path.join(config_folder(), PREFS_FILE)


def load():
    """The saved preferences, {} before the first save. Raises ValueError if unreadable."""
    path = prefs_path()
    try:
        with open(path, encoding="utf-8") as handle:
            content = json.load(handle)
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(content, dict):
        raise ValueError(f"{path} does not hold a settings object")
    return content


def save(prefs):
    """Write through a temporary file, so a crash cannot leave half a file behind."""
    folder = config_folder()
    os.makedirs(folder, exist_ok=True)
    path = prefs_path()
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(prefs, handle, indent=2, ensure_ascii=False)
    os.replace(temporary, path)


def with_recent(recent, path):
    """`recent` with `path` moved to the front."""
    path = os.path.abspath(path)
    return ([path] + [item for item in recent if item != path])[:MAX_RECENT]


def existing_recent(prefs):
    """The recent paths still on disk, ignoring anything malformed in the file."""
    recent = prefs.get("recent", [])
    if not isinstance(recent, list):
        return []
    return [item for item in recent if isinstance(item, str) and os.path.exists(item)]


def saved_int(prefs, key, default, low, high):
    """An integer preference within its range, else the default."""
    value = prefs.get(key)
    if isinstance(value, int) and not isinstance(value, bool) and low <= value <= high:
        return value
    return default


def default_geometry(screen_width, screen_height, max_width, max_height):
    """A window that fits the screen, centred."""
    width = min(max_width, int(screen_width * 0.92))
    height = min(max_height, int(screen_height * 0.88))
    return f"{width}x{height}+{(screen_width - width) // 2}+{(screen_height - height) // 3}"


def fitted_geometry(saved, screen_width, screen_height, max_width, max_height):
    """The saved window geometry if it is still on this screen, else a fresh one."""
    match = _GEOMETRY.match(saved) if isinstance(saved, str) else None
    if match:
        width, height = int(match.group(1)), int(match.group(2))
        x, y = int(match.group(3)), int(match.group(4))
        # A monitor unplugged since the last run must not leave the window out of reach.
        if width <= screen_width and height <= screen_height and (
                0 <= x < screen_width - 40 and 0 <= y < screen_height - 40):
            return saved
    return default_geometry(screen_width, screen_height, max_width, max_height)
