#!/usr/bin/env bash
# Creates .venv and installs dependencies. macOS / Linux.
set -euo pipefail

cd "$(dirname "$0")"

PY=python3
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "python3 not found. Install Python 3.9+ first." >&2
    exit 1
fi

if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
    echo "tkinter missing from this Python. Install it, then re-run:" >&2
    echo "  Debian/Ubuntu: sudo apt install python3-tk" >&2
    echo "  Fedora:        sudo dnf install python3-tkinter" >&2
    echo "  Arch:          sudo pacman -S tk" >&2
    echo "  macOS:         brew install python-tk" >&2
    exit 1
fi

"$PY" -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

echo
echo "Done. Run with:"
echo "  ./.venv/bin/python mat_plotter.py [file.mat]"
