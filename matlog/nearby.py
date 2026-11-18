"""Finding the files that describe a log: in its folder, or the nearest folder above."""
import os

from .runs import sort_key

JSON_EXTENSION = ".json"


def nearest(folder, matches):
    """The files in `folder` or the nearest folder above that has any whose name `matches`.

    Several in one folder all come back, in name order, so the caller can ask which one.
    """
    folder = os.path.abspath(folder)
    while True:
        try:
            names = os.listdir(folder)
        except PermissionError:
            # A folder above the logs that cannot be listed holds nothing for them, like
            # the isfile test this replaced; the search goes on above it.
            names = []
        found = [os.path.join(folder, name) for name in sorted(names, key=sort_key)
                 if matches(name) and os.path.isfile(os.path.join(folder, name))]
        if found:
            return found
        parent = os.path.dirname(folder)
        if parent == folder:
            return []
        folder = parent


def is_json(name):
    return name.lower().endswith(JSON_EXTENSION)
