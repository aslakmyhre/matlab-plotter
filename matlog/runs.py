"""The runs/ folder: one .mat log per run, titled by the values.md table."""
import os
import re

VALUES_FILE = "values.md"
# data_2-1-3-runG.mat -> G
RUN_PATTERN = re.compile(r"run([A-Za-z0-9]+)\.mat$", re.IGNORECASE)
# "G: p1=-20 p2=-25", with or without a list marker in front.
ENTRY_PATTERN = re.compile(r"^\s*(?:[-*]\s*)?([A-Za-z0-9]+)\s*:\s*(\S.*?)\s*$")


class Run:
    """One log file and the line values.md holds for it."""

    def __init__(self, letter, path, description):
        self.letter = letter
        self.path = path
        self.description = description

    def title(self):
        return f"Run {self.letter}" + (f" — {self.description}" if self.description else "")

    def legend_label(self):
        return f"{self.letter}: {self.description}" if self.description else self.letter

    def listing(self):
        return f"{self.letter:<3} {self.description or f'(no line in {VALUES_FILE})'}"


def read_values(folder):
    """The values.md table as {run letter: description}."""
    path = os.path.join(folder, VALUES_FILE)
    with open(path, encoding="utf-8") as handle:
        entries = {}
        for line in handle:
            match = ENTRY_PATTERN.match(line)
            if match:
                entries[match.group(1).upper()] = match.group(2)
    if not entries:
        raise ValueError(f"{path} holds no '<letter>: <values>' lines")
    return entries


def discover(folder):
    """Every run log in the folder, ordered by letter, titled from values.md."""
    entries = read_values(folder)
    runs = [Run(match.group(1).upper(), os.path.join(folder, name),
                entries.get(match.group(1).upper()))
            for name in os.listdir(folder)
            for match in [RUN_PATTERN.search(name)] if match]
    if not runs:
        raise ValueError(f"{folder} holds no ...run<letter>.mat files")
    return sorted(runs, key=lambda run: run.letter)
