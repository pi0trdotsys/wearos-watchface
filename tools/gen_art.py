#!/usr/bin/env python3
"""Generates every raster asset used by the watch face.

The cars are drawn as flat white silhouettes with knocked-out glass, arches and
apertures. They carry no colour of their own: the watch face applies the user's
chosen theme colour with `tintColor`, so one image serves every palette.

Everything is drawn 4x oversampled and downsampled with Lanczos.

    python3 tools/gen_art.py            # write assets
    python3 tools/gen_art.py --sheet    # also write a contact sheet of the cars
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

# --- layout, in the 480x480 design space -------------------------------------
# Sized so nothing lands on the bezel numerals: the 10 and 50 marks sit at
# y=137, the 20 and 40 marks at x=62 and x=417.
CAR_BOX = (54, 134, 372, 106)       # x, y, w, h
BADGE = (219, 44, 42, 27)           # date badge
ENERGY_BASELINE = 104               # energy label and value share this baseline
ROW_Y = 256                         # top of the three-metric row
ROW_VALUE_Y = 269
COL_X = (132, 240, 348)
TIME_Y = 304
TIME_SIZE = 78

ACCENT = (255, 90, 31)
MUTED = (138, 148, 166)
WHITE = (255, 255, 255)
INK = (8, 10, 14)


def px(v):
    return int(round(v * S))


def lw(units, minimum=1):
    return max(int(round(units * S)), minimum)


def down(img, w, h):
    return img.resize((w, h), Image.LANCZOS)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


# ============================================================== silhouettes ==
# Deliberate stylisation: the bodies are drawn slightly flatter than life, the
# way a side-profile illustration usually is. Straight orthographic proportions
# read stubby at watch size.
SQUASH = 0.90


class Placement:
    """Maps one car's own coordinate space into a pixel box, bottom aligned."""

    def __init__(self, car, box_w, box_h, bottom_pad=2.0):
        self.car = car
        self.s = box_w / 1000.0
        self.sy = self.s * SQUASH
        self.oy = box_h - bottom_pad - car.height * self.sy

    def pts(self, points):
        return [(px(x * self.s), px(y * self.sy + self.oy)) for x, y in points]

    def pt(self, p):
        return self.pts([p])[0]

    def u(self, v):
        return v * self.s * S

    def uy(self, v):
        return v * self.sy * S


def _wheel(mask, pl, cx, cy, r, outline_only=False):
    """Tyre ring, rim lip and a twin five-spoke face."""
    d = ImageDraw.Draw(mask)
    c = pl.pt((cx, cy))
    R, RY = pl.u(r), pl.uy(r)

    def box(f):
        return [c[0] - R * f, c[1] - RY * f, c[0] + R * f, c[1] + RY * f]

    if outline_only:
        d.ellipse(box(1.0), outline=255, width=lw(1.5, 2))
        d.ellipse(box(0.66), outline=255, width=lw(1.1, 2))
        d.ellipse(box(0.16), fill=255)
        return

    d.ellipse(box(1.0), fill=255)                  # tyre
    d.ellipse(box(0.70), fill=0)             # sidewall inner edge
    d.ellipse(box(0.665), fill=255)          # rim flange
    d.ellipse(box(0.60), fill=0)             # rim face

    for k in range(5):                           # five twin spokes
        base = -90 + k * 72 + 12
        for off in (-7.0, 7.0):
            a = math.radians(base + off)
            d.line([(c[0] + R * 0.19 * math.cos(a), c[1] + RY * 0.19 * math.sin(a)),
                    (c[0] + R * 0.585 * math.cos(a), c[1] + RY * 0.585 * math.sin(a))],
                   fill=255, width=lw(1.15, 2))

    d.ellipse(box(0.19), fill=255)           # centre lock cap
    d.ellipse(box(0.075), fill=0)


