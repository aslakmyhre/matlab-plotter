"""One look on every platform: ttk's clam theme, recoloured and scaled to the display.

Clam draws every element itself from these colours, so Windows, Linux and macOS render
the same widgets instead of three different native sets.
"""
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from PIL import Image, ImageDraw, ImageTk

SURFACE = "#ffffff"
SUNKEN = "#f0f1f4"
BORDER = "#dfe1e6"
BORDER_STRONG = "#b9bec7"
INK = "#1c1f24"
INK_2 = "#5a606a"
INK_3 = "#868c96"
ACCENT = "#1f6bc4"
ACCENT_HOVER = "#1a5ca9"
ACCENT_SOFT = "#dbe9fa"
ERROR = "#c4322f"

BASE_FONT_PX = 13
SMALL_FONT_PX = 12
HEADING_FONT_PX = 12
DISPLAY_FONT_PX = 22
DISPLAY_FONT = "AppDisplayFont"
# Preferred first. Tk substitutes silently for a missing family, so these are checked
# against what the system really has.
FONT_FAMILIES = ("Segoe UI", "Inter", "Cantarell", "Ubuntu", "Noto Sans", "Roboto",
                 "DejaVu Sans", "Liberation Sans")
FIXED_FAMILIES = ("Cascadia Mono", "Consolas", "SF Mono", "Menlo", "JetBrains Mono",
                  "Ubuntu Mono", "Noto Sans Mono", "DejaVu Sans Mono", "Liberation Mono")
# Tick boxes and radio dots are drawn this much larger, then scaled down for smooth edges.
SUPERSAMPLE = 4
INDICATOR_PX = 14
INDICATOR_GAP_PX = 6
# Icon pixels, as rows of what to paint: a rising trace on an accent square.
ICON_SIZE = 32
ICON_TRACE = ((5, 22), (10, 22), (14, 11), (18, 19), (22, 8), (27, 8))

_scale = 1.0


def px(pixels):
    """A size given for a 96 dpi display, in this display's pixels."""
    return max(1, round(pixels * _scale))


def apply(root):
    """Set the whole window up. Call once, before building any widget."""
    global _scale
    # Aqua lays out in points and scales to Retina itself.
    if root.tk.call("tk", "windowingsystem") != "aqua":
        _scale = max(1.0, root.winfo_fpixels("1i") / 96)
    root.configure(background=SURFACE)
    _configure_fonts(root)
    _configure_classic_widgets(root)
    _configure_styles(root)
    _unbind_wheel_from_value_widgets(root)
    _set_icon(root)


def _first_available(root, families):
    available = set(tkfont.families(root))
    return next((family for family in families if family in available), None)


def _configure_fonts(root):
    # macOS's default font already is its system font, which no family name reaches.
    aqua = root.tk.call("tk", "windowingsystem") == "aqua"
    family = None if aqua else _first_available(root, FONT_FAMILIES)
    fixed = _first_available(root, FIXED_FAMILIES)
    # Negative sizes are pixels, so text is the same size whatever Tk thinks a point is.
    for name, size in (("TkDefaultFont", BASE_FONT_PX), ("TkTextFont", BASE_FONT_PX),
                       ("TkMenuFont", BASE_FONT_PX), ("TkCaptionFont", BASE_FONT_PX),
                       ("TkHeadingFont", HEADING_FONT_PX), ("TkTooltipFont", SMALL_FONT_PX),
                       ("TkSmallCaptionFont", SMALL_FONT_PX), ("TkIconFont", BASE_FONT_PX)):
        named = tkfont.nametofont(name, root=root)
        named.configure(size=-px(size))
        if family:
            named.configure(family=family)
    tkfont.nametofont("TkHeadingFont", root=root).configure(weight="bold")
    fixed_font = tkfont.nametofont("TkFixedFont", root=root)
    fixed_font.configure(size=-px(BASE_FONT_PX))
    if fixed:
        fixed_font.configure(family=fixed)
    actual = tkfont.nametofont("TkDefaultFont", root=root).actual()
    # Created through Tcl: a tkinter Font object deletes its font when collected.
    root.tk.call("font", "create", DISPLAY_FONT, "-family", actual["family"],
                 "-size", -px(DISPLAY_FONT_PX))


