#!/usr/bin/env python3
"""Generates every raster asset used by the watch face.

Visual language ported from the approved TypeScript mockups
(wear-os-car-mockups): near-black ground, a single ember accent used
sparingly, hairline dividers, tiny wide-tracked uppercase labels. Colors
below are the mockups' oklch tokens, resolved to sRGB by sampling the
live rendering in a browser (WFF colors are plain hex, no oklch).

Cars render as flat white silhouettes (alpha = coverage) so `tintColor`
in the XML applies the user's chosen accent; wheels are drawn generically
here rather than per-car, mirroring CarSilhouette.tsx.

    python3 tools/gen_art.py            # write assets
    python3 tools/gen_art.py --sheet    # also write a contact sheet
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cars as CARS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "watchface", "src", "main", "res")
FONT_DIR = os.path.join(RES, "font")
OUT = os.path.join(RES, "drawable-nodpi")

SIZE = 480
S = 4

# --- palette, sampled from the mockup's oklch tokens (see module docstring) --
BG = (8, 10, 15)
BG_DEEP = (3, 4, 6)
INK = (244, 245, 248)
INK_MUTED = (142, 146, 154)
ACCENT = (251, 109, 39)
ACCENT_SOFT = (210, 95, 41)

# --- layout, in the 480x480 design space, ported from WatchFace.tsx ---------
CAR_BOX = (80, 150, 320, 120)        # x, y, w, h - viewBox AR is 1000:~220 avg
ENERGY_TOP = 62
DIVIDER_Y = 266
METRIC_TOP = 282
TIME_TOP = 334
TIME_TOP_AMBIENT = 300
BATTERY_ROW_AMBIENT = 414


def px(v):
    return int(round(v * S))


def lw(units, minimum=1):
    return max(int(round(units * S)), minimum)


def down(img, w, h):
    return img.resize((w, h), Image.LANCZOS)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def circle_mask(r=SIZE / 2.0, feather=0.9, n=SIZE):
    yy, xx = np.mgrid[0:n, 0:n]
    dist = np.sqrt((xx + 0.5 - n / 2.0) ** 2 + (yy + 0.5 - n / 2.0) ** 2)
    return Image.fromarray((np.clip((r - dist) / feather, 0, 1) * 255).astype(np.uint8), "L")


# ============================================================== silhouettes ==
class Placement:
    """Maps one car's own coordinate space (0..1000, 0..height) into a
    pixel box, bottom-aligned and centred - same convention CarSilhouette.tsx
    uses with its 400x150 viewBox."""

    def __init__(self, car, box_w, box_h, bottom_pad=4.0):
        self.s = box_w / 1000.0
        ground = max(cy + r for _, cy, r in car.wheels)
        self.oy = box_h - bottom_pad - ground * self.s

    def pts(self, points):
        return [(px(x * self.s), px(y * self.s + self.oy)) for x, y in points]

    def pt(self, p):
        return self.pts([p])[0]

    def u(self, v):
        return v * self.s * S


def _wheel(d, pl, cx, cy, r, outline_only=False):
    """Tyre ring + punched hub gap + hub + eight spokes - CarSilhouette.tsx's
    algorithm, generic across every car."""
    c = pl.pt((cx, cy))
    R = pl.u(r)

    def box(f):
        return [c[0] - R * f, c[1] - R * f, c[0] + R * f, c[1] + R * f]

    if outline_only:
        d.ellipse(box(0.62), outline=255, width=lw(1.6, 2))
        return

    d.ellipse(box(1.0), fill=255)          # tyre
    d.ellipse(box(0.58), fill=0)           # punched hub gap
    for k in range(8):
        a = (k / 8) * 2 * math.pi
        d.line([(c[0] + R * 0.22 * math.cos(a), c[1] + R * 0.22 * math.sin(a)),
                (c[0] + R * 0.54 * math.cos(a), c[1] + R * 0.54 * math.sin(a))],
               fill=255, width=lw(1.1, 2))
    d.ellipse(box(0.2), fill=255)          # hub


def car_mask(car, box_w, box_h, outline_only=False):
    W, H = px(box_w), px(box_h)
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    pl = Placement(car, box_w, box_h)

    if outline_only:
        d.line(pl.pts(car.body()), fill=255, width=lw(1.7, 2), joint="curve")
        for cx, cy, r in car.wheels:
            _wheel(d, pl, cx, cy, r, outline_only=True)
        return mask

    d.polygon(pl.pts(car.body()), fill=255)
    for cx, cy, r in car.wheels:
        _wheel(d, pl, cx, cy, r)
    # Detail creases cut a thin transparent hairline through the solid body -
    # the flat backdrop behind reads through it exactly like the mockup's
    # background-colored stroke, at zero extra tint complexity.
    for line in car.details():
        d.line(pl.pts(line), fill=0, width=lw(1.3, 2), joint="curve")
    return mask


def white_from_mask(mask, w, h):
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    img.putalpha(down(mask, w, h))
    return img


def render_car(car, outline_only=False):
    """Cars are modelled nose-right and mirrored on output, so they face left
    - matching the mockup screenshot's orientation."""
    _, _, bw, bh = CAR_BOX
    mask = car_mask(car, bw, bh, outline_only).transpose(Image.FLIP_LEFT_RIGHT)
    return white_from_mask(mask, bw, bh)


