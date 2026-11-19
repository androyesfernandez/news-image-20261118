#!/usr/bin/env python3
"""make.fun news-image-20261118 entry, round 3.

Writes one 1024x1024 PNG summing up the world news of Wednesday
18 November 2026 to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).

Design: a complete newspaper front page on one square canvas.
A navy masthead with a giant date, a colour-coded region strip with
story counts, a UTC timeline of the day, three illustrated lead
stories, eight more illustrated stories in two rows, a dotted world
map with numbered pins, 35 numbered one-line briefs, a red DATE
CHECK box naming what was left out and why, and a sources footer.

Every story below was reported on Wednesday 18 November 2026; the
DATE CHECK box lists the tempting stories that were NOT that day's
news (first reported Tuesday 17 November, or still to come) and so
are excluded. Claims are attributed to their makers.

Pure Python standard library, fully deterministic: no clock, no
random, no network, no file input. Two runs write identical bytes.
"""

import os
import struct
import zlib
from math import isqrt

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 233)
WHITE = (255, 254, 248)
INK = (18, 22, 28)
GRAY = (70, 76, 86)
FAINT = (203, 196, 178)
RED = (178, 32, 40)
NAVY = (16, 42, 84)
BLUE = (26, 72, 128)
TEAL = (14, 110, 104)
GOLD = (196, 138, 30)
GREEN = (38, 110, 58)
YELLOW = (250, 210, 60)
PURPLE = (96, 52, 140)
ORANGE = (198, 96, 26)
SKY = (168, 200, 232)
DEEP = (10, 16, 40)

_buf = bytearray(W * H * 3)


def _set_row(x, y, w, rgb):
    i = (y * W + x) * 3
    _buf[i:i + 3 * w] = bytes(rgb) * w


def rect(x, y, w, h, rgb):
    if w <= 0 or h <= 0:
        return
    x0 = max(0, x)
    x1 = min(W, x + w)
    if x1 <= x0:
        return
    for yy in range(max(0, y), min(H, y + h)):
        _set_row(x0, yy, x1 - x0, rgb)


def outline(x, y, w, h, rgb, t=3):
    rect(x, y, w, t, rgb)
    rect(x, y + h - t, w, t, rgb)
    rect(x, y, t, h, rgb)
    rect(x + w - t, y, t, h, rgb)


def circle(cx, cy, r, rgb):
    for dy in range(-r, r + 1):
        dx = isqrt(r * r - dy * dy)
        _set_row(cx - dx, cy + dy, 2 * dx + 1, rgb)


def line(x0, y0, x1, y1, rgb, t=3):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    half = t // 2
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i // steps
        y = y0 + (y1 - y0) * i // steps
        rect(x - half, y - half, t, t, rgb)