def _configure_classic_widgets(root):
    """The widgets ttk does not cover: menus, combobox lists, Tk's own Linux dialogs."""
    for pattern, value in (("*Menu.background", SURFACE), ("*Menu.foreground", INK),
                           ("*Menu.activeBackground", ACCENT),
                           ("*Menu.activeForeground", SURFACE),
                           ("*Menu.relief", "flat"), ("*Menu.borderWidth", 1),
                           ("*Menu.activeBorderWidth", 0),
                           ("*Listbox.background", SURFACE), ("*Listbox.foreground", INK),
                           ("*Listbox.selectBackground", ACCENT_SOFT),
                           ("*Listbox.selectForeground", INK), ("*Listbox.relief", "flat"),
                           ("*Listbox.highlightThickness", 0),
                           ("*Canvas.background", SURFACE), ("*Text.background", SURFACE),
                           ("*Text.foreground", INK)):
        root.option_add(pattern, value)


def _configure_styles(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=SURFACE, foreground=INK, bordercolor=BORDER,
                    lightcolor=SURFACE, darkcolor=SURFACE, troughcolor=SUNKEN,
                    focuscolor=SURFACE, selectbackground=ACCENT_SOFT, selectforeground=INK,
                    insertcolor=INK, font="TkDefaultFont")
    style.map(".", foreground=[("disabled", INK_3)])
    style.configure("Muted.TLabel", foreground=INK_2)
    style.configure("Small.TLabel", foreground=INK_2, font="TkSmallCaptionFont")
    style.configure("Heading.TLabel", foreground=INK, font="TkHeadingFont")
    style.configure("Display.TLabel", foreground=INK, font=DISPLAY_FONT)
    style.configure("Divider.TFrame", background=BORDER)
    style.configure("Track.TFrame", background=SUNKEN)
    _configure_buttons(style)
    _configure_fields(style)
    _configure_indicators(style, root)
    _configure_segments(style)
    _configure_tree(style, root)
    _configure_scrollbars(style)
    _configure_panes(style)


def _flat_button(style, name, normal, hover, pressed, foreground, border, padding):
    """A button whose whole face is one colour, with clam's bevel painted over."""
    # Clam only draws the border with a relief; the light and dark edges hide its bevel.
    style.configure(name, background=normal, foreground=foreground, bordercolor=border,
                    lightcolor=normal, darkcolor=normal, relief="raised", padding=padding,
                    anchor="center", focuscolor=normal, shiftrelief=0, width=0)
    states = [("disabled", SURFACE), ("pressed", pressed), ("active", hover)]
    style.map(name, background=states, lightcolor=states, darkcolor=states,
              focuscolor=states,
              foreground=[("disabled", INK_3)],
              bordercolor=[("disabled", BORDER), ("focus", ACCENT)])


def _configure_buttons(style):
    padding = (px(10), px(5))
    _flat_button(style, "TButton", SURFACE, SUNKEN, BORDER, INK, BORDER_STRONG, padding)
    # Tk's own file dialog on Linux uses one of these for its folder list.
    _flat_button(style, "TMenubutton", SURFACE, SUNKEN, BORDER, INK, BORDER_STRONG, padding)
    style.configure("TMenubutton", arrowcolor=INK_2)
    _flat_button(style, "Accent.TButton", ACCENT, ACCENT_HOVER, ACCENT_HOVER, SURFACE, ACCENT,
                 padding)
    style.map("Accent.TButton", foreground=[("disabled", INK_3)],
              bordercolor=[("disabled", BORDER), ("focus", INK)])
    _flat_button(style, "Ghost.TButton", SURFACE, SUNKEN, BORDER, INK_2, SURFACE,
                 (px(6), px(2)))
    style.map("Ghost.TButton", foreground=[("disabled", INK_3), ("active", INK)],
              bordercolor=[("focus", ACCENT), ("active", SUNKEN)])


