# Builds dist\MatLogPlotter.exe. Run on Windows, with internet available.
# The resulting exe needs no internet and no Python on the target machine.
$ErrorActionPreference = 'Stop'

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) { $py = 'py'; $pyArgs = @('-3') } else { $py = 'python'; $pyArgs = @() }

& $py @pyArgs -c "import tkinter" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "tkinter missing. Reinstall Python from python.org with the 'tcl/tk and IDLE' option checked."
}

if (-not (Test-Path .venv)) {
    & $py @pyArgs -m venv .venv
}

$venvPy = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r requirements.txt pyinstaller
& $venvPy -m PyInstaller --clean --noconfirm mat_plotter.spec

Write-Host ""
Write-Host "Built: $(Join-Path $PSScriptRoot 'dist\MatLogPlotter.exe')"
