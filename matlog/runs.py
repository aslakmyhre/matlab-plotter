"""A folder of runs: every .mat log below it, subfolders included."""
import os
import re

RUN_EXTENSION = ".mat"


class Run:
    """One log file, named by its path below the chosen folder."""

    def __init__(self, path, root):
        self.path = path
        relative = os.path.relpath(path, root)
        # "/" on every platform, so labels read the same on Windows. "" is the root itself.
        self.folder = os.path.dirname(relative).replace(os.sep, "/")
        self.name = os.path.splitext(os.path.basename(relative))[0]
        self.label = f"{self.folder}/{self.name}" if self.folder else self.name

    def matches(self, text):
        return text.lower() in self.label.lower()


def sort_key(name):
    """File-name order, with digit groups compared as numbers."""
    return [(int(part), "") if part.isdigit() else (0, part.lower())
            for part in re.split(r"(\d+)", name)]


def discover(root):
    """Every .mat log below root, folder by folder, in name order."""
    if not os.path.isdir(root):
        raise ValueError(f"{root!r} is not a folder")
    runs = []
    for folder, subfolders, files in os.walk(root):
        # Hidden folders hold tool state (.git, .venv), never logs.
        subfolders[:] = sorted((d for d in subfolders if not d.startswith(".")), key=sort_key)
        runs.extend(Run(os.path.join(folder, name), root)
                    for name in sorted(files, key=sort_key)
                    if name.lower().endswith(RUN_EXTENSION))
    if not runs:
        raise ValueError(f"{root} holds no {RUN_EXTENSION} files, subfolders included")
    return runs
