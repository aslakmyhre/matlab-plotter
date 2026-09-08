"""Plot MATLAB .mat logs.

Run:
    python3 mat_plotter.py [file.mat]
"""
import sys
import tkinter as tk

from matlog.app import App


def main():
    root = tk.Tk()
    root.title("MAT log plotter")
    root.geometry("1500x900")
    app = App(root)
    if len(sys.argv) > 1:
        app.open_file(sys.argv[1])
    root.mainloop()


if __name__ == "__main__":
    main()