# ==================================================================== rings ==
CENTER = SIZE / 2.0
R_OUTER = 232.0


def polar(r, deg):
    rad = math.radians(deg - 90)
    return (CENTER + r * math.cos(rad), CENTER + r * math.sin(rad))


def render_tick_ring(ambient=False):
    """Static minute ring: hairline safe-zone circle, 60 ticks (majors every
    5), and 00/15/30/45 numerals. The live per-minute sweep accent arc is
    drawn separately, directly in the XML, so it can animate."""
    W = SIZE * S
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")

    if not ambient:
        r = px(R_OUTER - 34)
        c = px(CENTER)
        d.ellipse([c - r, c - r, c + r, c + r], outline=(255, 255, 255, 20), width=lw(0.5))

    for i in range(60):
        is_major = i % 5 == 0
        if ambient and not is_major:
            continue
        length = 14 if is_major else 7
        p1 = polar(R_OUTER, i * 6)
        p2 = polar(R_OUTER - length, i * 6)
        opacity = (0.5 if ambient else (0.62 if is_major else 0.28))
        col = INK + (int(255 * opacity),)
        d.line([tuple(px(v) for v in p1), tuple(px(v) for v in p2)],
               fill=col, width=lw(2.0 if is_major else 1.0))

    f = font("ibm_plex_mono_medium.ttf", px(15))
    for m in (0, 15, 30, 45):
        p = polar(R_OUTER - 30, m * 6)
        opacity = 0.45 if ambient else 0.62
        d.text((px(p[0]), px(p[1])), f"{m:02d}", font=f,
               fill=INK + (int(255 * opacity),), anchor="mm")

    return down(img, SIZE, SIZE)


def render_backdrop():
    """Two soft radial glows (energy zone + a lower hint) over near-black."""
    W = SIZE * S
    img = Image.new("RGBA", (W, W), BG + (255,))

    def glow(cx, cy, rw, rh, color, alpha):
        yy, xx = np.mgrid[0:W, 0:W]
        dist = np.sqrt(((xx - px(cx)) / rw) ** 2 + ((yy - px(cy)) / rh) ** 2)
        a = np.clip(1 - dist, 0, 1) ** 1.8
        layer = np.zeros((W, W, 4))
        layer[:, :, 0], layer[:, :, 1], layer[:, :, 2] = color
        layer[:, :, 3] = a * alpha
        return Image.fromarray(layer.astype(np.uint8), "RGBA")

    img.alpha_composite(glow(240, 128 + 100, px(170) / S, px(100) / S, ACCENT, 46))
    img.alpha_composite(glow(240, 480, px(220) / S, px(140) / S, (36, 38, 48), 130))

    out = down(img, SIZE, SIZE)
    out.putalpha(circle_mask())
    return out


