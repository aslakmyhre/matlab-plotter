# MAT log plotter

A desktop app for browsing, comparing and exporting signals from MATLAB `.mat` log files.
It looks the same on Windows, Linux and macOS.

```
python3 mat_plotter.py [file.mat | folder]
```

Run without arguments it reopens the last folder. Window size, panes, layout and export
settings are remembered too, in `prefs.json` in `%APPDATA%\MatLogPlotter`,
`~/Library/Application Support/MatLogPlotter` or `~/.config/MatLogPlotter`. Delete that file
to start fresh.

## Requirements

- Python 3.9+
- **tkinter** — ships with the stdlib but is a separate OS package on Linux and on Homebrew Python (see below)
- Packages from `requirements.txt`: `numpy`, `scipy` (reads `.mat` via `scipy.io.loadmat`), `matplotlib`, `pillow` (already required by matplotlib)

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

Both scripts create `.venv/` in the repo, upgrade pip, and install `requirements.txt`. They abort with instructions if Python or tkinter is missing. `setup.sh` also checks for venv support (`python3-venv` on Debian/Ubuntu) and that EPS export works.

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

## The window

- **Left: what to plot.** Runs on top, signals below.
- **Middle: the plot.**
- **Right: how it looks.** The Signals, Panels, Lines, Figure and Data tabs. **Settings** in
  the top bar hides them.

### Runs

**Open folder…** lists every `.mat` log below a folder, subfolders included. Runs are named by
their path below it, e.g. `day2/data_2-1-3-runC`. A folder named `runs/` next to the app is
picked up when there is no last folder to reopen.

- **Click a run** to plot it. Moving between runs keeps the names, panels, expressions and
  zoom. **↑ / ↓** step through the runs from anywhere but a text field.
- **Ctrl/⌘-click or shift-click** adds or drops a run, and **click a folder** for every run in
  it. Runs of different lengths are fine: every line carries its own time vector.
- **Filter** narrows the list to runs whose path contains the text. Esc clears it.
- Hover a run for its full name.

### Signals

**Tick the signals to plot.** The ticks apply in every view and stay while you move between
runs. A newly ticked signal gets its own panel. To put several signals in one panel, choose
the same panel for them in the Signals tab. Click a colour patch to change the colour.

### Layout

The buttons in the top bar lay out the ticked signals, for one run or several:

- *Overlay*: a panel per signal, a line per run.
- *Merged*: every line in one panel. Colour is the run, dash pattern is the signal.
- *Grid*: a panel per signal and run, one row per signal and one column per run.
- *Side by side*: a panel per run, each holding that run's signals. Colour is the signal, the
  same in every panel.

### The plot

- **Scroll** (or two fingers) zooms time around the pointer, **shift-scroll** zooms y.
- **Double-click** or **Reset** returns to the full view. **Pan** and **Zoom box** are below
  the plot.
- The zoom is kept while stepping through runs and editing settings, so the same window can
  be compared across runs. A limit typed in the Figure or Panels tab replaces it.
- **Hover a line** to highlight it and read its value.

Edits redraw on their own once you stop typing. If a value is invalid, the plot stays as it
was and the status bar says what is wrong. Limits accept a decimal comma, and a limit left
blank stays automatic.

All keyboard shortcuts are under **Help → Mouse and Keyboard**.

## Exporting figures

**Export…** saves PNG, PDF, SVG or EPS, named after the figure title, starting in the last
folder used.

By default a figure comes out the size it is on screen. For figures that match across a
report, pick a fixed size under **Figure → Export**: full width (16 × 9 cm), half width
(8 × 6 cm), slide (25 × 14 cm) or custom. Text keeps its point size, so it reads the same on
paper however small the figure is. **PNG dpi** sets the resolution of PNG files.

## Legends and line styles

Overlaid runs get a legend on the first panel, using only the part of the run names that
differs (`run 136 q2 2.50`). The **Lines** tab lists every plotted line under its panel, with a
Legend box per panel. A line's text follows renames until you edit it. Clear the text to leave
a line out of the legend. Click a line's colour patch to pick its colour. The style menu sets a
line solid, dashed, dotted or dash-dot; *auto* keeps the view's own choice. **Reset all** puts
text, colour and style back to automatic. Lines of a single run keep their legend, style and
colour while stepping through runs, and **Figure → Settings file → Save…** stores them.

## Derived signals

**+ Derived signal** in the Signals tab adds a signal computed from the others, such as
`deg(pitch) - deg(p_c)`. The names it can use are listed below the table. Derived signals plot
for a single run in the Overlay layout.

## Signal names

A Simulink *To File* log holds only numbers: row 0 is time, then one row per Mux input,
with no names. Name the signals in the **Signals** tab at any time, then **Save names…**
writes them to a `signals.json`. A log picks up the `signals.json` in its own folder or
the nearest folder above it, so one file in `LQR med integral/` names every run below it,
while a subfolder logged another way can carry its own. A file listing a different
number of signals than the log has is not applied, and the Signals tab says why. A signal
whose name is left blank counts as an unused input and starts unticked.
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
