#!/usr/bin/env python3
"""make.fun news-image-20261118 entry.

Writes one 1024x1024 PNG summing up the world news of Wednesday
18 November 2026 to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).

Pure Python standard library, fully deterministic: no clock, no random,
no network, no file input. The image is drawn pixel by pixel from the
hard-coded headlines below, so two runs always produce identical bytes.
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
GRAY = (86, 92, 102)
FAINT = (203, 196, 178)
RED = (178, 32, 40)
BLUE = (26, 72, 128)
TEAL = (14, 110, 104)
GOLD = (196, 138, 30)
GREEN = (38, 110, 58)
SKY = (168, 205, 232)
SEA = (64, 118, 168)
SAND = (226, 205, 158)

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


def ring(cx, cy, r, rgb, t=3):
    circle(cx, cy, r, rgb)
    circle(cx, cy, max(0, r - t), PAPER)


def line(x0, y0, x1, y1, rgb, t=3):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    half = t // 2
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i // steps
        y = y0 + (y1 - y0) * i // steps
        rect(x - half, y - half, t, t, rgb)


# ------------------------------------------------------------------- font
# 5x7 bitmap font, generated in code. '#' = ink pixel.
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
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '*': (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
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


def text_r(right, y, s, scale, rgb):
    return text(right - text_w(s, scale), y, s, scale, rgb)


# ------------------------------------------------------------------ icons
def icon_burst(cx, cy, r, rgb):
    """Explosion star: 8 spokes plus a core."""
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
        line(cx, cy, cx + dx * r, cy + dy * r, rgb, 5)
    circle(cx, cy, r // 3, rgb)


def icon_flags(x, y):
    """China and Russia flags side by side, compact."""
    rect(x, y, 3, 26, INK)
    rect(x + 3, y, 26, 18, RED)
    for sx, sy in ((4, 3), (11, 1), (13, 6), (11, 11), (4, 8)):
        rect(x + 3 + sx, y + sy, 3, 3, (250, 210, 60))
    rect(x + 34, y, 3, 26, INK)
    rect(x + 37, y, 26, 6, WHITE)
    rect(x + 37, y + 6, 26, 6, BLUE)
    rect(x + 37, y + 12, 26, 6, RED)
    outline(x + 37, y, 26, 18, INK, 1)


def icon_aid(x, y):
    """Aid cross badge beside a damaged building."""
    rect(x, y, 24, 24, WHITE)
    outline(x, y, 24, 24, INK, 2)
    rect(x + 9, y + 4, 6, 16, RED)
    rect(x + 4, y + 9, 16, 6, RED)
    rect(x + 32, y + 8, 30, 18, GRAY)
    rect(x + 38, y + 2, 16, 6, GRAY)
    line(x + 48, y + 8, x + 62, y + 18, PAPER, 3)


def icon_virus(x, y):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
        line(x + 15, y + 15, x + 15 + dx * 12, y + 15 + dy * 12, RED, 3)
        circle(x + 15 + dx * 13, y + 15 + dy * 13, 2, RED)
    circle(x + 15, y + 15, 10, RED)
    circle(x + 11, y + 12, 2, WHITE)
    circle(x + 19, y + 17, 3, WHITE)


def icon_probe(x, y):
    """Voyager-style probe: dish, body, boom."""
    circle(x + 13, y + 14, 12, WHITE)
    ring(x + 13, y + 14, 12, INK, 2)
    circle(x + 13, y + 14, 3, INK)
    line(x + 21, y + 20, x + 30, y + 24, INK, 3)
    rect(x + 29, y + 21, 10, 7, GOLD)
    line(x + 36, y + 24, x + 56, y + 8, INK, 2)
    circle(x + 57, y + 7, 2, INK)


# -------------------------------------------------------------- composition
def panel(x, y, w, h, kicker, kicker_rgb, head, sub, icon):
    rect(x, y, w, h, WHITE)
    outline(x, y, w, h, INK, 3)
    rect(x, y, w, 10, kicker_rgb)
    text(x + 16, y + 22, kicker, 2, kicker_rgb)
    if icon:
        icon(x + w - 80, y + 13)
    ty = y + 52
    for ln in head:
        text(x + 16, ty, ln, 5, INK)
        ty += 40
    ty = y + 176
    for ln in sub:
        text(x + 16, ty, ln, 3, GRAY)
        ty += 25


def mini(x, y, w, h, tab_rgb, tab, head, sub):
    rect(x, y, w, h, WHITE)
    outline(x, y, w, h, INK, 3)
    rect(x, y, w, 22, tab_rgb)
    text(x + 10, y + 4, tab, 2, WHITE)
    ty = y + 32
    for ln in head:
        text(x + 10, ty, ln, 3, INK)
        ty += 22
    text(x + 10, y + 84, sub, 2, GRAY)


def compose():
    rect(0, 0, W, H, PAPER)
    outline(6, 6, W - 12, H - 12, INK, 3)

    # Masthead
    text_c(W // 2, 30, "THE WORLD IN ONE DAY", 8, INK)
    rect(24, 96, W - 48, 5, RED)
    rect(24, 105, W - 48, 2, INK)

    # Date band: the day, named loud and clear
    rect(24, 116, W - 48, 54, RED)
    text_c(W // 2, 126, "WEDNESDAY, 18 NOVEMBER 2026", 5, WHITE)
    text_c(W // 2, 178, "ALL STORIES REPORTED ON THIS DAY, ACROSS THE WORLD", 2, GRAY)

    # Top story
    tx, ty, tw, th = 24, 200, W - 48, 216
    rect(tx, ty, tw, th, WHITE)
    outline(tx, ty, tw, th, INK, 3)
    rect(tx, ty, tw, 10, RED)
    text(tx + 18, ty + 20, "TOP STORY * MIDDLE EAST", 3, RED)
    icon_burst(tx + tw - 40, ty + 28, 16, GOLD)
    text(tx + 12, ty + 48, "IRAN STRIKES GULF BASES", 7, INK)
    text(tx + 18, ty + 102, "REPLYING TO U.S. QESHM HIT", 6, INK)
    text(tx + 18, ty + 152, "TEHRAN TARGETS KUWAIT, BAHRAIN AFTER", 4, GRAY)
    text(tx + 18, ty + 184, "U.S. STRUCK MISSILE SITE ON QESHM", 4, GRAY)

    # Four main panels
    pw, ph = 486, 228
    panel(24, 424, pw, ph, "ASIA * DIPLOMACY", BLUE,
          ["XI AND PUTIN", "MEET IN", "SHENZHEN"],
          ["APEC TALKS COME BEFORE", "THREE-WAY TRUMP SUMMIT"],
          icon_flags)
    panel(514, 424, pw, ph, "EUROPE * WAR IN UKRAINE", RED,
          ["ZAPORIZHIA AID", "CENTRE TOLL", "RISES TO 40"],
          ["ZELENSKYY RAISES TOLL;", "DOZENS STILL MISSING"],
          icon_aid)
    panel(24, 664, pw, ph, "AFRICA * HEALTH", GREEN,
          ["CONGO EBOLA", "CASES PASS", "11,000"],
          ["DOUBLED IN THREE MONTHS;", "CHILDREN HARDEST HIT"],
          icon_virus)
    panel(514, 664, pw, ph, "SCIENCE * SPACE", TEAL,
          ["VOYAGER 1 NOW", "ONE LIGHT-DAY", "FROM EARTH"],
          ["SIGNALS TAKE 24 HOURS TO", "REACH THE 1977 PROBE"],
          icon_probe)

    # Four mini stories
    mw, mh = 237, 106
    mini(24, 902, mw, mh, BLUE, "POLITICS",
         ["PELTOLA WINS", "ALASKA VOTE"], "SENATE: DEMS 56-44")
    mini(273, 902, mw, mh, RED, "HEALTH",
         ["U.S. LOSES", "MEASLES-FREE"], "CASES PASS 5,400")
    mini(522, 902, mw, mh, GOLD, "MARKETS",
         ["NVIDIA SEES", "$130BN QTR"], "GOLD BELOW $3,800")
    mini(771, 902, mw, mh, TEAL, "CLIMATE",
         ["COP31 FIGHT", "ON AID CASH"], "DEAL STILL UNCLEAR")


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