# ------------------------------------------------------------------- font
# 5x7 bitmap font. '#' = ink pixel.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", ".#.#.", "..#..", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"),
    '2': (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    '3': (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "'": (".##..", ".##..", ".#...", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#..##", "#..##"),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", "...#."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '*': (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    '€': (".###.", "#....", "#####", "#....", "#####", "#....", ".###."),
    '£': (".###.", "#..#.", "#....", "#####", "#....", "#....", "#####"),
    '×': (".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "....."),
    '°': (".##..", "#..#.", ".##..", ".....", ".....", ".....", "....."),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale if s else 0


def text(x, y, s, scale, rgb):
    """Draw string s with top-left at (x, y); returns its pixel width."""
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[' '])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == '#':
                    rect(x + gx * scale, y + gy * scale, scale, scale, rgb)
        x += 6 * scale
    return text_w(s, scale)


def text_c(cx, y, s, scale, rgb):
    return text(cx - text_w(s, scale) // 2, y, s, scale, rgb)


def wrap(s, scale, max_w):
    """Greedy word wrap: list of lines that fit max_w pixels."""
    words = s.split()
    lines = []
    cur = ""
    for wd in words:
        trial = (cur + " " + wd) if cur else wd
        if text_w(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ scenes
# Flat vector-style illustration panels. Each paints inside (x, y, w, h).

def scene_summit(x, y, w, h):
    """Shenzhen skyline, a landing plane, China / US / Russia flags."""
    rect(x, y, w, h, SKY)
    rect(x, y + h - 18, w, 18, NAVY)
    for bx, bh in ((6, 26), (30, 38), (58, 22), (84, 44), (118, 30),
                   (150, 40), (182, 24), (214, 34), (246, 20)):
        if bx < w - 18:
            rect(x + bx, y + h - 18 - bh, 20, bh, NAVY)
    circle(x + w - 42, y + 26, 14, YELLOW)
    # plane silhouette descending left to right
    px, py = x + 62, y + 28
    line(px - 40, py + 14, px + 36, py - 8, INK, 8)
    line(px + 6, py - 2, px - 10, py - 20, INK, 7)
    line(px - 30, py + 12, px - 44, py - 2, INK, 7)
    line(px - 34, py + 13, px - 46, py + 24, INK, 6)
    # flags on the ground line: CN, US, RU
    fy = y + h - 18
    for i, fx in enumerate((x + 18, x + 58, x + 98)):
        rect(fx, fy - 34, 3, 34, INK)
        if i == 0:
            rect(fx + 3, fy - 34, 30, 20, RED)
            rect(fx + 7, fy - 30, 5, 5, YELLOW)
            rect(fx + 15, fy - 31, 3, 3, YELLOW)
            rect(fx + 15, fy - 25, 3, 3, YELLOW)
        elif i == 1:
            rect(fx + 3, fy - 34, 30, 20, WHITE)
            for s in range(3):
                rect(fx + 3, fy - 32 + s * 6, 30, 3, RED)
            rect(fx + 3, fy - 34, 13, 10, BLUE)
        else:
            rect(fx + 3, fy - 34, 30, 7, WHITE)
            rect(fx + 3, fy - 27, 30, 7, BLUE)
            rect(fx + 3, fy - 20, 30, 6, RED)
        outline(fx + 3, fy - 34, 30, 20, INK, 1)


def scene_gulf(x, y, w, h):
    """Gulf map: sand land, blue sea, a drone and an interception."""
    rect(x, y, w, h, BLUE)
    rect(x, y, w * 2 // 5, h, (232, 205, 150))
    line(x + w * 2 // 5, y, x + w // 3, y + h, (232, 205, 150), 10)
    rect(x, y + h - 30, w // 4, 30, (232, 205, 150))
    text(x + 44, y + 12, "IRAN", 3, INK)
    text(x + w - 92, y + h - 30, "ARABIA", 2, WHITE)
    # drone: X quadcopter with a body
    cx, cy = x + w * 3 // 5, y + h // 3
    line(cx - 26, cy - 16, cx + 26, cy + 16, INK, 5)
    line(cx - 26, cy + 16, cx + 26, cy - 16, INK, 5)
    for dx, dy in ((-26, -16), (26, -16), (-26, 16), (26, 16)):
        circle(cx + dx, cy + dy, 6, INK)
    rect(cx - 9, cy - 6, 18, 12, RED)
    # interception burst low left of the drone
    bx, by = cx - 74, cy + 52
    for dx, dy in ((20, 0), (-20, 0), (0, 20), (0, -20),
                   (14, 14), (14, -14), (-14, 14), (-14, -14)):
        line(bx, by, bx + dx, by + dy, GOLD, 5)
    circle(bx, by, 7, RED)


def scene_voyager(x, y, w, h):
    """Deep space: Earth, the probe, and a signal that takes a day."""
    rect(x, y, w, h, DEEP)
    for sx, sy in ((20, 18), (70, 40), (130, 14), (190, 52), (250, 22),
                   (36, 84), (96, 66), (160, 92), (226, 84), (268, 60),
                   (52, 30), (210, 36)):
        if sx < w - 6 and sy < h - 6:
            rect(x + sx, y + sy, 3, 3, YELLOW)
    circle(x + 44, y + h - 44, 24, BLUE)
    circle(x + 36, y + h - 52, 8, GREEN)
    circle(x + 52, y + h - 34, 6, GREEN)
    # probe: gold bus, panels, big dish
    px, py = x + w - 84, y + 52
    rect(px - 34, py - 8, 18, 16, BLUE)
    rect(px + 16, py - 8, 18, 16, BLUE)
    rect(px - 11, py - 7, 22, 14, GOLD)
    circle(px, py - 24, 12, WHITE)
    circle(px, py - 24, 4, DEEP)
    line(px, py - 12, px, py - 7, INK, 3)
    # signal arcs from Earth toward the probe
    for r in (34, 52, 70):
        for a in range(-40, 41, 10):
            import math
            dx = int(r * math.cos(a * 3.14159 / 180))
            dy = int(r * math.sin(a * 3.14159 / 180))
            rect(x + 44 + dx, y + h - 44 - dy, 3, 3, TEAL)


def scene_drones(x, y, w, h):
    """Night sky full of drones over a city silhouette."""
    rect(x, y, w, h, NAVY)
    rect(x, y + h - 16, w, 16, INK)
    for bx, bh in ((4, 26), (34, 36), (66, 22), (96, 32), (128, 24),
                   (158, 38), (190, 26)):
        if bx < w - 14:
            rect(x + bx, y + h - 16 - bh, 16, bh, INK)
            rect(x + bx + 4, y + h - 16 - bh + 6, 3, 3, YELLOW)
    for dx, dy, s in ((30, 24, 1), (76, 40, 1), (120, 20, 1),
                      (164, 44, 1), (208, 26, 1), (58, 58, 1),
                      (146, 62, 1), (196, 66, 1)):
        if dx < w - 16:
            line(x + dx - 8, y + dy - 5, x + dx + 8, y + dy + 5, RED, 3)
            line(x + dx - 8, y + dy + 5, x + dx + 8, y + dy - 5, RED, 3)
            rect(x + dx - 3, y + dy - 2, 6, 4, YELLOW)


def scene_eu(x, y, w, h):
    """EU blue: the loan figure in gold, a row of twelve stars."""
    rect(x, y, w, h, BLUE)
    text_c(x + w // 2 + 14, y + h // 2 - 21, "€45BN", 6, GOLD)
    for i in range(12):
        sx = x + 14 + i * (w - 28) // 11
        rect(sx - 2, y + h - 12, 5, 5, YELLOW)


def scene_fed(x, y, w, h):
    """A marble central-bank facade and a falling red market line."""
    rect(x, y, w, h, (226, 224, 216))
    rect(x + 10, y + h - 14, w - 20, 6, INK)
    rect(x + 16, y + 18, w - 32, 8, INK)
    for i in range(5):
        cxp = x + 24 + i * (w - 48) // 4
        rect(cxp, y + 26, 7, h - 46, INK)
    rect(x + 10, y + 8, w - 20, 8, INK)
    line(x + 14, y + h - 34, x + w // 3, y + h - 44, RED, 4)
    line(x + w // 3, y + h - 44, x + w // 2, y + h - 38, RED, 4)
    line(x + w // 2, y + h - 38, x + w - 30, y + h - 20, RED, 4)
    line(x + w - 30, y + h - 20, x + w - 44, y + h - 21, RED, 4)
    line(x + w - 30, y + h - 20, x + w - 29, y + h - 34, RED, 4)


def scene_cyclone(x, y, w, h):
    """A cyclone spiral over teal sea, bearing on a coast."""
    rect(x, y, w, h, TEAL)
    rect(x + w - 34, y, 34, h, (232, 205, 150))
    line(x + w - 34, y, x + w - 44, y + h, (232, 205, 150), 8)
    import math
    cx, cy = x + w // 2 - 8, y + h // 2 + 2
    for r in (36, 26, 17, 9):
        for a in range(0, 360, 12):
            px = cx + int(r * math.cos(a * 3.14159 / 180))
            py = cy + int(r * math.sin(a * 3.14159 / 180) * 0.72)
            rect(px - 3, py - 3, 6, 6, WHITE)
    circle(cx, cy, 6, NAVY)
    text(x + w - 40, y + 8, "INDIA", 1, INK)


def scene_sudan(x, y, w, h):
    """Sand, a town grid, and a drone overhead (story attributed)."""
    rect(x, y, w, h, (232, 205, 150))
    for bx, by in ((16, h - 16), (44, h - 12), (72, h - 18), (102, h - 12),
                   (132, h - 17), (162, h - 12), (190, h - 16), (216, h - 12)):
        if bx < w - 16:
            rect(x + bx, y + by, 14, 10, (178, 142, 92))
    cx, cy = x + w // 2, y + 26
    line(cx - 22, cy - 12, cx + 22, cy + 12, INK, 4)
    line(cx - 22, cy + 12, cx + 22, cy - 12, INK, 4)
    for dx, dy in ((-22, -12), (22, -12), (-22, 12), (22, 12)):
        circle(cx + dx, cy + dy, 5, INK)
    rect(cx - 7, cy - 4, 14, 8, RED)


def scene_gaza(x, y, w, h):
    """City blocks, a tank, and the Yellow Line."""
    rect(x, y, w, h, (214, 208, 192))
    for bx, by, bh in ((8, 12, 18), (34, 8, 24), (62, 14, 16),
                       (150, 10, 22), (178, 14, 16), (204, 8, 24)):
        if bx < w - 20:
            rect(x + bx, y + by, 20, bh, GRAY)
            rect(x + bx + 4, y + by + 5, 4, 4, PAPER)
            rect(x + bx + 12, y + by + 11, 4, 4, PAPER)
    rect(x, y + h - 12, w, 12, (160, 150, 128))
    # tank silhouette
    tx, ty = x + 88, y + h - 30
    rect(tx, ty, 52, 12, INK)
    rect(tx + 12, ty - 9, 26, 9, INK)
    line(tx + 34, ty - 6, tx + 66, ty - 12, INK, 5)
    circle(tx + 10, ty + 13, 6, INK)
    circle(tx + 26, ty + 13, 6, INK)
    circle(tx + 42, ty + 13, 6, INK)
    # the Yellow Line: a dashed yellow band up the right side
    for yy in range(y + 6, y + h - 18, 16):
        rect(x + w - 18, yy, 7, 9, YELLOW)


def scene_capitol(x, y, w, h):
    """The US Capitol: dome, wings, steps."""
    rect(x, y, w, h, SKY)
    rect(x, y + h - 10, w, 10, (120, 128, 110))
    cx = x + w // 2
    rect(cx - 70, y + h - 28, 140, 18, WHITE)
    outline(cx - 70, y + h - 28, 140, 18, INK, 1)
    rect(cx - 22, y + h - 40, 44, 12, WHITE)
    outline(cx - 22, y + h - 40, 44, 12, INK, 1)
    for r in range(10):
        rect(cx - 15 + r // 2, y + h - 40 - 10 + r, 30 - r, 1, WHITE)
    rect(cx - 1, y + h - 54, 3, 6, INK)
    circle(cx, y + h - 56, 3, GOLD)
    for i in range(6):
        rect(cx - 60 + i * 22, y + h - 24, 4, 10, INK)


def scene_gta(x, y, w, h):
    """Vice City night: purple sky, palms, a game controller."""
    rect(x, y, w, h, PURPLE)
    rect(x, y + h - 18, w, 18, DEEP)
    circle(x + 30, y + 24, 11, YELLOW)
    for px in (x + 24, x + w - 30):
        line(px, y + h - 18, px + 3, y + h - 52, INK, 5)
        for a in (-38, -14, 12, 36):
            import math
            ex = px + 3 + int(22 * math.sin(a * 3.14159 / 180))
            ey = y + h - 52 - int(12 * math.cos(a * 3.14159 / 180))
            line(px + 3, y + h - 52, ex, ey, GREEN, 4)
    # controller
    cx, cy = x + w // 2, y + h // 2 + 6
    rect(cx - 44, cy - 16, 88, 34, INK)
    circle(cx - 44, cy + 1, 17, INK)
    circle(cx + 44, cy + 1, 17, INK)
    rect(cx - 28, cy - 3, 16, 6, WHITE)
    rect(cx - 23, cy - 8, 6, 16, WHITE)
    circle(cx + 22, cy - 6, 4, RED)
    circle(cx + 32, cy + 3, 4, YELLOW)
    circle(cx + 12, cy + 3, 4, TEAL)


def badge(n, x, y, rgb=RED):
    """Numbered story badge: filled circle, white number."""
    circle(x + 13, y + 13, 13, rgb)
    s = str(n)
    text(x + 13 - text_w(s, 2) // 2, y + 6, s, 2, WHITE)


# ---------------------------------------------------------------- world map
# Dotted world map on an 84 x 38 grid (col ~ longitude, row ~ latitude).
# Land is a list of (row, first col, last col) spans.

LAND = [
    (1, 2, 8), (1, 13, 21), (1, 33, 37), (1, 54, 82),
    (2, 1, 9), (2, 12, 26), (2, 31, 37), (2, 48, 52), (2, 53, 83),
    (3, 2, 8), (3, 12, 27), (3, 33, 36), (3, 47, 52), (3, 53, 83),
    (4, 3, 7), (4, 11, 28), (4, 43, 44), (4, 48, 83),
    (5, 4, 7), (5, 10, 27), (5, 43, 45), (5, 48, 52), (5, 53, 82),
    (6, 11, 27), (6, 45, 56), (6, 57, 80),
    (7, 12, 26), (7, 44, 57), (7, 61, 79),
    (8, 12, 26), (8, 43, 58), (8, 59, 76),
    (9, 12, 27), (9, 44, 52), (9, 53, 58), (9, 60, 77),
    (10, 12, 27), (10, 43, 47), (10, 50, 52), (10, 53, 56),
    (10, 57, 62), (10, 63, 70), (10, 68, 77),
    (11, 12, 26), (11, 54, 58), (11, 59, 63), (11, 64, 68),
    (11, 68, 78),
    (12, 13, 26), (12, 44, 56), (12, 57, 62), (12, 60, 67),
    (12, 66, 70), (12, 70, 77),
    (13, 14, 25), (13, 43, 58), (13, 57, 63), (13, 65, 71),
    (13, 71, 76),
    (14, 13, 18), (14, 42, 59), (14, 58, 63), (14, 66, 71),
    (14, 72, 76),
    (15, 15, 17), (15, 42, 60), (15, 67, 70), (15, 73, 77),
    (16, 14, 17), (16, 43, 60), (16, 67, 69), (16, 73, 77),
    (16, 78, 79),
    (17, 21, 27), (17, 44, 59), (17, 60, 61), (17, 67, 69),
    (17, 74, 77),
    (18, 21, 29), (18, 45, 58), (18, 59, 61), (18, 74, 76),
    (18, 78, 80),
    (19, 21, 30), (19, 45, 57), (19, 72, 74), (19, 76, 79),
    (19, 81, 82),
    (20, 22, 30), (20, 46, 57), (20, 73, 76), (20, 78, 80),
    (20, 82, 83),
    (21, 22, 30), (21, 47, 57), (21, 74, 78), (21, 80, 82),
    (22, 23, 31), (22, 47, 56),
    (23, 23, 31), (23, 48, 56), (23, 59, 59),
    (24, 23, 30), (24, 48, 56), (24, 59, 60), (24, 76, 80),
    (25, 23, 30), (25, 49, 56), (25, 59, 60), (25, 75, 85),
    (26, 23, 29), (26, 49, 56), (26, 74, 86),
    (27, 23, 29), (27, 50, 55), (27, 74, 86),
    (28, 23, 28), (28, 50, 55), (28, 75, 85),
    (29, 22, 27), (29, 51, 54), (29, 76, 84),
    (30, 22, 26), (30, 51, 54), (30, 77, 83),
    (31, 22, 25), (31, 82, 83),
    (32, 22, 24), (32, 82, 83),
    (33, 22, 24),
    (34, 22, 23),
    (35, 22, 23),
]

# story number -> (col, row) pin on the map grid; None = off the map
PINS = {
    1: (69, 16), 2: (53, 14), 3: None, 4: (49, 8), 5: (43, 8),
    6: (24, 11), 7: (62, 16), 8: (49, 18), 9: (50, 13),
    10: (25, 12), 11: (82, 32),
}


def draw_map(x, y):
    """Dotted world map with numbered pins and brief dots."""
    text(x + 4, y, "WHERE IT HAPPENED", 2, INK)
    oy = y + 30
    for r, c0, c1 in LAND:
        for c in range(c0, c1 + 1):
            rect(x + c * 4 + 1, oy + r * 4 + 1, 2, 2, (176, 168, 148))
    for n, dot in BRIEF_DOTS.items():
        c, r = dot
        circle(x + c * 4 + 2, oy + r * 4 + 2, 2, GRAY)
    for n, pin in PINS.items():
        if pin is None:
            continue
        c, r = pin
        px, py = x + c * 4 + 2, oy + r * 4 + 2
        circle(px, py, 8, RED)
        s = str(n)
        text(px - text_w(s, 1) // 2, py - 3, s, 1, WHITE)
    text(x + 4, oy + 156, "RED NUMBERS: STORIES 1-11 * GREY DOTS: BRIEFS", 1, GRAY)
    text(x + 4, oy + 166, "3 IS IN DEEP SPACE, OFF THE MAP * APPROXIMATE", 1, GRAY)


# ------------------------------------------------------------------- cards
def lead_card(x, y, w, h, n, kicker, head, dek, src, scene, accent):
    rect(x, y, w, h, WHITE)
    outline(x, y, w, h, INK, 3)
    scene(x + 3, y + 3, w - 6, 96)
    badge(n, x + 10, y + 10, accent)
    text(x + 12, y + 107, kicker, 2, accent)
    text(x + w - 12 - text_w(src, 1), y + 111, src, 1, GRAY)
    yy = y + 128
    for ln in wrap(head, 3, w - 24)[:2]:
        text(x + 12, yy, ln, 3, INK)
        yy += 23
    yy += 4
    for ln in wrap(dek, 2, w - 24)[:2]:
        text(x + 12, yy, ln, 2, GRAY)
        yy += 16


def row_card(x, y, w, h, n, kicker, head, dek, src, scene, accent):
    rect(x, y, w, h, WHITE)
    outline(x, y, w, h, INK, 2)
    scene(x + 2, y + 2, w - 4, 54)
    badge(n, x + 6, y + 6, accent)
    text(x + 8, y + 62, kicker, 1, accent)
    yy = y + 74
    for ln in wrap(head, 2, w - 16)[:2]:
        text(x + 8, yy, ln, 2, INK)
        yy += 16
    for ln in wrap(dek, 1, w - 16)[:2]:
        text(x + 8, yy, ln, 1, GRAY)
        yy += 9
    text(x + 8, y + h - 11, src, 1, GRAY)


# -------------------------------------------------------------------- data
# Briefs: (number, place, text, map dot). Every brief was reported on
# Wednesday 18 November 2026.

BRIEFS = [
    (12, "MANILA", "QUAD LEADERS MEET, FIRST IN 2 YEARS", (70, 17)),
    (13, "TOKYO", "RUSSIAN JETS IN AIRSPACE AT FUKUOKA", (72, 12)),
    (14, "TAIPEI", "10 PLA SORTIES AND 11 SHIPS LOGGED", (70, 15)),
    (15, "PORT MORESBY", "6.0 EARTHQUAKE STRIKES", (76, 24)),
    (16, "SEOUL", "PRESIDENT LEE COURTS BEIJING AT APEC", (71, 11)),
    (17, "LONDON", "INFLATION AT 3.6%, A ONE-YEAR HIGH", (42, 8)),
    (18, "ROME", "ANTI-ANTISEMITISM LAW PASSES 147-93", (45, 10)),
    (19, "BERLIN", "FINANCIAL-LITERACY PLAN ADOPTED", (45, 7)),
    (20, "BRUSSELS", "EU TO SIGN INDONESIA TRADE PACT", (44, 9)),
    (21, "ANKARA", "EUROPEAN COURT: FREE MP ATALAY", (49, 11)),
    (22, "BUCHAREST", "5.3 EARTHQUAKE STRIKES ROMANIA", (48, 9)),
    (23, "STOCKHOLM", "ECDC: EUROPE OFF TRACK, SUPERBUGS", (46, 5)),
    (24, "GENEVA", "UKRAINE, RUSSIA SET FOR US-LED TALKS", (43, 9)),
    (25, "HORMUZ", "TANKER STRUCK; A CREW MEMBER MISSING", (55, 14)),
    (26, "ISFAHAN", "4 DIE IN ARMY HELICOPTER CRASH", (54, 13)),
    (27, "GAZA", "WHO: 950,000 DISPLACED, FLOOD-PRONE", (51, 13)),
    (28, "NEW YORK", "CITYWIDE TRAVEL BAN AS STORM HITS", (25, 10)),
    (29, "HONDURAS", "12 KILLED IN YORO; FORCES DEPLOYED", (22, 17)),
    (30, "MEXICO", "CALM URGED AFTER CARTEL LEADER DIES", (19, 16)),
    (31, "CARACAS", "WARNS US NUCLEAR PRESENCE A THREAT", (26, 19)),
    (32, "BOGOTA", "COLOMBIA ECONOMY SHRINKS 0.8% IN Q3", (25, 20)),
    (33, "N'DJAMENA", "CHAD CLOSES ITS BORDER WITH SUDAN", (45, 18)),
    (34, "ABUJA", "NIGERIA BIDS FOR UN RIGHTS SEAT", (44, 19)),
    (35, "DELHI", "INDIA URGES CITIZENS TO LEAVE IRAN", (60, 14)),
    (36, "PAKISTAN", "BUILDING BLAST TOLL RISES TO 16", (58, 15)),
    (37, "MARKETS", "GOLD AT ITS LOWEST IN OVER A YEAR", (41, 7)),
    (38, "ANKARA", "TURKEY TAKES OVER OPPOSITION STATION", (48, 11)),
    (39, "OSLO", "NORWAY KEEPS ITS THREAT LEVEL STEADY", (44, 5)),
    (40, "MANILA", "US-PHILIPPINE TRADE DEAL ANNOUNCED", (70, 18)),
    (41, "KYIV", "UKRAINE SEEKS MORE JETS, AIR DEFENCE", (48, 7)),
    (42, "BEIRUT", "GERMAN PRESIDENT TO VISIT BLAST SITE", (50, 12)),
    (43, "ENERGY", "OIL NEAR $93; HORMUZ SHIPPING STALLS", (56, 15)),
    (44, "YEMEN", "UNICEF: 64 CHILDREN KILLED SINCE SEPT", (53, 17)),
    (45, "KEREM SHALOM", "AID-TRUCK SCANNERS BEGIN WORK", (49, 14)),
    (46, "VIENNA", "NATO UNVEILS NEW COMMS STRATEGY", (46, 6)),
]

BRIEF_DOTS = {n: dot for n, _p, _t, dot in BRIEFS}

TIMELINE = [
    ("OVERNIGHT", "DRONES OVER KUWAIT + BAHRAIN + UKRAINE"),
    ("07:00", "UK INFLATION 3.6%"),
    ("MORNING", "XI GREETS TRUMP IN SHENZHEN"),
    ("MIDDAY", "VOYAGER 1: ONE LIGHT-DAY"),
    ("11:00", "GTA VI OPENS IN NEW ZEALAND"),
    ("AFTERNOON", "EU OFFERS KYIV A €45BN LOAN"),
    ("19:00", "FED MINUTES: MORE HIKES AHEAD"),
    ("21:00", "DOW CLOSES DOWN 1.1%"),
]

REGIONS = [
    ("ASIA 7", PURPLE), ("EUROPE 13", BLUE), ("AMERICAS 7", GREEN),
    ("AFRICA 3", ORANGE), ("MID EAST 10", RED), ("S ASIA 3", GOLD),
    ("GLOBAL 3", GRAY),
]


# -------------------------------------------------------------- composition
def compose():
    rect(0, 0, W, H, PAPER)
    outline(6, 6, W - 12, H - 12, INK, 3)

    # Masthead: navy band, gold furniture, the date in huge white type
    rect(10, 10, W - 20, 108, NAVY)
    text(24, 18, "THE DAY IN WORLD NEWS", 2, GOLD)
    top_r = "46 STORIES * 7 REGIONS * 11 DRAWN"
    text(W - 24 - text_w(top_r, 2), 18, top_r, 2, GOLD)
    text_c(W // 2, 40, "WEDNESDAY 18 NOVEMBER 2026", 6, WHITE)
    text_c(W // 2, 92,
           "EVERYTHING HERE HAPPENED, OR WAS FIRST REPORTED, ON THIS DAY",
           2, SKY)

    # Region strip: colour-coded counts of the stories on this page
    rx = 24
    for label, rgb in REGIONS:
        rect(rx, 126, 136, 24, rgb)
        text_c(rx + 68, 131, label, 2, WHITE)
        rx += 140

    # The day in UTC
    text(24, 158, "THE DAY IN UTC", 2, RED)
    reads = "READS AT 3 SIZES: THUMBNAIL * HALF * FULL"
    text(W - 24 - text_w(reads, 1), 162, reads, 1, GRAY)
    tx = 24
    for when, what in TIMELINE:
        text(tx, 178, when, 2, INK)
        ly = 196
        for ln in wrap(what, 1, 116)[:2]:
            text(tx, ly, ln, 1, GRAY)
            ly += 9
        tx += 122

    # Three lead stories
    lead_card(24, 216, 318, 218, 1, "SHENZHEN * APEC",
              "XI GREETS TRUMP IN SHENZHEN",
              "ON THE TARMAC; PUTIN TOO; TALKS THURSDAY",
              "AFP * AP * NPR", scene_summit, PURPLE)
    lead_card(353, 216, 318, 218, 2, "THE GULF * OVERNIGHT",
              "KUWAIT, BAHRAIN STOP IRAN DRONES",
              "DRONES AIMED AT A U.S. BASE AND GULF STATES",
              "AL JAZEERA * REUTERS", scene_gulf, RED)
    lead_card(682, 216, 318, 218, 3, "DEEP SPACE * NASA",
              "VOYAGER 1: ONE LIGHT-DAY OUT",
              "25.9BN KM FROM EARTH; SIGNALS TAKE 24 HOURS",
              "NASA * JPL", scene_voyager, BLUE)

    # Illustrated stories, row of four (4-7)
    row_card(24, 442, 238, 148, 4, "UKRAINE",
             "RUSSIA FIRES 141 DRONES; 126 DOWNED",
             "UKRAINE'S AIR FORCE COUNTED 141 BY 08:00; SIX HURT IN DNIPRO",
             "UKRAINE AIR FORCE", scene_drones, NAVY)
    row_card(268, 442, 238, 148, 5, "EUROPE",
             "EU PROPOSES €45BN LOAN FOR KYIV, 2027",
             "€25BN MILITARY, €20BN BUDGET SUPPORT, IF MEMBERS AGREE",
             "EUROPEAN COMMISSION", scene_eu, BLUE)
    row_card(512, 442, 238, 148, 6, "MARKETS * WASHINGTON",
             "FED MINUTES: NEARLY ALL SEE MORE HIKES",
             "OFFICIALS NEARLY UNITED ON MORE RATE RISES; DOW CLOSED -1.1%",
             "FEDERAL RESERVE", scene_fed, GOLD)
    row_card(756, 442, 238, 148, 7, "INDIA * WEATHER",
             "CYCLONE AKVAN VEERS TOWARD ODISHA",
             "EVACUATIONS BEGIN IN THE SOUTH; LANDFALL DUE FRIDAY",
             "IMD", scene_cyclone, TEAL)

    # Illustrated stories, row of four (8-11)
    row_card(24, 598, 238, 148, 8, "SUDAN * AMNESTY",
             "RSF DRONES KILLED 37 IN EL OBEID",
             "AMNESTY INTERNATIONAL ATTRIBUTES THE STRIKES TO THE RSF",
             "AMNESTY INTERNATIONAL", scene_sudan, ORANGE)
    row_card(268, 598, 238, 148, 9, "GAZA",
             "ISRAELI TANKS PUSH INTO CENTRAL GAZA",
             "FORCES ADVANCE PAST THE YELLOW LINE NEAR NUSEIRAT",
             "AL JAZEERA", scene_gaza, RED)
    row_card(512, 598, 238, 148, 10, "WASHINGTON",
             "DEMOCRATS PICK JEFFRIES 251-11",
             "HOUSE DEMOCRATS' VOTE NAMES THEIR SPEAKER CANDIDATE",
             "HOUSE DEMOCRATS", scene_capitol, NAVY)
    row_card(756, 598, 238, 148, 11, "GAMING",
             "GTA VI IS ON SALE AFTER 13 YEARS",
             "NEW ZEALAND SOLD FIRST AT MIDNIGHT; THE WORLD FOLLOWS",
             "ROCKSTAR GAMES", scene_gta, PURPLE)

    # Bottom left: the map. Bottom right: the briefs.
    outline(24, 754, 336, 208, INK, 2)
    draw_map(28, 762)
    text(372, 756, "ALSO ON WEDNESDAY", 3, RED)
    text(372 + text_w("ALSO ON WEDNESDAY", 3) + 10, 763,
         "* 35 MORE STORIES", 2, GRAY)
    by = 788
    for i, (n, place, txt, _dot) in enumerate(BRIEFS):
        col_x = 372 if i < 18 else 686
        row_y = by + (i % 18) * 10
        text(col_x, row_y, str(n), 1, RED)
        text(col_x + 16, row_y, place + " - " + txt, 1, INK)

    # Date check: what was left out, and why it was not this day's news
    outline(24, 970, W - 48, 42, RED, 2)
    text(36, 976, "DATE CHECK", 2, RED)
    body = [
        "NOT THIS DAY'S NEWS - FIRST REPORTED TUE 17 NOV: NVIDIA'S RESULTS AND THE HUANG RULING * THE US STRIKE ON QESHM * ALASKA'S SENATE CALL * THE KNESSET VOTE * THE KERCH BRIDGE COLLAPSE",
        "NOT YET NEWS: THE TRUMP-XI-PUTIN SUMMIT IS THURSDAY 19 * AKVAN'S LANDFALL IS FRIDAY 20 * CLAIMS ARE ATTRIBUTED, NOT STATED AS FACT",
        "SOURCES: AP * AFP * AL JAZEERA * NPR * DW * ONS * IMD * NASA * JPL * AMNESTY * WHO * UKMTO * ECDC * COGAT * THE FED",
    ]
    ly = 974
    for ln_text in body:
        for ln in wrap(ln_text, 1, 806):
            text(190, ly, ln, 1, INK)
            ly += 9


# -------------------------------------------------------------------- png
def png_bytes():
    raw = bytearray()
    row = W * 3
    for y in range(H):
        raw.append(0)
        raw += _buf[y * row:(y + 1) * row]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    compose()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png_bytes())


if __name__ == "__main__":
    main()
