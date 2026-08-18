"""Silhouette profiles for the selectable cars.

Visual language matches the approved TypeScript mockups
(wear-os-car-mockups/src/components/watchface/CarSilhouette.tsx +
cars.ts): each car is one filled body path plus an optional thin
"detail" crease, wheels drawn generically by the renderer (tyre ring,
punched-out hub gap, hub, eight spokes) rather than per-car. Ambient
mode strokes the same body outline with no fill and draws a plain
circle per wheel - also handled generically, in tools/gen_art.py.

Body geometry differs from the mockup's own authoring approach in one
way: a car is specified as a `top_spec` (the roofline/hood/nose/tail,
from one wheel's sill point to the other's) plus a `sill` height and
per-wheel radius. `body()` then constructs the full closed silhouette
itself, sweeping a wheel-arch bulge into the underbody at each wheel so
the tyre always sits inside a matching cutout rather than floating
against a straight closing edge - the mistake a first pass at this made.

These are original silhouettes, proportioned to evoke a body style by
its defining stance (roofline height and set-back, wheelbase-to-overhang
ratio, waistline, nose/tail treatment, ride height). None traces a
photograph, and none carries a badge, wordmark or model-specific
ornament. The display name is descriptive only and never rendered on
the watch face itself - it appears solely in the watch face editor's
picker, exactly like the mockup's own `CarSpec.name` contract.

Coordinate space per profile: x 0..1000 (0 = tail, 1000 = nose),
y 0..height (0 = highest point, larger y = lower / closer to the ground).
"""

import math


def cubic(p0, p1, p2, p3, n=48):
    out = []
    for i in range(1, n + 1):
        t = i / n
        u = 1 - t
        out.append((
            u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1],
        ))
    return out


def build(spec):
    pts, cur = [], None
    for cmd in spec:
        if cmd[0] in ('M', 'L'):
            cur = cmd[1]
            pts.append(cur)
        else:
            seg = cubic(cur, cmd[1], cmd[2], cmd[3])
            pts.extend(seg)
            cur = seg[-1]
    return pts


def arc(cx, cy, r, a0, a1, n=56):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


def wheel_arch(cx, cy, r, sill):
    """Arch cutout: enters and leaves at the sill line, bulging upward
    over the wheel so the tyre always sits inside matching bodywork."""
    dy = sill - cy
    dx = math.sqrt(max(r * r - dy * dy, 1.0))
    a0 = math.degrees(math.atan2(dy, dx))
    return arc(cx, cy, r, a0, -(180 + a0))


class Car:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def top(self):
        return build(self.top_spec)

    def _sill_point(self, cx, cy, r, side):
        """Where a wheel arch of radius r meets the sill line, on the near
        (side=-1) or far (side=+1) edge of the wheel."""
        dx = math.sqrt(max(r * r - (self.sill - cy) ** 2, 1.0))
        return (cx + side * dx, self.sill)

    def body(self):
        """Rear sill point -> top() -> front sill point -> front arch
        (outer to inner) -> straight underbody -> rear arch (inner to
        outer, closing the loop). Explicit sill points at both joins, so
        the polygon never backtracks over itself regardless of how close
        `top_spec`'s own endpoints land - the mistake a first pass made,
        which showed up as wheels rendering detached from the body.
        """
        (rcx, rcy, rr), (fcx, fcy, fr) = self.wheels
        rr, fr = rr + self.arch_pad, fr + self.arch_pad
        r_outer = self._sill_point(rcx, rcy, rr, -1)
        r_inner = self._sill_point(rcx, rcy, rr, +1)
        f_outer = self._sill_point(fcx, fcy, fr, +1)
        f_inner = self._sill_point(fcx, fcy, fr, -1)

        pts = [r_outer] + self.top() + [f_outer]
        pts += wheel_arch(fcx, fcy, fr, self.sill)  # f_outer -> f_inner
        pts.append(r_inner)                          # flat underbody run
        pts += wheel_arch(rcx, rcy, rr, self.sill)  # r_inner -> r_outer
        return pts

    def details(self):
        """List of open polylines - hairline creases, never filled."""
        return [build(spec) for spec in (self.detail_specs or [])]


