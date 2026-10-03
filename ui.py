import tkinter as tk

# ---------- colours and fonts ----------
BG = "#ffffff"
SURFACE = "#f6f7f9"
TINT = "#ecfdf5"
SKY = "#ecfdf5"
BORDER = "#e5e7eb"
TEXT = "#111827"
MUTED = "#6b7280"
ACCENT = "#059669"
ACCENT_HOVER = "#047857"
RED = "#dc2626"
FONT = "Segoe UI"

# button kinds: (normal colour, hover colour, text colour)
BUTTON_STYLES = {
    "primary": (ACCENT, ACCENT_HOVER, "white"),
    "secondary": ("#eef0f3", "#e2e5ea", TEXT),
    "danger": (RED, "#b91c1c", "white"),
}

APP = None  # the main window, app.py sets this when the program starts


# ---------- pixel art money (used by the loading animation) ----------
# each letter is one pixel: D = dark green, G = green, L = light green
BILL = [
    "DDDDDDDDDDDDDD",
    "DGGGGGGGGGGGGD",
    "DGGGLLLLLLGGGD",
    "DGGLLLDDLLLGGD",
    "DGGLLLDDLLLGGD",
    "DGGGLLLLLLGGGD",
    "DGGGGGGGGGGGGD",
    "DDDDDDDDDDDDDD",
]
PALETTE = {"D": "#047857", "G": "#34d399", "L": "#a7f3d0"}

# wing pixels (x, y) next to the note, one set for wings up, one for wings down
WING_UP = [(-1, 0), (-2, -1), (-2, 0), (-3, -2), (-3, -1), (-3, 0)]
WING_DOWN = [(-1, 0), (-2, 1), (-2, 0), (-3, 2), (-3, 1), (-3, 0)]
WING_COLOR = "#cbd5e1"


def build_runs(rows):
    # joins pixels of the same colour in a row into one rectangle (faster to draw)
    runs = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch = row[x]
            start = x
            while x < len(row) and row[x] == ch:
                x += 1
            runs.append((start, y, x - start, ch))
    return runs


BILL_RUNS = build_runs(BILL)


def draw_bill(canvas, x, y, flap_up, size=6):
    for cx, cy, w, ch in BILL_RUNS:
        canvas.create_rectangle(x + cx * size, y + cy * size,
                                x + (cx + w) * size, y + (cy + 1) * size,
                                fill=PALETTE[ch], outline="")
    wing = WING_UP if flap_up else WING_DOWN
    for dx, dy in wing:
        gy = 3 + dy
        for gx in (dx, 13 - dx):  # left wing and right wing
            canvas.create_rectangle(x + gx * size, y + gy * size,
                                    x + (gx + 1) * size, y + (gy + 1) * size,
                                    fill=WING_COLOR, outline="")


def brand_mark(parent, bg):
    canvas = tk.Canvas(parent, width=130, height=60, bg=bg, highlightthickness=0)
    draw_bill(canvas, 23, 6, True, 6)
    return canvas


# ---------- pixel art bank (background of the home page) ----------
def block(canvas, ox, oy, s, x, y, w, h, color):
    # draws one rectangle made of "pixels"; x, y, w, h are counted in pixels
    canvas.create_rectangle(ox + x * s, oy + y * s, ox + (x + w) * s,
                            oy + (y + h) * s, fill=color, outline="", tags="scene")


def draw_scene(canvas, w, h):
    canvas.delete("scene")
    s = max(6, min(w // 90, h // 48))  # size of one pixel
    ground = 3 * s

    # sun and clouds
    block(canvas, w - 14 * s, 2 * s, s, 1, 0, 4, 6, "#fde68a")
    block(canvas, w - 14 * s, 2 * s, s, 0, 1, 6, 4, "#fde68a")
    for cx, cy in ((0.50, 3), (0.74, 7), (0.30, 11)):
        ox = int(w * cx)
        oy = cy * s
        block(canvas, ox, oy, s, 2, 0, 4, 1, "white")
        block(canvas, ox, oy, s, 0, 1, 8, 2, "white")
        block(canvas, ox, oy, s, 1, 3, 6, 1, "white")

    # ground
    canvas.create_rectangle(0, h - ground, w, h, fill="#bbf7d0", outline="",
                            tags="scene")
    canvas.create_rectangle(0, h - ground, w, h - ground + s // 2 + 1,
                            fill="#86efac", outline="", tags="scene")

    # the bank (46 x 31 pixels), sitting on the ground at the right side
    ox = w - 46 * s - 6 * s
    oy = h - ground - 31 * s
    green, dark, wall, shade = "#6ee7b7", "#34d399", "white", "#d1fae5"

    for r in range(8):  # triangle roof
        half = 2 + 2 * r
        block(canvas, ox, oy, s, 23 - half, r, 2 * half, 1, dark if r == 0 else green)
    block(canvas, ox, oy, s, 21, 3, 4, 4, "#fcd34d")  # coin on the roof
    block(canvas, ox, oy, s, 22, 4, 2, 2, "#f59e0b")

    block(canvas, ox, oy, s, 4, 8, 38, 1, dark)       # bar under the roof
    block(canvas, ox, oy, s, 4, 9, 38, 2, green)
    canvas.create_text(ox + 23 * s, oy + 9.5 * s, text="AR BANK", fill="white",
                       font=("Consolas", -int(2 * s), "bold"), tags="scene")

    block(canvas, ox, oy, s, 5, 11, 36, 14, shade)    # wall behind the columns
    for x in (5, 11, 17, 26, 32, 38):                 # six columns
        block(canvas, ox, oy, s, x, 11, 3, 14, wall)
        block(canvas, ox, oy, s, x + 2, 11, 1, 14, "#e5e7eb")
    block(canvas, ox, oy, s, 21, 17, 4, 8, dark)      # door
    block(canvas, ox, oy, s, 24, 20, 1, 1, "#fcd34d")

    block(canvas, ox, oy, s, 3, 25, 40, 2, "#a7f3d0")  # three steps
    block(canvas, ox, oy, s, 1, 27, 44, 2, "#6ee7b7")
    block(canvas, ox, oy, s, 0, 29, 46, 2, "#34d399")

    # two bushes
    for bx in (ox - 9 * s, ox - 18 * s):
        by = h - ground - 5 * s
        block(canvas, bx, by, s, 0, 2, 7, 3, "#34d399")
        block(canvas, bx, by, s, 1, 1, 5, 1, "#34d399")
        block(canvas, bx, by, s, 2, 0, 3, 1, "#34d399")

    canvas.tag_lower("scene")  # keep the art behind the text and buttons


# ---------- widgets ----------
def with_loading(command):
    # every button runs the animation first, then does its real job
    def wrapper():
        APP.run_with_loading(command)
    return wrapper


def make_button(parent, text, command, kind="primary"):
    color, hover, fg = BUTTON_STYLES[kind]
    btn = tk.Button(parent, text=text, command=with_loading(command), bg=color,
                    fg=fg, font=(FONT, 11, "bold"), relief="flat", bd=0,
                    activebackground=hover, activeforeground=fg,
                    cursor="hand2", padx=22, pady=10)
    # colour change when the mouse moves over the button
    btn.bind("<Enter>", lambda e: btn.config(bg=hover))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def make_entry(parent, show=None):
    return tk.Entry(parent, font=(FONT, 12), bg="white", fg=TEXT,
                    insertbackground=TEXT, relief="flat", show=show, width=36,
                    highlightthickness=1, highlightbackground=BORDER,
                    highlightcolor=ACCENT)