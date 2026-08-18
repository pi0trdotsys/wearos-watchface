"""Silhouette profiles for the six selectable cars.

Every profile is constructed from published dimensions - length, height,
wheelbase, front and rear overhang, tyre sizes, and the heights of the roof,
waistline, wing crest and lamp centres - rather than traced from an image. No
badge, wordmark, crest or model name appears anywhere in the artwork.

Coordinate space per profile:
    x  0 .. 1000    0 = rear bumper, 1000 = nose
    y  0 .. height  0 = highest point, height = tyre contact patch

`height` is 1000 * real_height / real_length, so each car keeps its own stance.
Heights convert back to millimetres with

    mm = height_mm * (1 - y / height)

which is how every anchor point below was placed; the comments carry the
millimetre figure so the drawing stays checkable.

Front and rear tyres are sized separately. Staggered fitment is a large part of
why a rear-engined coupe reads the way it does in profile.
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


def arc(cx, cy, r, a0, a1, n=72):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


def wheel_arch(cx, cy, r, sill):
    """Arch cutout: enters and leaves at the sill line, bulging upward."""
    dy = sill - cy
    dx = math.sqrt(max(r * r - dy * dy, 1.0))
    a0 = math.degrees(math.atan2(dy, dx))
    return arc(cx, cy, r, a0, -(180 + a0))


def slot(x0, y0, x1, y1, h, skew=0.0):
    """A tapered horizontal slot - vents, lamp bars, intakes, exhausts."""
    return [(x0, y0), (x1, y1), (x1 + skew, y1 + h), (x0 + skew, y0 + h)]


class Car:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.wheel_fy = self.height - self.tyre_r_front
        self.wheel_ry = self.height - self.tyre_r_rear

    # -- body --------------------------------------------------------------
    def top(self):
        return build(self.top_spec)

    def outline(self):
        pts = self.top()
        pts.append((self.front_x + self.arch_f * 0.94, self.sill))
        pts += wheel_arch(self.front_x, self.wheel_fy, self.arch_f, self.sill)
        pts.append((self.rear_x + self.arch_r * 0.94, self.sill + self.sill_drop))
        pts += wheel_arch(self.rear_x, self.wheel_ry, self.arch_r,
                          self.sill + self.sill_drop)
        pts.append((self.tail_sill_x, self.sill + self.sill_drop - 2))
        pts.append(self.top_spec[0][1])
        return pts

    # -- glass, derived from the roof curve ---------------------------------
    def glass(self):
        """Roof curve pushed down by the pillar thickness, closed on the belt."""
        roof = [(x, min(y + self.glass_inset, self.belt)) for x, y in self.top()
                if self.glass_x0 <= x <= self.glass_x1]
        if len(roof) < 3:
            return []
        return [(roof[0][0], self.belt)] + roof + [(roof[-1][0], self.belt)]

    def _roof_y(self, x):
        best, bd = 0.0, 1e9
        for rx, ry in self.top():
            if abs(rx - x) < bd:
                best, bd = ry, abs(rx - x)
        return best

    def pillar(self):
        if self.pillar_x is None:
            return []
        x, w = self.pillar_x, self.pillar_w
        top = self._roof_y(x) + self.glass_inset
        return [(x - w / 2, top), (x + w / 2, top),
                (x + w / 2 + self.pillar_rake, self.belt + 1),
                (x - w / 2 + self.pillar_rake, self.belt + 1)]

    def shut_lines(self):
        return [[(x, self._roof_y(x) + self.glass_inset + 2), (x, self.sill - 7)]
                for x in self.shuts]

    def cutouts(self):
        """Every shape knocked out of the body, in draw order."""
        out = []
        for shape in (self.tail, self.handle, self.front_intake, self.exhaust):
            if shape:
                out.append(shape)
        for shape in (self.vents or ()):
            out.append(shape)
        return out

    # -- wheels -------------------------------------------------------------
    def wheels(self):
        """(cx, cy, tyre radius) for the front and rear wheels."""
        return ((self.front_x, self.wheel_fy, self.tyre_r_front),
                (self.rear_x, self.wheel_ry, self.tyre_r_rear))


_D = dict(pillar_w=8.0, pillar_rake=0.0, sill_drop=0.0, wing=None, lamp=None,
          tail=None, handle=None, mirror=None, vents=None, exhaust=None,
          front_intake=None, shuts=())


CARS = [
    # ======================================================================
    # 1. Rear-engined coupe.  4519 x 1300 mm, 2450 mm wheelbase,
    #    875 mm front / 1194 mm rear overhang, 245/35R20 and 305/30R21 tyres.
    #    Roof apex 1300, waistline 1015, scuttle 1040, wing crest 1050,
    #    lid trailing edge 1140, rear screen base 1180, nose 730 mm.
    # ======================================================================
    Car(**_D | dict(
        id="rear_engine", label="car_rear_engine", name="Rear-engine coupe",
        length_mm=4519, height_mm=1300, height=288.0,
        rear_x=264, front_x=806,
        tyre_r_front=75.1, tyre_r_rear=79.2,           # 679 mm / 716 mm
        arch_f=82.0, arch_r=86.5,                      # tight, low-profile fitment
        sill=242.0, sill_drop=1.0,                     # visible rocker edge
        belt=86.0, tail_sill_x=64,                     # waistline, 912 mm
        glass_x0=318, glass_x1=676, glass_inset=6,
        pillar_x=382, pillar_rake=-5, shuts=(376, 678),
        lamp=(902, 106, 21.0, 19.0),                   # round lamp set into the wing
        tail=slot(3, 72, 48, 66, 12),
        handle=slot(432, 100, 474, 98, 7),
        mirror=[(690, 48), (722, 41), (732, 46), (728, 56), (696, 59)],
        vents=[slot(318, 106, 380, 102, 8), slot(318, 118, 380, 114, 8),
               slot(392, 216, 700, 212, 5)],   # rocker line
        front_intake=slot(924, 164, 978, 158, 30),
        exhaust=slot(20, 214, 70, 211, 11),
        top_spec=[
            ('M', (56, 234)),
            ('C', (28, 228), (9, 212), (3, 186)),      # bumper tucks under
            ('C', (0, 152), (0, 104), (3, 76)),        # upright rear fascia
            ('C', (5, 60), (10, 51), (20, 47)),        # tail corner, 1088 mm
            ('C', (28, 46), (36, 45), (48, 44)),       # lid trailing edge
            ('C', (112, 37), (182, 30), (252, 25)),    # engine lid, rising
            ('C', (286, 22), (312, 20), (340, 17)),    # 1223 mm screen base
            ('C', (386, 10), (428, 4), (470, 2)),      # rear screen
            ('C', (494, 0), (518, 0), (540, 1)),       # short roof, 1300 mm
            ('C', (578, 6), (616, 20), (652, 38)),     # long raked windscreen
            ('C', (674, 48), (690, 54), (704, 57)),    # scuttle, 1040 mm
            ('C', (734, 58), (768, 56), (800, 55)),    # wing crest, 1050 mm
            ('C', (846, 57), (890, 68), (930, 88)),    # wings fall away
            ('C', (958, 100), (980, 118), (990, 142)),  # nose, 759 mm
            ('C', (996, 158), (998, 176), (993, 194)),
            ('L', (972, 230)),                          # splitter
        ])),

    # ======================================================================
    # 2. Front-engined wedge GT.  4520 x 1282 mm, 2500 mm wheelbase.
    # ======================================================================
    Car(**_D | dict(
        id="wedge", label="car_wedge", name="Wedge GT",
        length_mm=4520, height_mm=1282, height=284.0,
        rear_x=239, front_x=792,
        tyre_r_front=70.0, tyre_r_rear=73.0,
        arch_f=78.0, arch_r=81.0,
        sill=254.0, belt=94.0, tail_sill_x=62,
        glass_x0=156, glass_x1=598, glass_inset=8,
        pillar_x=332, pillar_rake=-4, shuts=(326, 604),
        tail=slot(4, 96, 58, 92, 14),
        handle=slot(416, 108, 458, 106, 7),
        mirror=[(596, 82), (636, 72), (650, 78), (646, 90), (604, 94)],
        vents=[slot(196, 74, 258, 70, 7)],
        front_intake=slot(896, 200, 972, 194, 30),
        exhaust=slot(24, 226, 78, 223, 13),
        top_spec=[
            ('M', (44, 240)),
            ('C', (18, 232), (4, 214), (2, 188)),
            ('C', (1, 154), (3, 124), (10, 102)),
            ('C', (16, 86), (28, 74), (46, 66)),
            ('C', (108, 46), (176, 30), (248, 20)),
            ('C', (306, 12), (362, 7), (416, 6)),
            ('C', (446, 6), (472, 9), (494, 16)),
            ('C', (534, 29), (570, 48), (602, 70)),
            ('C', (622, 82), (646, 90), (674, 94)),
            ('C', (742, 100), (812, 108), (872, 120)),
            ('C', (914, 130), (950, 144), (974, 162)),
            ('C', (988, 174), (994, 190), (992, 208)),
            ('L', (972, 242)),
        ])),

    # ======================================================================
    # 3. Mid-engined wedge.  4430 x 1130 mm, 2450 mm wheelbase, rear wing.
    # ======================================================================
    Car(**_D | dict(
        id="mid_engine", label="car_mid_engine", name="Mid-engine wedge",
        length_mm=4430, height_mm=1130, height=255.0,
        rear_x=262, front_x=815,
        tyre_r_front=72.0, tyre_r_rear=78.0,
        arch_f=79.0, arch_r=86.0,
        sill=226.0, belt=84.0, tail_sill_x=56,
        glass_x0=352, glass_x1=690, glass_inset=8,
        pillar_x=None, shuts=(700,),
        tail=slot(4, 78, 52, 74, 12),
        handle=slot(470, 96, 512, 94, 7),
        mirror=[(694, 66), (734, 56), (748, 62), (744, 74), (702, 78)],
        vents=[slot(306, 100, 396, 92, 12, skew=-8), slot(122, 60, 214, 56, 7)],
        front_intake=slot(902, 168, 972, 162, 30),
        exhaust=slot(20, 194, 74, 191, 13),
        wing=[[(16, 28), (242, 16), (244, 36), (18, 48)],
              [(40, 42), (56, 41), (62, 96), (46, 97)],
              [(204, 30), (220, 29), (226, 92), (210, 93)]],
        top_spec=[
            ('M', (52, 214)),
            ('C', (24, 208), (8, 194), (4, 172)),
            ('C', (2, 146), (4, 116), (10, 94)),
            ('C', (14, 82), (22, 76), (36, 74)),
            ('C', (96, 68), (168, 62), (236, 56)),
            ('C', (280, 52), (312, 46), (340, 40)),
            ('C', (378, 30), (414, 21), (452, 16)),
            ('C', (484, 12), (514, 11), (540, 12)),
            ('C', (566, 13), (590, 16), (610, 22)),
            ('C', (642, 32), (672, 48), (698, 68)),
            ('C', (712, 78), (726, 84), (742, 86)),
            ('C', (786, 88), (836, 94), (880, 106)),
            ('C', (924, 118), (958, 134), (980, 154)),
            ('C', (992, 166), (996, 180), (992, 196)),
            ('L', (970, 218)),
        ])),

    # ======================================================================
    # 4. Long-nose front-engined GT.  4650 x 1270 mm, 2720 mm wheelbase.
    # ======================================================================
    Car(**_D | dict(
        id="front_gt", label="car_front_gt", name="Long-nose GT",
        length_mm=4650, height_mm=1270, height=273.0,
        rear_x=221, front_x=806,
        tyre_r_front=73.0, tyre_r_rear=76.0,
        arch_f=80.0, arch_r=84.0,
        sill=244.0, belt=88.0, tail_sill_x=50,
        glass_x0=308, glass_x1=688, glass_inset=8,
        pillar_x=398, pillar_rake=-5, shuts=(392, 694),
        lamp=(890, 116, 20.0, 16.0),
        tail=slot(4, 92, 56, 88, 13),
        handle=slot(496, 102, 538, 100, 7),
        mirror=[(680, 74), (720, 64), (734, 70), (730, 82), (688, 86)],
        vents=[slot(760, 96, 828, 92, 8)],
        front_intake=slot(908, 176, 976, 170, 32),
        exhaust=slot(20, 216, 76, 213, 13),
        top_spec=[
            ('M', (34, 236)),
            ('C', (12, 228), (2, 210), (2, 184)),
            ('C', (2, 152), (4, 124), (10, 102)),
            ('C', (14, 88), (22, 78), (36, 72)),
            ('C', (80, 56), (134, 44), (190, 36)),
            ('C', (232, 30), (268, 26), (302, 23)),
            ('C', (346, 17), (392, 12), (438, 10)),
            ('C', (470, 9), (500, 11), (526, 16)),
            ('C', (562, 24), (596, 40), (626, 60)),
            ('C', (644, 72), (662, 78), (682, 80)),
            ('C', (752, 82), (826, 88), (886, 102)),
            ('C', (926, 112), (958, 128), (978, 150)),
            ('C', (990, 164), (995, 182), (992, 202)),
            ('L', (972, 238)),
        ])),

    # ======================================================================
    # 5. Hypercar.  4700 x 1110 mm, 2710 mm wheelbase, active rear wing.
    # ======================================================================
    Car(**_D | dict(
        id="hyper", label="car_hyper", name="Hypercar",
        length_mm=4700, height_mm=1110, height=236.0,
        rear_x=232, front_x=809,
        tyre_r_front=68.0, tyre_r_rear=74.0,
        arch_f=75.0, arch_r=82.0,
        sill=208.0, belt=84.0, tail_sill_x=52,
        glass_x0=344, glass_x1=652, glass_inset=7,
        pillar_x=None, shuts=(664,),
        tail=slot(4, 74, 48, 70, 11),
        mirror=[(656, 62), (696, 52), (710, 58), (706, 70), (664, 74)],
        vents=[slot(292, 96, 372, 88, 12, skew=-8), slot(118, 62, 200, 58, 7)],
        front_intake=slot(906, 156, 972, 150, 28),
        exhaust=slot(18, 178, 70, 175, 12),
        wing=[[(10, 20), (202, 8), (204, 28), (12, 40)],
              [(32, 34), (48, 33), (54, 96), (38, 97)],
              [(166, 24), (182, 23), (188, 90), (172, 91)]],
        top_spec=[
            ('M', (58, 196)),
            ('C', (28, 190), (10, 176), (4, 156)),
            ('C', (2, 134), (4, 112), (10, 94)),
            ('C', (14, 84), (22, 80), (34, 78)),
            ('C', (90, 74), (156, 70), (218, 64)),
            ('C', (268, 58), (312, 48), (352, 34)),
            ('C', (392, 22), (430, 14), (470, 11)),
            ('C', (498, 10), (524, 12), (546, 17)),
            ('C', (588, 27), (626, 46), (658, 70)),
            ('C', (676, 82), (696, 88), (718, 90)),
            ('C', (776, 92), (838, 98), (888, 110)),
            ('C', (930, 120), (962, 136), (982, 156)),
            ('C', (992, 168), (996, 182), (992, 196)),
            ('L', (966, 218)),
        ])),

    # ======================================================================
    # 6. Sixties racing coupe.  4325 x 1210 mm, 2400 mm wheelbase.
    # ======================================================================
    Car(**_D | dict(
        id="classic", label="car_classic", name="Sixties racer",
        length_mm=4325, height_mm=1210, height=280.0,
        rear_x=253, front_x=808,
        tyre_r_front=74.0, tyre_r_rear=78.0,
        arch_f=82.0, arch_r=86.0,
        sill=248.0, belt=94.0, tail_sill_x=60,
        glass_x0=290, glass_x1=590, glass_inset=8,
        pillar_x=374, pillar_rake=-4, shuts=(368, 596),
        lamp=(884, 122, 19.0, 17.0),
        tail=slot(6, 104, 46, 100, 13),
        handle=slot(448, 110, 486, 108, 7),
        mirror=[(596, 78), (628, 70), (640, 76), (636, 86), (602, 90)],
        vents=[slot(716, 108, 782, 104, 8), slot(716, 120, 782, 116, 8)],
        front_intake=slot(902, 186, 962, 180, 30),
        exhaust=slot(24, 220, 72, 217, 12),
        top_spec=[
            ('M', (44, 244)),
            ('C', (16, 236), (2, 216), (2, 190)),
            ('C', (2, 158), (5, 128), (12, 106)),
            ('C', (18, 90), (26, 82), (40, 78)),
            ('C', (86, 68), (136, 60), (186, 54)),
            ('C', (222, 49), (252, 44), (280, 38)),
            ('C', (322, 28), (364, 20), (406, 16)),
            ('C', (434, 14), (462, 15), (486, 19)),
            ('C', (520, 26), (552, 40), (580, 60)),
            ('C', (598, 72), (618, 80), (640, 84)),
            ('C', (700, 88), (770, 90), (830, 96)),
            ('C', (884, 102), (930, 116), (962, 140)),
            ('C', (980, 154), (990, 174), (988, 196)),
            ('L', (966, 240)),
        ])),
]

BY_ID = {c.id: c for c in CARS}