# ================================================================== energy ==
def render_energy_gap_mask(w=436, h=32, segments=16, gap=12):
    """A 16-segment gap mask: opaque where a segment sits, transparent in the
    gaps between. Composited over a continuous scaled bar so a single
    Group/scaleX progress fill (the WFF-native technique) reads as discrete
    chiclets, exactly like EnergyBadge.tsx's 16-bar."""
    img = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(img)
    seg_w = (w * S - (segments - 1) * gap * S / 4) / segments
    x = 0.0
    for _ in range(segments):
        d.rectangle([x, 0, x + seg_w, h * S], fill=255)
        x += seg_w + gap * S / 4
    return img.resize((w, h), Image.LANCZOS)


# ================================================================== preview ==
def tint(img, color):
    solid = Image.new("RGBA", img.size, tuple(color) + (255,))
    solid.putalpha(img.split()[3])
    return solid


def stamp(base, fn):
    """Draw through a transparent layer so partial alpha actually blends -
    ImageDraw on an RGBA image replaces pixels rather than compositing."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer, "RGBA"))
    base.alpha_composite(layer)


def render_preview(car_id="porsche_911", accent=ACCENT, ambient=False):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255)) if ambient else render_backdrop().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    f_mono = font("ibm_plex_mono_medium.ttf", 10)
    f_energy = font("saira_condensed_regular.ttf", 30)
    f_metric = font("saira_condensed_regular.ttf", 26)
    f_time = font("dseg7_bold.ttf", 92)

    car = CARS.BY_ID[car_id]
    bx, by, bw, bh = CAR_BOX

    def tracked(cx, y, txt, f, fill, sp, anchor="mt"):
        widths = [d.textlength(ch, font=f) for ch in txt]
        total = sum(widths) + sp * (len(txt) - 1)
        x = cx - total / 2 if "m" in anchor else cx
        for ch, wd in zip(txt, widths):
            d.text((x, y), ch, font=f, fill=fill, anchor="l" + anchor[1])
            x += wd + sp

    if ambient:
        img.alpha_composite(render_tick_ring(ambient=True))
        img.alpha_composite(tint(render_car(car, outline_only=True), accent), (bx, by))

        tracked(240, ENERGY_TOP, "ENERGIA", f_mono, INK_MUTED + (150,), 4.2)
        d.text((240, ENERGY_TOP + 20), "84", font=f_energy, fill=INK + (204,), anchor="mt")

        stamp(img, lambda dd: dd.text((240, TIME_TOP_AMBIENT), "88:88", font=f_time,
                                      fill=(255, 255, 255, 22), anchor="mt"))
        d.text((240, TIME_TOP_AMBIENT), "21:47", font=f_time, fill=INK + (235,), anchor="mt")

        tracked(240, BATTERY_ROW_AMBIENT, "86%", f_mono, INK_MUTED + (255,), 3.4)
    else:
        img.alpha_composite(render_tick_ring())
        sweep_deg = (47 + 0 / 60) * 6
        d.arc([px(CENTER - (R_OUTER - 1)) / S, px(CENTER - (R_OUTER - 1)) / S,
               px(CENTER + (R_OUTER - 1)) / S, px(CENTER + (R_OUTER - 1)) / S],
              -90, -90 + sweep_deg, fill=accent + (230,), width=2)

        tracked(240, ENERGY_TOP, "ENERGIA", f_mono, INK_MUTED + (255,), 4.2)
        d.text((240, ENERGY_TOP + 20), "84", font=f_energy, fill=accent + (255,), anchor="mt")
        bar_w, seg_h, gap, n = 108, 8, 3, 16
        seg_w = (bar_w - (n - 1) * gap) / n
        filled = round(0.84 * n)
        x0 = 240 - bar_w / 2
        for i in range(n):
            x = x0 + i * (seg_w + gap)
            h = seg_h if i < filled else 5
            col = accent + (255,) if i < filled else (255, 255, 255, 40)
            d.rectangle([x, ENERGY_TOP + 58 - h, x + seg_w, ENERGY_TOP + 58], fill=col)

        img.alpha_composite(tint(render_car(car), accent), (bx, by))

        d.line([(96, DIVIDER_Y), (384, DIVIDER_Y)], fill=(255, 255, 255, 41), width=1)
        cols = [(146, "KROKI", "8432", None), (240, "TEMP", "24", "°"),
                (334, "BATERIA", "86", "%")]
        for i, (cx, label, value, unit) in enumerate(cols):
            if i:
                d.line([(cx - 47, METRIC_TOP), (cx - 47, METRIC_TOP + 46)],
                       fill=(255, 255, 255, 20), width=1)
            tracked(cx, METRIC_TOP, label, f_mono, INK_MUTED + (255,), 3.0)
            col = accent if label == "BATERIA" else INK
            wv = d.textlength(value, font=f_metric)
            wu = d.textlength(unit, font=f_mono) if unit else 0
            x0 = cx - (wv + wu) / 2
            d.text((x0, METRIC_TOP + 16), value, font=f_metric, fill=col + (255,), anchor="lt")
            if unit:
                d.text((x0 + wv + 1, METRIC_TOP + 24), unit, font=f_mono,
                       fill=INK_MUTED + (255,), anchor="lt")

        stamp(img, lambda dd: dd.text((240, TIME_TOP), "88:88", font=f_time,
                                      fill=(255, 255, 255, 26), anchor="mt"))
        d.text((240, TIME_TOP), "21:47", font=f_time, fill=INK + (255,), anchor="mt")

    img.putalpha(circle_mask())
    return img


def contact_sheet():
    cols = 3
    bw, bh = CAR_BOX[2], CAR_BOX[3]
    rows = (len(CARS.CARS) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (bw + 24), rows * (bh + 40)), BG_DEEP + (255,))
    d = ImageDraw.Draw(sheet)
    f = font("ibm_plex_mono_medium.ttf", 13)
    for i, car in enumerate(CARS.CARS):
        col, row = i % cols, i // cols
        x, y = col * (bw + 24) + 12, row * (bh + 40) + 28
        sheet.alpha_composite(tint(render_car(car), ACCENT), (x, y))
        d.text((x, y - 18), car.name, font=f, fill=INK + (255,))
    return sheet


# ===================================================================== main ==
def main():
    os.makedirs(OUT, exist_ok=True)
    scratch = os.environ.get("SCRATCH", OUT)

    render_backdrop().save(os.path.join(OUT, "backdrop.png"))
    render_tick_ring().save(os.path.join(OUT, "tick_ring.png"))
    render_tick_ring(ambient=True).save(os.path.join(OUT, "tick_ring_aod.png"))
    render_energy_gap_mask().save(os.path.join(OUT, "energy_gap_mask.png"))

    for car in CARS.CARS:
        render_car(car).save(os.path.join(OUT, f"car_{car.id}.png"))
        render_car(car, outline_only=True).save(os.path.join(OUT, f"car_{car.id}_aod.png"))

    render_preview().save(os.path.join(OUT, "preview.png"))

    contact_sheet().save(os.path.join(scratch, "cars_sheet.png"))
    render_preview().save(os.path.join(scratch, "preview_check.png"))
    render_preview(ambient=True).save(os.path.join(scratch, "aod_check.png"))

    total = 0
    for f in sorted(os.listdir(OUT)):
        n = os.path.getsize(os.path.join(OUT, f))
        total += n
        print(f"{f:26s} {n / 1024:7.1f} kB")
    print(f"{'TOTAL':26s} {total / 1024:7.1f} kB")


if __name__ == "__main__":
    main()
