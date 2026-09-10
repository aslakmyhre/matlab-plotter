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

The **Runs** tab reads a folder of logs named `…run<letter>.mat` alongside a `values.md`
that titles them, one line per run:

```
C: p1=-1 p2=-2
G: p1=-20 p2=-25
L: p1=-3+5i p2=-3-5i
```

A folder named `runs/` next to the app is picked up on start; any other folder can be
chosen. Each run gets a line in the tab:

- **▶** shows that run on its own, titling the figure `Run G — p1=-20 p2=-25`. Stepping
  from one run to the next keeps the names, panels and expressions already set up.
- the **tick box** includes the run in an overlay. *Overlay ticked runs* draws one panel
  per ticked signal, one line per run, each labelled with its `values.md` line. Runs of
  different lengths are fine — every line carries its own time vector.
- **Merge signals into one panel** puts every line in a single panel instead: colour is
  the run, dash pattern is the signal.

A run with no line in `values.md` is still listed, and says so.

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
