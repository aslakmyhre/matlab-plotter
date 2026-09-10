"""The runs/ folder: one .mat log per run, titled by the values.md table."""
import os
import re

VALUES_FILE = "values.md"
# data_2-1-3-runG.mat -> G. A log named any other way keeps its own file name.
LETTER_PATTERN = re.compile(r"run([A-Za-z0-9]+)\.mat$", re.IGNORECASE)
# "G: p1=-20 p2=-25", with or without a list marker in front.
ENTRY_PATTERN = re.compile(r"^\s*(?:[-*]\s*)?([A-Za-z0-9]+)\s*:\s*(\S.*?)\s*$")


class Run:
    """One log file and the line values.md holds for it."""

    def __init__(self, name, path, description):
        self.name = name
        self.path = path
        self.description = description

    def title(self):
        head = self.name if self.name.lower().startswith("run") else f"Run {self.name}"
        return head + (f" — {self.description}" if self.description else "")

    def legend_label(self):
        return f"{self.name}: {self.description}" if self.description else self.name

    def listing(self):
        return f"{self.name:<3} {self.description or f'(no line in {VALUES_FILE})'}"


def read_values(folder):
    """The values.md table as {run name: description}, empty when there is no table.

    The table only titles the runs, so a folder without one still plots.
    """
    path = os.path.join(folder, VALUES_FILE)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        entries = {}
        for line in handle:
            match = ENTRY_PATTERN.match(line)
            if match:
                entries[match.group(1).upper()] = match.group(2)
    if not entries:
        raise ValueError(f"{path} holds no '<letter>: <values>' lines")
    return entries


def run_name(filename):
    """The letter of a ...run<letter>.mat log, else the file name without .mat."""
    match = LETTER_PATTERN.search(filename)
    return match.group(1).upper() if match else os.path.splitext(filename)[0]


def sort_key(name):
    """Runs in file-name order, with digit groups compared as numbers."""
    return [(int(part), "") if part.isdigit() else (0, part.lower())
            for part in re.split(r"(\d+)", name)]


def discover(folder):
    """Every .mat log in the folder, in name order, titled from values.md."""
    entries = read_values(folder)
    runs = [Run(name, os.path.join(folder, filename), entries.get(name.upper()))
            for filename in os.listdir(folder) if filename.lower().endswith(".mat")
            for name in [run_name(filename)]]
    if not runs:
        raise ValueError(f"{folder} holds no .mat files")
    return sorted(runs, key=lambda run: sort_key(run.name))
