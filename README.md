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
