# Creates .venv and installs dependencies. Windows PowerShell.
$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) { $python = "py"; $pyArgs = @("-3") } else {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { throw "Python not found. Install Python 3.9+ from python.org (tick 'Add to PATH' and 'tcl/tk')." }
    $python = "python"; $pyArgs = @()
}

& $python @pyArgs -c "import tkinter" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "tkinter missing. Re-run the python.org installer and enable 'tcl/tk and IDLE'." }

& $python @pyArgs -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host ""
Write-Host "Done. Run with:"
Write-Host "  .\.venv\Scripts\python.exe mat_plotter.py [file.mat]"