def _configure_fields(style):
    for name in ("TEntry", "TCombobox", "TSpinbox"):
        style.configure(name, fieldbackground=SURFACE, background=SURFACE, foreground=INK,
                        bordercolor=BORDER_STRONG, lightcolor=SURFACE, darkcolor=SURFACE,
                        padding=(px(5), px(3)), arrowcolor=INK_2, arrowsize=px(12),
                        insertcolor=INK)
        style.map(name,
                  bordercolor=[("focus", ACCENT), ("hover", INK_3)],
                  lightcolor=[("focus", ACCENT)], darkcolor=[("focus", ACCENT)],
                  fieldbackground=[("disabled", SUNKEN), ("readonly", SURFACE)],
                  background=[("active", SUNKEN), ("pressed", BORDER)],
                  foreground=[("disabled", INK_3)],
                  selectbackground=[("readonly", SURFACE), ("!readonly", ACCENT_SOFT)],
                  selectforeground=[("readonly", INK), ("!readonly", INK)],
                  arrowcolor=[("disabled", INK_3)])


def _indicator_image(root, draw):
    """An indicator with its gap to the label, smoothed. `draw(canvas, size)` paints it."""
    size = px(INDICATOR_PX) * SUPERSAMPLE
    gap = px(INDICATOR_GAP_PX) * SUPERSAMPLE
    image = Image.new("RGBA", (size + gap, size), (0, 0, 0, 0))
    draw(ImageDraw.Draw(image), size)
    small = image.resize((image.width // SUPERSAMPLE, image.height // SUPERSAMPLE), Image.LANCZOS)
    photo = ImageTk.PhotoImage(small, master=root)
    # ttk keeps only the name, and the image vanishes with the last Python reference.
    root.theme_images.append(photo)
    return photo


def _tick_box(fill, edge, tick=False):
    def draw(canvas, size):
        line = SUPERSAMPLE
        canvas.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 5, fill=fill,
                                 outline=edge, width=line)
        if tick:
            canvas.line([(size * 0.24, size * 0.53), (size * 0.43, size * 0.72),
                         (size * 0.77, size * 0.29)], fill=SURFACE, width=int(size * 0.14),
                        joint="curve")
    return draw


def _radio_dot(fill, edge, dot=False):
    def draw(canvas, size):
        canvas.ellipse((0, 0, size - 1, size - 1), fill=fill, outline=edge, width=SUPERSAMPLE)
        if dot:
            inset = size * 0.3
            canvas.ellipse((inset, inset, size - inset, size - inset), fill=SURFACE)
    return draw


def _indicator_element(style, root, element, shape):
    """Clam's own tick is an X, which reads as "off", so these are drawn here."""
    image = lambda *look: _indicator_image(root, shape(*look))  # noqa: E731
    style.element_create(element, "image", image(SURFACE, BORDER_STRONG),
                         ("disabled", "selected", image(BORDER_STRONG, BORDER_STRONG, True)),
                         ("disabled", image(SUNKEN, BORDER)),
                         ("selected", "active", image(ACCENT_HOVER, ACCENT_HOVER, True)),
                         ("selected", image(ACCENT, ACCENT, True)),
                         ("active", image(SURFACE, ACCENT)))


def _configure_indicators(style, root):
    root.theme_images = []
    for name, kind, shape in (("TCheckbutton", "Checkbutton", _tick_box),
                              ("TRadiobutton", "Radiobutton", _radio_dot)):
        element = f"Drawn.{kind}.indicator"
        _indicator_element(style, root, element, shape)
        style.layout(name, [(f"{kind}.padding", {"sticky": "nswe", "children": [
            (element, {"side": "left", "sticky": ""}),
            (f"{kind}.label", {"side": "left", "sticky": "w"})]})])
        style.configure(name, padding=(0, px(2)))
        style.map(name, background=[("active", SURFACE)])
    style.configure("Row.TCheckbutton", padding=(px(2), px(2)))
    style.map("Row.TCheckbutton", background=[("active", SUNKEN)])


def _configure_segments(style):
    """Radio buttons drawn as a segmented control, on a Track.TFrame."""
    name = "Segment.Toolbutton"
    style.configure(name, background=SUNKEN, foreground=INK_2, bordercolor=SUNKEN,
                    lightcolor=SUNKEN, darkcolor=SUNKEN, relief="raised",
                    padding=(px(10), px(3)), anchor="center", focuscolor=SUNKEN)
    faces = [("selected", SURFACE), ("active", BORDER)]
    style.map(name, background=faces, lightcolor=faces, darkcolor=faces, focuscolor=faces,
              bordercolor=[("selected", BORDER_STRONG), ("active", BORDER)],
              foreground=[("selected", ACCENT), ("active", INK)])
    toggle = "Toggle.Toolbutton"
    style.configure(toggle, background=SURFACE, foreground=INK, bordercolor=BORDER_STRONG,
                    lightcolor=SURFACE, darkcolor=SURFACE, relief="raised",
                    padding=(px(10), px(5)), anchor="center", focuscolor=SURFACE)
    faces = [("selected", ACCENT_SOFT), ("active", SUNKEN)]
    style.map(toggle, background=faces, lightcolor=faces, darkcolor=faces, focuscolor=faces,
              bordercolor=[("selected", ACCENT)], foreground=[("selected", ACCENT)])
    style.configure("Plot.Toggle.Toolbutton", padding=(px(6), px(2)), bordercolor=SURFACE)


def _configure_tree(style, root):
    line = tkfont.nametofont("TkDefaultFont", root=root).metrics("linespace")
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=INK,
                    borderwidth=0, rowheight=line + px(7), indent=px(14))
    style.map("Treeview", background=[("selected", ACCENT_SOFT)],
              foreground=[("selected", INK)])
    # Without the border, and without the dotted focus box on the active row.
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    style.layout("Item", [("Treeitem.padding", {"sticky": "nswe", "children": [
        ("Treeitem.indicator", {"side": "left", "sticky": ""}),
        ("Treeitem.image", {"side": "left", "sticky": ""}),
        ("Treeitem.text", {"side": "left", "sticky": ""})]})])


