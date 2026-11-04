"""Plot MATLAB .mat logs.

Run:
    python3 mat_plotter.py [file.mat | folder]
"""
import os
import sys
import tkinter as tk

from matlog import theme
from matlog.app import App


def enable_sharp_text_on_windows():
    """Without this, Windows renders the window small and stretches it into a blur."""
    if sys.platform == "win32":
        import ctypes
        per_monitor_aware = 1
        ctypes.windll.shcore.SetProcessDpiAwareness(per_monitor_aware)


def main():
    enable_sharp_text_on_windows()
    root = tk.Tk()
    theme.apply(root)
    app = App(root)
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.isdir(target):
            app.open_folder(target)
        else:
            app.open_file(target)
    else:
        app.reopen_last_folder()
    root.mainloop()


if __name__ == "__main__":
    main()
