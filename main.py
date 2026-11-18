#!/usr/bin/env python3
"""make.fun news-image-20261118 entry.

Writes one 1024x1024 PNG summing up the world news of Wednesday
18 November 2026 to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).

Design: a bold newspaper front page built for a vision judge that sees
the image at about 300 px across. A huge date masthead, one dominant
top story, and five supporting stories -- every headline set large
enough to stay legible in the thumbnail, one factual subhead each,
no small body text anywhere.

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
GRAY = (70, 76, 86)
FAINT = (203, 196, 178)
RED = (178, 32, 40)
BLUE = (26, 72, 128)
TEAL = (14, 110, 104)
GOLD = (196, 138, 30)
GREEN = (38, 110, 58)
YELLOW = (250, 210, 60)

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
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", "...#."),
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


# ------------------------------------------------------------------ icons
# Bold, simple pictograms drawn around a centre point, ~64 px across,
# with strokes thick enough to survive a shrink to 300 px wide.

def icon_burst(cx, cy, r, rgb, core_rgb):
    """Explosion starburst with a solid core (top story)."""
    d = r * 7 // 10
    for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r),
                   (d, d), (d, -d), (-d, d), (-d, -d)):
        line(cx, cy, cx + dx, cy + dy, rgb, 8)
    circle(cx, cy, r // 3, core_rgb)
    circle(cx, cy, r // 6, rgb)


def icon_missile(x0, y0, x1, y1):
    """Incoming missile: thick body, nose toward (x1, y1), fins and
    a flame at the tail (x0, y0) so it reads as a missile at 300 px."""
    circle(x0, y0, 7, GOLD)
    circle(x0, y0, 4, RED)
    line(x0, y0, x1, y1, INK, 13)
    line(x0, y0, x0 - 15, y0 + 3, INK, 6)
    line(x0, y0, x0 - 3, y0 - 15, INK, 6)


def icon_flags(cx, cy):
    """China and Russia flags on poles, side by side."""
    rect(cx - 33, cy - 26, 3, 54, INK)
    rect(cx - 30, cy - 26, 30, 21, RED)
    rect(cx - 26, cy - 22, 5, 5, YELLOW)
    for sx, sy in ((10, -24), (13, -19), (10, -14)):
        rect(cx - 30 + sx, cy + sy, 3, 3, YELLOW)
    rect(cx + 2, cy - 26, 3, 54, INK)
    rect(cx + 5, cy - 26, 30, 7, WHITE)
    rect(cx + 5, cy - 19, 30, 7, BLUE)
    rect(cx + 5, cy - 12, 30, 7, RED)
    outline(cx + 5, cy - 26, 30, 21, INK, 1)


def icon_aid(cx, cy):
    """Damaged building with a red-cross aid badge."""
    rect(cx - 30, cy - 6, 36, 34, GRAY)
    rect(cx - 30, cy - 13, 36, 7, GRAY)
    rect(cx - 20, cy + 14, 9, 14, PAPER)
    rect(cx - 2, cy - 6, 8, 10, PAPER)
    line(cx - 12, cy + 2, cx - 8, cy + 10, INK, 2)
    line(cx - 8, cy + 10, cx - 13, cy + 18, INK, 2)
    circle(cx + 19, cy - 15, 15, INK)
    circle(cx + 19, cy - 15, 12, WHITE)
    rect(cx + 16, cy - 22, 6, 14, RED)
    rect(cx + 12, cy - 18, 14, 6, RED)


def icon_virus(cx, cy):
    """Virus particle: spoked ball."""
    for dx, dy in ((24, 0), (-24, 0), (0, 24), (0, -24),
                   (17, 17), (17, -17), (-17, 17), (-17, -17)):
        line(cx, cy, cx + dx, cy + dy, RED, 4)
        circle(cx + dx + (3 if dx > 0 else -3 if dx < 0 else 0),
               cy + dy + (3 if dy > 0 else -3 if dy < 0 else 0), 4, RED)
    circle(cx, cy, 15, RED)
    circle(cx - 5, cy - 4, 3, WHITE)
    circle(cx + 6, cy + 5, 4, WHITE)


def icon_chart(cx, cy):
    """Rising market bars with an arrow."""
    for bx, bh, rgb in ((-27, 20, GOLD), (-9, 30, GOLD), (9, 42, GREEN)):
        rect(cx + bx, cy + 24 - bh, 13, bh, rgb)
    line(cx - 29, cy + 26, cx + 29, cy + 26, INK, 4)
    line(cx - 28, cy - 2, cx + 22, cy - 24, RED, 5)
    line(cx + 22, cy - 24, cx + 9, cy - 24, RED, 5)
    line(cx + 22, cy - 24, cx + 22, cy - 11, RED, 5)


def icon_probe(cx, cy):
    """Deep-space probe: gold bus, blue solar panels, dish, stars."""
    rect(cx - 31, cy - 9, 16, 18, BLUE)
    rect(cx + 15, cy - 9, 16, 18, BLUE)
    line(cx - 23, cy - 9, cx - 23, cy + 9, WHITE, 2)
    line(cx + 23, cy - 9, cx + 23, cy + 9, WHITE, 2)
    rect(cx - 15, cy - 4, 30, 3, INK)
    rect(cx - 8, cy - 11, 16, 22, GOLD)
    outline(cx - 8, cy - 11, 16, 22, INK, 2)
    circle(cx, cy - 20, 7, INK)
    circle(cx, cy - 20, 5, WHITE)
    line(cx, cy - 13, cx, cy - 11, INK, 3)
    line(cx + 6, cy + 8, cx + 16, cy + 20, INK, 3)
    circle(cx + 17, cy + 21, 2, INK)
    for sx, sy in ((-29, -24), (28, -22), (-27, 21)):
        rect(cx + sx, cy + sy, 3, 3, GOLD)


# -------------------------------------------------------------- composition
def strip(y, accent, headline, sub, icon):
    """One supporting story: full-width band, pictogram left, big text."""
    rect(24, y, W - 48, 92, WHITE)
    outline(24, y, W - 48, 92, INK, 3)
    rect(27, y + 3, 6, 86, accent)
    icon(72, y + 46)
    rect(114, y + 12, 2, 68, FAINT)
    text(126, y + 11, headline, 6, INK)
    text(126, y + 59, sub, 4, GRAY)


def compose():
    rect(0, 0, W, H, PAPER)
    outline(6, 6, W - 12, H - 12, INK, 3)

    # Masthead: paper name, then the date HUGE on two lines
    text_c(W // 2, 24, "THE WORLD IN ONE DAY", 6, INK)
    rect(24, 74, W - 48, 5, RED)
    rect(24, 83, W - 48, 2, INK)
    text_c(W // 2, 94, "WEDNESDAY", 11, INK)
    text_c(W // 2, 178, "NOVEMBER 18, 2026", 8, RED)
    rect(24, 244, W - 48, 3, INK)
    rect(24, 250, W - 48, 2, RED)

    # Top story: Iran strikes Gulf bases
    ty = 260
    rect(24, ty, W - 48, 248, WHITE)
    outline(24, ty, W - 48, 248, INK, 3)
    rect(24, ty, W - 48, 10, RED)
    text(40, ty + 20, "TOP STORY * MIDDLE EAST", 4, RED)
    text(40, ty + 54, "IRAN STRIKES", 10, INK)
    text(40, ty + 128, "GULF BASES", 10, INK)
    text(40, ty + 206, "KUWAIT, BAHRAIN HIT; U.S. STRUCK QESHM", 4, GRAY)
    icon_burst(880, ty + 114, 78, GOLD, RED)
    icon_missile(968, ty + 34, 922, ty + 80)

    # Five supporting stories
    strip(520, BLUE, "XI + PUTIN IN SHENZHEN",
          "APEC TALKS BEFORE TRUMP SUMMIT", icon_flags)
    strip(618, RED, "ZAPORIZHIA TOLL: 40 DEAD",
          "AID CENTRE HIT; DOZENS MISSING", icon_aid)
    strip(716, GREEN, "CONGO EBOLA TOPS 11,000",
          "CASES DOUBLED IN THREE MONTHS", icon_virus)
    strip(814, GOLD, "NVIDIA FORECASTS $130BN",
          "GOLD SINKS BELOW $3,800 AN OUNCE", icon_chart)
    strip(912, TEAL, "VOYAGER 1: ONE LIGHT-DAY",
          "ITS SIGNALS TAKE A FULL 24 HOURS", icon_probe)


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