def _configure_scrollbars(style):
    """A slim thumb with no arrows."""
    for orient, sticky in (("Vertical", "ns"), ("Horizontal", "ew")):
        name = f"{orient}.TScrollbar"
        style.layout(name, [(f"{orient}.Scrollbar.trough", {"sticky": sticky, "children": [
            (f"{orient}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
        style.configure(name, background=BORDER_STRONG, troughcolor=SURFACE,
                        bordercolor=SURFACE, lightcolor=BORDER_STRONG, darkcolor=BORDER_STRONG,
                        arrowsize=px(9), gripcount=0, relief="flat")
        style.map(name, background=[("active", INK_3)], lightcolor=[("active", INK_3)],
                  darkcolor=[("active", INK_3)])


def _configure_panes(style):
    style.configure("TPanedwindow", background=BORDER)
    style.configure("Sash", sashthickness=px(3), gripcount=0, background=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, bordercolor=BORDER, sashrelief="flat")


def _unbind_wheel_from_value_widgets(root):
    """Scrolling a settings list must not change the values it passes under the pointer."""
    for widget_class in ("TCombobox", "TSpinbox"):
        for sequence in root.bind_class(widget_class):
            if "Wheel" in sequence or "TouchpadScroll" in sequence or sequence in (
                    "<Button-4>", "<Button-5>"):
                root.unbind_class(widget_class, sequence)


def _set_icon(root):
    """Replace Tk's feather, which otherwise marks the window on Windows and Linux."""
    icon = tk.PhotoImage(master=root, width=ICON_SIZE, height=ICON_SIZE)
    icon.put(ACCENT, to=(0, 0, ICON_SIZE, ICON_SIZE))
    for (x0, y0), (x1, y1) in zip(ICON_TRACE, ICON_TRACE[1:]):
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for step in range(steps + 1):
            x = x0 + (x1 - x0) * step // steps
            y = y0 + (y1 - y0) * step // steps
            icon.put(SURFACE, to=(x, y, x + 2, y + 2))
    root.iconphoto(True, icon)
    # Tk does not hold a reference to the image; losing it would blank the icon.
    root.app_icon = icon
