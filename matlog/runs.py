"""A folder of runs: every .mat log below it, subfolders included."""
import os
import posixpath
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


def _is_number(token):
    try:
        float(token)
    except ValueError:
        return False
    return True


def _differing_parts(names):
    """Each name cut down to the "_" separated parts that differ, plus what labels them.

    Log names repeat most of their parameters, so run_136_q1_3.60_q2_2.50_... against
    run_137_q1_3.60_q2_0.25_... comes out as "run 136 q2 2.50" and "run 137 q2 0.25".
    """
    split = [name.split("_") for name in names]
    if len({len(parts) for parts in split}) != 1:
        return names
    keep = set()
    for position, column in enumerate(zip(*split)):
        if len(set(column)) > 1:
            keep.add(position)
            if position and not _is_number(split[0][position - 1]):
                keep.add(position - 1)
    if not keep:
        return names
    return [" ".join(parts[i] for i in sorted(keep)) for parts in split]


def short_labels(chosen):
    """{run path: just enough of its name to tell these runs apart}."""
    if len(chosen) == 1:
        return {chosen[0].path: chosen[0].label}
    names = _differing_parts([run.name for run in chosen])
    shared = posixpath.commonpath([run.folder for run in chosen])
    labels = {}
    for run, name in zip(chosen, names):
        below = run.folder[len(shared):].lstrip("/")
        labels[run.path] = f"{below}/{name}" if below else name
    return labels


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
