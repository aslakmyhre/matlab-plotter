# PyInstaller spec for the Windows one-file build.
# Build on Windows: pyinstaller --clean --noconfirm mat_plotter.spec

block_cipher = None

a = Analysis(
    ['mat_plotter.py'],
    pathex=[],
    binaries=[],
    datas=[],
    # scipy.io.matlab picks its reader modules at call time, so PyInstaller's
    # import graph does not see them.
    hiddenimports=[
        'scipy.io.matlab',
        'scipy.io.matlab._mio5_utils',
        'scipy.io.matlab._streams',
        'scipy.io.matlab._mio_utils',
    ],
    hookspath=[],
    runtime_hooks=[],
    # Backends other than TkAgg drag in PyQt/wx/GTK and roughly double the exe.
    excludes=[
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_webagg',
        'IPython', 'jupyter', 'notebook', 'pytest', 'setuptools._distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MatLogPlotter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