CARS = [
    # ======================================================================
    # Rear-engine coupe stance: short front overhang, long tail, shallow
    # greenhouse set well aft, roofline falling almost flat into the deck.
    Car(
        id="porsche_911", label="car_porsche_911", name="Porsche 911",
        sill=196.0, arch_pad=14.0,
        wheels=[(160.0, 168.0, 58.0), (800.0, 168.0, 58.0)],
        top_spec=[
            ('M', (66, 196)),
            ('C', (30, 190), (6, 176), (4, 150)),
            ('C', (2, 118), (4, 84), (12, 60)),
            ('C', (16, 47), (24, 39), (38, 35)),
            ('C', (86, 25), (142, 19), (194, 17)),
            ('C', (234, 16), (264, 18), (288, 22)),
            ('C', (342, 12), (402, 4), (460, 2)),
            ('C', (488, 1), (512, 2), (532, 5)),
            ('C', (574, 13), (616, 29), (652, 49)),
            ('C', (676, 59), (696, 64), (716, 65)),
            ('C', (744, 63), (770, 60), (794, 60)),
            ('C', (840, 62), (880, 73), (914, 93)),
            ('C', (946, 111), (968, 135), (980, 163)),
            ('C', (984, 174), (984, 184), (978, 194)),
            ('L', (940, 196)),
        ],
        detail_specs=[
            [('M', (298, 64)), ('C', (352, 38), (412, 20), (464, 14)),
             ('C', (502, 10), (538, 12), (570, 20)),
             ('C', (608, 30), (644, 46), (674, 64))],
            [('M', (548, 14)), ('L', (554, 64))],
        ]),

    # ======================================================================
    # Electric pickup stance: dead-flat wedge hood, one straight cabin
    # diagonal, a flat load bed at the tail, tall ride height.
    Car(
        id="cybertruck", label="car_cybertruck", name="Electric pickup",
        sill=196.0, arch_pad=12.0,
        wheels=[(210.0, 168.0, 62.0), (818.0, 168.0, 62.0)],
        top_spec=[
            ('M', (18, 196)),
            ('L', (14, 108)),
            ('L', (60, 108)),
            ('L', (170, 58)),
            ('L', (452, 58)),
            ('L', (486, 96)),
            ('L', (918, 96)),
            ('L', (974, 132)),
            ('L', (982, 190)),
            ('L', (952, 196)),
        ],
        detail_specs=[
            [('M', (60, 108)), ('L', (486, 96))],
            [('M', (170, 58)), ('L', (452, 58))],
        ]),

    # ======================================================================
    # American muscle coupe stance: long, flat, high rear deck; short front
    # overhang; a wide, low, near-horizontal beltline the roof sits on top of.
    Car(
        id="challenger", label="car_challenger", name="American muscle coupe",
        sill=192.0, arch_pad=14.0,
        wheels=[(220.0, 164.0, 56.0), (784.0, 164.0, 56.0)],
        top_spec=[
            ('M', (56, 192)),
            ('C', (24, 186), (4, 172), (4, 150)),
            ('C', (4, 120), (10, 92), (22, 70)),
            ('C', (28, 57), (38, 50), (54, 47)),
            ('C', (104, 38), (160, 35), (214, 36)),
            ('C', (240, 36), (258, 38), (272, 42)),
            ('L', (338, 42)),
            ('C', (378, 27), (428, 18), (476, 17)),
            ('C', (506, 17), (532, 20), (554, 26)),
            ('C', (586, 35), (614, 48), (636, 64)),
            ('L', (712, 68)),
            ('C', (758, 71), (802, 76), (842, 86)),
            ('C', (886, 97), (920, 114), (942, 137)),
            ('C', (958, 154), (966, 172), (962, 188)),
            ('L', (924, 192)),
        ],
        detail_specs=[
            [('M', (340, 43)), ('C', (380, 29), (428, 20), (476, 19)),
             ('C', (506, 19), (532, 22), (554, 28)),
             ('C', (586, 37), (612, 49), (632, 64))],
        ]),

    # ======================================================================
    # American pony coupe stance: longer, lower hood than the muscle coupe,
    # a proper fastback roof sloping into a short decklid, lower waist.
    Car(
        id="mustang", label="car_mustang", name="American pony coupe",
        sill=188.0, arch_pad=14.0,
        wheels=[(212.0, 162.0, 54.0), (792.0, 162.0, 54.0)],
        top_spec=[
            ('M', (48, 188)),
            ('C', (18, 182), (2, 168), (2, 148)),
            ('C', (2, 122), (7, 98), (18, 78)),
            ('C', (24, 65), (34, 57), (50, 53)),
            ('C', (94, 44), (144, 40), (192, 41)),
            ('C', (210, 41), (226, 43), (240, 46)),
            ('C', (270, 30), (312, 19), (360, 15)),
            ('C', (394, 12), (426, 14), (454, 21)),
            ('C', (496, 31), (536, 47), (570, 68)),
            ('L', (686, 72)),
            ('C', (738, 75), (788, 81), (832, 92)),
            ('C', (878, 104), (914, 122), (936, 145)),
            ('C', (952, 162), (958, 178), (954, 194)),
            ('L', (916, 196)),
        ],
        detail_specs=[
            [('M', (242, 47)), ('C', (272, 32), (312, 22), (358, 18)),
             ('C', (392, 15), (424, 17), (452, 24)),
             ('C', (494, 34), (532, 49), (564, 68))],
        ]),

    # ======================================================================
    # British grand tourer stance: very long bonnet, low formal 2+2 roof set
    # well aft of the front axle, restrained curvature, big wheels.
    Car(
        id="continental_gt", label="car_continental_gt", name="British grand tourer",
        sill=186.0, arch_pad=14.0,
        wheels=[(228.0, 160.0, 54.0), (808.0, 160.0, 54.0)],
        top_spec=[
            ('M', (56, 186)),
            ('C', (22, 180), (4, 164), (4, 144)),
            ('C', (4, 120), (8, 98), (18, 80)),
            ('C', (25, 66), (36, 58), (52, 54)),
            ('C', (90, 46), (130, 43), (168, 43)),
            ('C', (202, 34), (242, 28), (284, 27)),
            ('C', (314, 26), (340, 29), (362, 35)),
            ('C', (396, 44), (426, 57), (450, 74)),
            ('L', (478, 76)),
            ('C', (540, 62), (608, 55), (674, 56)),
            ('C', (720, 56), (762, 63), (800, 76)),
            ('C', (848, 92), (886, 111), (910, 135)),
            ('C', (926, 152), (932, 168), (926, 184)),
            ('L', (888, 188)),
        ],
        detail_specs=[
            [('M', (170, 44)), ('C', (204, 35), (242, 29), (284, 28)),
             ('C', (314, 27), (340, 30), (362, 36)),
             ('C', (396, 45), (426, 58), (448, 75))],
            [('M', (478, 76)), ('C', (540, 63), (608, 56), (674, 57))],
        ]),

    # ======================================================================
    # Compact city hatch stance: very short wheelbase, tall bubble roof set
    # nearly centred, stubby overhangs, chunky wheels relative to the body.
    Car(
        id="mini", label="car_mini", name="Compact city hatch",
        sill=196.0, arch_pad=14.0,
        wheels=[(180.0, 168.0, 54.0), (470.0, 168.0, 54.0)],
        top_spec=[
            ('M', (46, 196)),
            ('C', (16, 190), (2, 174), (2, 150)),
            ('C', (2, 116), (12, 86), (30, 66)),
            ('C', (42, 52), (58, 42), (78, 37)),
            ('C', (114, 15), (160, 4), (208, 4)),
            ('C', (256, 4), (300, 15), (334, 37)),
            ('C', (354, 42), (370, 52), (382, 66)),
            ('C', (400, 74), (416, 86), (426, 102)),
            ('C', (440, 118), (444, 136), (440, 154)),
            ('L', (426, 196)),
        ],
        detail_specs=[
            [('M', (80, 38)), ('C', (116, 17), (160, 6), (208, 6)),
             ('C', (256, 6), (300, 17), (332, 38))],
            [('M', (284, 12)), ('L', (300, 66))],
        ]),

    # ======================================================================
    # Mid-engine hypercar stance: extremely low and wide, a very short
    # cabin set mid-body, dramatic horseshoe crease behind the door - the
    # single most recognisable line on this body.
    Car(
        id="chiron", label="car_chiron", name="Mid-engine hypercar",
        sill=170.0, arch_pad=13.0,
        wheels=[(226.0, 142.0, 52.0), (826.0, 142.0, 52.0)],
        top_spec=[
            ('M', (66, 170)),
            ('C', (28, 164), (6, 148), (4, 122)),
            ('C', (2, 100), (7, 82), (18, 68)),
            ('C', (24, 58), (34, 52), (48, 50)),
            ('C', (100, 44), (158, 42), (212, 42)),
            ('C', (256, 42), (296, 38), (328, 30)),
            ('C', (362, 21), (398, 16), (436, 15)),
            ('C', (464, 15), (490, 18), (514, 24)),
            ('C', (554, 34), (590, 52), (620, 74)),
            ('C', (636, 84), (654, 89), (674, 90)),
            ('C', (730, 92), (790, 98), (844, 110)),
            ('C', (888, 120), (924, 134), (946, 152)),
            ('C', (958, 162), (962, 172), (958, 182)),
            ('L', (900, 184)),
        ],
        detail_specs=[
            [('M', (328, 68)), ('C', (358, 58), (394, 54), (426, 58)),
             ('C', (444, 78), (444, 104), (424, 122)),
             ('C', (394, 128), (358, 126), (332, 116))],
            [('M', (214, 43)), ('C', (256, 43), (296, 39), (328, 31))],
        ]),

    # ======================================================================
    # Boxy 4x4 off-roader stance: dead-flat roof, steep near-vertical
    # windscreen, flat vertical sides, minimal rounding, tall ride height.
    Car(
        id="g_wagen", label="car_g_wagen", name="Boxy 4x4 off-roader",
        sill=196.0, arch_pad=12.0,
        wheels=[(196.0, 168.0, 60.0), (760.0, 168.0, 60.0)],
        top_spec=[
            ('M', (62, 196)),
            ('L', (58, 84)),
            ('L', (82, 72)),
            ('L', (150, 42)),
            ('L', (206, 40)),
            ('L', (206, 78)),
            ('L', (846, 78)),
            ('L', (846, 40)),
            ('L', (886, 42)),
            ('C', (916, 48), (936, 62), (946, 84)),
            ('L', (950, 196)),
        ],
        detail_specs=[
            [('M', (206, 40)), ('L', (206, 78))],
            [('M', (846, 40)), ('L', (846, 78))],
            [('M', (58, 84)), ('L', (946, 84))],
            # spare-wheel disc on the tailgate
            [('M', (906, 156)), ('C', (906, 140), (920, 128), (934, 128)),
             ('C', (948, 128), (960, 140), (960, 156)),
             ('C', (960, 172), (948, 184), (934, 184)),
             ('C', (920, 184), (906, 172), (906, 156))],
        ]),
]

BY_ID = {c.id: c for c in CARS}
