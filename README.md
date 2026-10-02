# MAT log plotter

Tkinter GUI for plotting signals out of MATLAB `.mat` log files.

```
python3 mat_plotter.py [file.mat]
```

## Requirements

- Python 3.9+
- **tkinter** — ships with the stdlib but is a separate OS package on Linux and on Homebrew Python (see below)
- Packages from `requirements.txt`: `numpy`, `scipy` (reads `.mat` via `scipy.io.loadmat`), `matplotlib`

## Setup

There is no way to make `git clone` install dependencies by itself — git runs no hooks on the client after a clone. The closest thing is one command after cloning.

### macOS / Linux

```bash
git clone https://github.com/aslakmyhre/matlab-plotter.git
cd matlab-plotter
./setup.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/aslakmyhre/matlab-plotter.git
cd matlab-plotter
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

Both scripts create `.venv/` in the repo, upgrade pip, and install `requirements.txt`. They abort with instructions if Python or tkinter is missing.

### Manual, if you prefer

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python mat_plotter.py
```

### One-liner with uv

If you have [uv](https://docs.astral.sh/uv/), no setup step is needed — the venv is created and dependencies installed on first run:

```bash
uv run --with-requirements requirements.txt mat_plotter.py [file.mat]
```

## Running

```bash
./.venv/bin/python mat_plotter.py path/to/log.mat    # macOS/Linux
.\.venv\Scripts\python.exe mat_plotter.py path\to\log.mat   # Windows
```

Or activate the venv first (`source .venv/bin/activate`) and just use `python mat_plotter.py`.

## A folder of runs

The **Runs** tab lists every `.mat` log below a chosen folder, subfolders included, as a
tree. A folder named `runs/` next to the app is picked up on start; any other folder can
be chosen. Runs are named by their path below that folder, e.g. `day2/data_2-1-3-runC`.

- **Click a run** to plot it on its own. Moving from one run to the next keeps the names,
  panels and expressions already set up. **Up/Down** steps through the runs.
- **Select several** (ctrl/⌘-click, shift-click, or click a folder for every run in it)
  and they are overlaid: one panel per selected signal, one line per run. Runs of
  different lengths are fine — every line carries its own time vector.
- **Signals to overlay** starts as whatever is plotted for the single run; change the
  selection to pick others.
- **Filter** narrows the list to runs whose path contains the text.
- **All / None / Invert** under each list change the selection in one go.
- **Hover a line** to highlight it and see which run (and, merged, which signal) it is.
- **Layout** sets how the selected signals are laid out:
  - *Overlay*: a panel per signal, a line per run.
  - *Merged*: every line in one panel. Colour is the run, dash pattern is the signal.
  - *Grid*: a panel per signal and run, one row per signal and one column per run, so
    the same signal of different runs sits side by side.
  - *Side by side*: a panel per run, in one row, each holding that run's selected
    signals together. Colour is the signal, the same in every panel.

  Merged, Grid and Side by side work on a single run too, showing just its selected
  signals.

Edits in the Signals, Panels and Figure tabs redraw on their own once you stop typing.

## Legends and line styles

The **Lines** tab lists every plotted line under its panel, with a Legend box per panel.
Each line's legend text starts as the automatic label (signal name and unit for one run,
the run's path when runs are overlaid) and follows renames until you edit it. Clear the
text to leave a line out of the legend. Click a line's colour swatch to pick its colour.
The style menu sets a line solid, dashed, dotted or dash-dot; *auto* keeps the view's own
choice. **Reset all** puts text, colour and style back to automatic. Lines of a single
run keep their legend, style and colour while stepping through runs, and
**Save settings…** stores them.

## Signal names

A Simulink *To File* log holds only numbers: row 0 is time, then one row per Mux input,
with no names. Name the signals in the **Signals** tab at any time, then **Save names…**
writes them to a `signals.json`. A log picks up the `signals.json` in its own folder or
the nearest folder above it, so one file in `LQR med integral/` names every run below it,
while a subfolder logged another way can carry its own. A file listing a different
number of signals than the log has is not applied, and the Signals tab says why.
**Load names…** applies any names file by hand.

```json
{"signals": [{"name": "Time", "unit": "s"}, {"name": "Travel", "unit": "rad"}]}
```

## tkinter per platform

tkinter is not installable from pip — it comes from the OS or the Python build.

| Platform | Command |
| --- | --- |
| Debian / Ubuntu | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-tkinter` |
| Arch | `sudo pacman -S tk` |
| macOS (Homebrew Python) | `brew install python-tk` |
| macOS (python.org installer) | already included |
| Windows | included, as long as "tcl/tk and IDLE" is ticked in the installer |

Check it:

```bash
python3 -c "import tkinter; print('ok')"
```

## Windows .exe (no internet needed on the target machine)

`mat_plotter.spec` builds a single `MatLogPlotter.exe` that bundles Python, tkinter,
numpy, scipy and matplotlib. Copy the file onto the target machine and double-click it —
no installer, no Python, no network.

PyInstaller cannot cross-compile, so the exe must be produced **on Windows**. Two ways:

**On a Windows machine** (needs internet once, for pip):

```powershell
powershell -ExecutionPolicy Bypass -File .\build-windows.ps1
```

Output: `dist\MatLogPlotter.exe`.

**Via GitHub Actions**, if you have no Windows machine: run the *Build Windows exe*
workflow (Actions tab → Run workflow, or push a `v*` tag) and download the
`MatLogPlotter-windows` artifact.