def car_mask(car, box_w, box_h, outline_only=False):
    """Single-channel coverage mask for one car at the given pixel box."""
    W, H = px(box_w), px(box_h)
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    pl = Placement(car, box_w, box_h)

    if outline_only:
        d.line(pl.pts(car.outline()), fill=255, width=lw(1.5, 2), joint="curve")
        glass = car.glass()
        if glass:
            d.line(pl.pts(glass + [glass[0]]), fill=255, width=lw(1.1, 2), joint="curve")
        for poly in (car.wing or ()):
            d.line(pl.pts(poly + [poly[0]]), fill=255, width=lw(1.1, 2), joint="curve")
        for cx, cy, r in car.wheels():
            _wheel(mask, pl, cx, cy, r, outline_only=True)
        return mask

    d.polygon(pl.pts(car.outline()), fill=255)
    for poly in (car.wing or ()):
        d.polygon(pl.pts(poly), fill=255)
    if car.mirror:
        d.polygon(pl.pts(car.mirror), fill=255)

    glass = car.glass()
    if glass:
        d.polygon(pl.pts(glass), fill=0)
    pillar = car.pillar()
    if pillar:
        d.polygon(pl.pts(pillar), fill=255)

    for shape in car.cutouts():
        d.polygon(pl.pts(shape), fill=0)
    if car.lamp:
        lx, ly, rx, ry = car.lamp
        c = pl.pt((lx, ly))
        ax, ay = pl.u(rx), pl.u(ry)
        d.ellipse([c[0] - ax, c[1] - ay, c[0] + ax, c[1] + ay], fill=0)
    for line in car.shut_lines():
        d.line(pl.pts(line), fill=0, width=lw(1.1, 2))

    for cx, cy, r in car.wheels():
        _wheel(mask, pl, cx, cy, r)
    return mask


def white_from_mask(mask, w, h):
    """Turn a coverage mask into a white RGBA image at final resolution."""
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    img.putalpha(down(mask, w, h))
    return img


def render_car(car, outline_only=False):
    """Cars are modelled nose-right and mirrored on output, so they face left."""
    _, _, bw, bh = CAR_BOX
    mask = car_mask(car, bw, bh, outline_only).transpose(Image.FLIP_LEFT_RIGHT)
    return white_from_mask(mask, bw, bh)


# ==================================================================== bezel ==
def render_bezel():
    """Minute track: hairline minors, weighted majors, small light numerals."""
    W = SIZE * S
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    c = px(SIZE / 2.0)

    for i in range(60):
        a = math.radians(i * 6 - 90)
        quarter, major = i % 15 == 0, i % 5 == 0
        r0 = px(239)
        r1 = px(224 if quarter else 228 if major else 233)
        col = ((242, 246, 254, 225) if quarter
               else (214, 222, 238, 165) if major
               else (128, 140, 162, 85))
        d.line([(c + r0 * math.cos(a), c + r0 * math.sin(a)),
                (c + r1 * math.cos(a), c + r1 * math.sin(a))],
               fill=col, width=lw(2.2 if quarter else 1.6 if major else 0.9))

    f = font("saira_condensed_medium.ttf", px(18))
    for i in range(12):
        n = 60 if i == 0 else i * 5
        a = math.radians(i * 30 - 90)
        r = px(210)
        d.text((c + r * math.cos(a), c + r * math.sin(a)), str(n), font=f,
               fill=(214, 224, 242, 210) if i % 3 else (240, 246, 255, 240),
               anchor="mm")

    return down(img, SIZE, SIZE)


def circle_mask(r=SIZE / 2.0, feather=0.9, n=SIZE):
    yy, xx = np.mgrid[0:n, 0:n]
    dist = np.sqrt((xx + 0.5 - n / 2.0) ** 2 + (yy + 0.5 - n / 2.0) ** 2)
    return Image.fromarray((np.clip((r - dist) / feather, 0, 1) * 255).astype(np.uint8), "L")


def render_backdrop():
    """Flat black with two hairlines - the only structure the dial needs."""
    W = SIZE * S
    img = Image.new("RGBA", (W, W), (0, 0, 0, 255))
    yy, _ = np.mgrid[0:W, 0:W]
    lift = np.clip(1 - (yy / W) * 1.6, 0, 1) ** 2
    layer = np.zeros((W, W, 4))
    layer[:, :, 0], layer[:, :, 1], layer[:, :, 2] = 18, 22, 32
    layer[:, :, 3] = lift * 190
    img.alpha_composite(Image.fromarray(layer.astype(np.uint8), "RGBA"))

    d = ImageDraw.Draw(img, "RGBA")
    c = px(SIZE / 2.0)
    r = px(202)
    d.ellipse([c - r, c - r, c + r, c + r], outline=(255, 255, 255, 16), width=lw(0.8))
    d.line([(px(104), px(248)), (px(376), px(248))], fill=(255, 255, 255, 26),
           width=lw(0.8))

    out = down(img, SIZE, SIZE)
    out.putalpha(circle_mask())
    return out


# ================================================================== preview ==
def tint(img, color):
    solid = Image.new("RGBA", img.size, color + (255,))
    solid.putalpha(img.split()[3])
    return solid


