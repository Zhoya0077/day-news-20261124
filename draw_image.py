#!/usr/bin/env python3
"""Render the 24 November 2026 world-news front page as entry.png (1024x1024).

Pillow only, no external assets: every icon is drawn from primitives.
"""

import math

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
NAVY = (13, 27, 42)
PAPER = (255, 255, 255)
INK = (13, 27, 42)
SUB_INK = (58, 71, 84)
RULE = (13, 27, 42)
FOOT_BG = (236, 239, 243)
RED = (198, 40, 40)

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BANNER_H = 132
GRID_TOP = BANNER_H + 2
FOOTER_TOP = 938
GRID_BOTTOM = FOOTER_TOP - 2

# type scale: one deck size everywhere, headlines shrink only when they must
DECK_PT = 20
HEAD_MAX = 46
HEAD_MIN = 26
HEAD_GAP = 12

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def text_w(draw, text, f):
    return draw.textlength(text, font=f)


def wrap(draw, text, f, max_w):
    """Greedy word wrap; returns lines that each fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(draw, trial, f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_block(draw, text, path, max_w, max_h, hi, lo, leading=1.16):
    """Largest font size in [lo, hi] whose wrapped block fits the box."""
    for size in range(hi, lo - 1, -1):
        f = font(path, size)
        lines = wrap(draw, text, f, max_w)
        if all(text_w(draw, line, f) <= max_w for line in lines):
            if len(lines) * size * leading <= max_h:
                return f, lines, size * leading
    f = font(path, lo)
    return f, wrap(draw, text, f, max_w), lo * leading


def tracked(draw, xy, text, f, fill, tracking=0.0):
    """Draw text with extra letter spacing; returns the width used."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += text_w(draw, ch, f) + tracking
    return x - xy[0]


def tracked_w(draw, text, f, tracking):
    return sum(text_w(draw, ch, f) for ch in text) + tracking * (len(text) - 1)


def fit_tracked(draw, text, path, max_w, hi, lo, tracking_ratio=0.14):
    for size in range(hi, lo - 1, -1):
        f = font(path, size)
        tracking = size * tracking_ratio
        if tracked_w(draw, text, f, tracking) <= max_w:
            return f, tracking
    f = font(path, lo)
    return f, lo * tracking_ratio


# ---------------------------------------------------------------- icons ----
# Each icon is a white glyph on a filled rounded square, drawn by panel().

def icon_chip(d, x, y, s):
    """Microchip: package outline, inner die, pins on all four sides."""
    d.rounded_rectangle([x + 12, y + 12, x + s - 12, y + s - 12], radius=5,
                        outline=(255, 255, 255), width=3)
    d.rectangle([x + 23, y + 23, x + s - 23, y + s - 23], fill=(255, 255, 255))
    for i in range(3):
        off = 17 + i * 9
        d.line([x + 3, y + off, x + 12, y + off], fill=(255, 255, 255), width=3)
        d.line([x + s - 12, y + off, x + s - 3, y + off], fill=(255, 255, 255), width=3)
        d.line([x + off, y + 3, x + off, y + 12], fill=(255, 255, 255), width=3)
        d.line([x + off, y + s - 12, x + off, y + s - 3], fill=(255, 255, 255), width=3)


def icon_scales(d, x, y, s):
    """Scales of justice: post, beam, two pans, base."""
    cx = x + s / 2
    d.line([cx, y + 10, cx, y + s - 12], fill=(255, 255, 255), width=3)
    d.line([x + 10, y + 14, x + s - 10, y + 14], fill=(255, 255, 255), width=3)
    d.line([x + 13, y + s - 12, x + s - 13, y + s - 12], fill=(255, 255, 255), width=3)
    for px in (x + 11, x + s - 11):
        d.line([px, y + 14, px, y + 20], fill=(255, 255, 255), width=2)
        d.polygon([(px - 9, y + 20), (px + 9, y + 20), (px + 4, y + 32), (px - 4, y + 32)],
                  fill=(255, 255, 255))


def icon_thermo(d, x, y, s):
    """Thermometer: thick bulb and tube with scale marks."""
    cx = x + s / 2 - 5
    d.rounded_rectangle([cx - 4, y + 7, cx + 4, y + s - 20], radius=4,
                        outline=(255, 255, 255), width=3)
    d.ellipse([cx - 10, y + s - 24, cx + 10, y + s - 4], fill=(255, 255, 255))
    d.rectangle([cx - 2, y + 20, cx + 2, y + s - 22], fill=(255, 255, 255))
    for i in range(5):
        ty = y + 14 + i * 6
        d.line([cx + 7, ty, cx + 16, ty], fill=(255, 255, 255), width=2)


def _star(d, cx, cy, r_out, r_in, points, fill):
    """Filled spiky star, used for the mine blast."""
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = -math.pi / 2 + i * math.pi / points
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=fill)