def stamp(base, fn):
    """Draw through a transparent layer.

    ImageDraw writes straight into an RGBA image - it replaces pixels rather
    than compositing - so anything drawn with a partial alpha has to go through
    its own layer to blend.
    """
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer, "RGBA"))
    base.alpha_composite(layer)


def render_preview(car_id="rear_engine", accent=ACCENT, time_color=WHITE,
                   ambient=False):
    """Approximates the live face; used for the store and editor preview."""
    img = (Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255)) if ambient
           else render_backdrop().convert("RGBA"))
    d = ImageDraw.Draw(img, "RGBA")

    f_lab = font("saira_condensed_medium.ttf", 14)
    f_badge = font("saira_condensed_bold.ttf", 20)
    f_val = font("dseg7_bold.ttf", 22)
    f_energy = font("dseg7_bold.ttf", 27)
    f_time = font("dseg7_bold.ttf", TIME_SIZE)
    f_unit = font("saira_condensed_semibold.ttf", 16)

    car = CARS.BY_ID[car_id]
    bx, by, _, _ = CAR_BOX
    x, y, w, h = BADGE

    if ambient:
        img.alpha_composite(tint(render_car(car, outline_only=True), accent), (bx, by))
        stamp(img, lambda dd: (
            dd.rounded_rectangle([x, y, x + w, y + h], radius=6,
                                 outline=accent + (170,), width=2),
            dd.text((x + w / 2, y + h / 2 + 1), "28", font=f_badge,
                    fill=accent + (190,), anchor="mm"),
            dd.text((240, TIME_Y), "88:88", font=f_time,
                    fill=(255, 255, 255, 22), anchor="mt")))
        d.text((240, TIME_Y), "21:47", font=f_time, fill=(206, 216, 234, 255), anchor="mt")
        img.putalpha(circle_mask())
        return img

    img.alpha_composite(render_bezel())

    d.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=accent + (255,))
    d.text((x + w / 2, y + h / 2 + 1), "28", font=f_badge, fill=INK + (255,), anchor="mm")

    d.text((228, ENERGY_BASELINE), "ENERGIA", font=f_lab, fill=MUTED + (255,), anchor="rs")
    d.text((240, ENERGY_BASELINE), "84", font=f_energy, fill=accent + (255,), anchor="ls")

    img.alpha_composite(tint(render_car(car), accent), (bx, by))

    for cx, (label, value, unit) in zip(COL_X, (("KROKI", "8432", ""),
                                                ("TEMP", "24", "\u00b0"),
                                                ("BATERIA", "86", "%"))):
        d.text((cx, ROW_Y), label, font=f_lab, fill=MUTED + (255,), anchor="mt")
        wv = d.textlength(value, font=f_val)
        wu = d.textlength(unit, font=f_unit) if unit else 0
        x0 = cx - (wv + wu) / 2
        d.text((x0, ROW_VALUE_Y), value, font=f_val, fill=WHITE + (255,), anchor="lt")
        if unit:
            d.text((x0 + wv + 1, ROW_VALUE_Y + 3), unit, font=f_unit,
                   fill=MUTED + (255,), anchor="lt")

    stamp(img, lambda dd: dd.text((240, TIME_Y), "88:88", font=f_time,
                                  fill=(255, 255, 255, 26), anchor="mt"))
    d.text((240, TIME_Y), "21:47", font=f_time, fill=time_color + (255,), anchor="mt")

    img.putalpha(circle_mask())
    return img


def contact_sheet():
    cols, rows = 2, 3
    bw, bh = CAR_BOX[2], CAR_BOX[3]
    sheet = Image.new("RGBA", (cols * (bw + 20), rows * (bh + 36)), (10, 12, 16, 255))
    d = ImageDraw.Draw(sheet)
    f = font("saira_condensed_semibold.ttf", 16)
    for i, car in enumerate(CARS.CARS):
        col, row = i % cols, i // cols
        x, y = col * (bw + 20) + 10, row * (bh + 36) + 26
        sheet.alpha_composite(tint(render_car(car), ACCENT), (x, y))
        d.text((x, y - 20), f"{car.id}   {car.length_mm}x{car.height_mm} mm",
               font=f, fill=(200, 208, 224, 255))
    return sheet


# ===================================================================== main ==
def main():
    os.makedirs(OUT, exist_ok=True)
    scratch = os.environ.get("SCRATCH", OUT)

    render_backdrop().save(os.path.join(OUT, "backdrop.png"))
    render_bezel().save(os.path.join(OUT, "bezel.png"))
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