def icon_tanker(d, x, y, s):
    """Tanker in side view with a large blast star bursting from its deck."""
    # hull: long deck, raked bow right, flat keel
    d.polygon([(x + 3, y + 25), (x + 45, y + 25), (x + 39, y + 34), (x + 9, y + 34)],
              fill=(255, 255, 255))
    # deckhouse aft + funnel
    d.rectangle([x + 7, y + 16, x + 17, y + 25], fill=(255, 255, 255))
    d.rectangle([x + 10, y + 10, x + 14, y + 16], fill=(255, 255, 255))
    # tank domes forward
    d.rectangle([x + 21, y + 21, x + 40, y + 25], fill=(255, 255, 255))
    # blast star rising amidships
    _star(d, x + 31, y + 18, 13, 5.0, 8, (255, 255, 255))
    # waterline under the keel
    d.line([x + 3, y + 39, x + s - 3, y + 39], fill=(255, 255, 255), width=2)


def icon_sinking(d, x, y, s):
    """Ship rolled over and half under the waterline, bow tilted down."""
    # hull, tilted clockwise: stern high left, bow low right
    d.polygon([(x + 4, y + 24), (x + 40, y + 33), (x + 35, y + 41), (x + 8, y + 31)],
              fill=(255, 255, 255))
    # superstructure sitting on the sloping deck
    d.polygon([(x + 9, y + 15), (x + 21, y + 18), (x + 22, y + 25), (x + 10, y + 22)],
              fill=(255, 255, 255))
    d.polygon([(x + 12, y + 9), (x + 16, y + 10), (x + 16, y + 15), (x + 12, y + 14)],
              fill=(255, 255, 255))
    # water: line passes through the hull so the ship reads as going under
    d.line([x + 2, y + 36, x + s - 2, y + 36], fill=(255, 255, 255), width=3)
    for wy in (y + 44,):
        pts = [(x + 3 + k, wy + (2 if (k // 4) % 2 == 0 else -2)) for k in range(0, s - 6, 4)]
        d.line(pts, fill=(255, 255, 255), width=3)


def icon_health(d, x, y, s):
    """Bold medical cross, no container, so it cannot read as a record button."""
    cx = cy = x + s / 2
    d.rectangle([cx - 19, cy - 6.5, cx + 19, cy + 6.5], fill=(255, 255, 255))
    d.rectangle([cx - 6.5, cy - 19, cx + 6.5, cy + 19], fill=(255, 255, 255))


ICONS = [icon_chip, icon_scales, icon_thermo, icon_tanker, icon_sinking, icon_health]

STORIES = [
    ("TECH · USA", "JENSEN HUANG BACK AS NVIDIA CEO",
     "Trump intervenes; markets surge, Nasdaq +6.5%", (27, 79, 156)),
    ("WORLD COURT · THE HAGUE", "ICJ: MYANMAR COMMITTED GENOCIDE",
     "Rohingya ruling backed by 14 nations", (91, 58, 142)),
    ("CLIMATE · COP31", "CLIMATE SUMMIT ENDS WITH NO DEAL",
     "Fossil-fuel pact collapses; UN urges action", (30, 107, 69)),
    ("MIDDLE EAST · HORMUZ", "3 TANKERS HIT MINES IN HORMUZ",
     "Iran refuses talks; Qatar mediates in Washington", (170, 74, 28)),
    ("WAR · UKRAINE", "UKRAINE SINKS RUSSIAN CORVETTE",
     "Naval drones strike off the Libyan coast", (141, 31, 43)),
    ("HEALTH · USA", "US LOSES MEASLES-FREE STATUS",
     "Elimination status ends after 25 years", (15, 95, 107)),
]


# ----------------------------------------------------------------- panel ---

def panel(d, box, story, icon, overflow):
    """Draw one story panel and record any text that escapes its box."""
    x0, y0, x1, y1 = box
    accent = story[3]
    pad_x = 26
    left, right = x0 + pad_x, x1 - pad_x
    top, bottom = y0 + 20, y1 - 20
    inner_w = right - left

    icon_s = 48
    ix, iy = right - icon_s, top
    d.rounded_rectangle([ix, iy, ix + icon_s, iy + icon_s], radius=10, fill=accent)
    icon(d, ix, iy, icon_s)

    kf, ktrack = fit_tracked(d, story[0], BOLD, inner_w - icon_s - 16, 16, 10)
    kw = tracked(d, (left, top + 10), story[0], kf, accent, ktrack)
    if left + kw > right - icon_s - 10:
        overflow.append((story[0], "kicker", (left, top, left + kw, top + 20), box))

    rule_y = top + icon_s + 7
    d.rectangle([left, rule_y, left + 44, rule_y + 3], fill=accent)
    head_top = rule_y + 14
    avail_h = bottom - head_top

    # deck keeps one fixed size in every panel so the page reads consistently
    sf = font(REG, DECK_PT)
    slines = wrap(d, story[2], sf, inner_w)
    sline_h = DECK_PT * 1.32
    sub_h = len(slines) * sline_h

    hf, hlines, hline_h = None, [], 0
    for size in range(HEAD_MAX, HEAD_MIN - 1, -1):
        cand = font(BOLD, size)
        lines = wrap(d, story[1], cand, inner_w)
        if len(lines) * size * 1.12 + HEAD_GAP + sub_h <= avail_h:
            hf, hlines, hline_h = cand, lines, size * 1.12
            break
    if hf is None:  # smallest size still does not fit: draw it and report
        hf = font(BOLD, HEAD_MIN)
        hlines = wrap(d, story[1], hf, inner_w)
        hline_h = HEAD_MIN * 1.12
        overflow.append((story[1], "headline+deck", (left, head_top, right, bottom), box))

    # centre the headline+deck block in the space under the accent rule
    block_h = len(hlines) * hline_h + HEAD_GAP + sub_h
    y = head_top + max(0.0, (avail_h - block_h) / 2)

    for line in hlines:
        d.text((left, y), line, font=hf, fill=INK)
        bb = d.textbbox((left, y), line, font=hf)
        if bb[2] > right + 1:
            overflow.append((line, "headline", bb, (left, head_top, right, bottom)))
        y += hline_h

    y += HEAD_GAP
    for line in slines:
        d.text((left, y), line, font=sf, fill=SUB_INK)
        bb = d.textbbox((left, y), line, font=sf)
        if bb[2] > right + 1 or bb[3] > bottom + 2:
            overflow.append((line, "sub", bb, (left, head_top, right, bottom)))
        y += sline_h


def draw_banner(d):
    d.rectangle([0, 0, W, BANNER_H], fill=NAVY)
    d.rectangle([0, BANNER_H - 6, W, BANNER_H], fill=RED)

    small = font(BOLD, 19)
    tracked(d, (32, 22), "THE WORLD IN ONE DAY", small, (255, 255, 255), 5.4)

    strap = font(REG, 15)
    s = "MORNING EDITION"
    d.text((W - 32 - text_w(d, s, strap), 25), s, font=strap, fill=(150, 168, 186))

    date = "TUESDAY 24 NOVEMBER 2026"
    df, dtrack = fit_tracked(d, date, BOLD, W - 64, 66, 40, tracking_ratio=0.02)
    tw = tracked_w(d, date, df, dtrack)
    tracked(d, ((W - tw) / 2, 50), date, df, (255, 255, 255), dtrack)


def draw_grid(d, overflow):
    col_w = W // 2
    row_h = (GRID_BOTTOM - GRID_TOP) / 3.0
    for i, story in enumerate(STORIES):
        r, c = divmod(i, 2)
        x0 = c * col_w
        y0 = GRID_TOP + r * row_h
        panel(d, (x0, y0, x0 + col_w, y0 + row_h), story, ICONS[i], overflow)

    d.line([col_w, GRID_TOP, col_w, GRID_BOTTOM], fill=RULE, width=2)
    for r in (1, 2):
        y = round(GRID_TOP + r * row_h)
        d.line([0, y, W, y], fill=RULE, width=2)
    d.line([0, GRID_TOP, W, GRID_TOP], fill=RULE, width=2)
    d.line([0, GRID_BOTTOM, W, GRID_BOTTOM], fill=RULE, width=2)


FOOTER_ITEMS = [
    "ALSO:",
    "Sanofi buys Insmed for $41B",
    "Nepal quake M5.6",
    "China opens Tiangong station to first foreign astronaut",
    "FIFA names Women's World Cup hosts for 2031 & 2035",
]


def draw_footer(d):
    d.rectangle([0, FOOTER_TOP, W, H], fill=FOOT_BG)
    d.line([0, FOOTER_TOP, W, FOOTER_TOP], fill=RULE, width=2)
    f = font(BOLD, 15)
    sep = " · "
    # glue the separator to the item it follows so no line starts with a bullet
    tokens = [it + (" " if i == 0 else sep) for i, it in enumerate(FOOTER_ITEMS)]
    tokens[-1] = FOOTER_ITEMS[-1]

    lines, cur = [], ""
    for tok in tokens:
        trial = cur + tok
        if not cur or text_w(d, trial.rstrip(), f) <= W - 64:
            cur = trial
        else:
            lines.append(cur.rstrip())
            cur = "   " + tok
    if cur.strip():
        lines.append(cur.rstrip())

    block_h = len(lines) * 22
    y = FOOTER_TOP + (H - FOOTER_TOP - block_h) / 2 - 2
    for line in lines:
        d.text((32, y), line, font=f, fill=INK)
        y += 22
    return lines


if __name__ == "__main__":
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    draw_banner(d)
    overflow = []
    draw_grid(d, overflow)
    foot_lines = draw_footer(d)
    img.save("entry.png", format="PNG", optimize=True)

    print("footer lines:", len(foot_lines))
    for line in foot_lines:
        print("  |", line)
    print("overflow:", overflow if overflow else "none")
