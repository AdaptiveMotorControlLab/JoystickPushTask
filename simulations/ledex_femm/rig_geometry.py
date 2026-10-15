"""Measured rig geometry: one source of truth for the joystick, holder, constrainer, washers and Ledex.

    python rig_geometry.py      # prints the stack-up, writes results/rig/stackup.csv

World frame (all models and the rig explorer): X along the push (+X away from the mouse), Y lateral, Z up from
the breadboard top, origin under the joystick axis. The lever models (lever.py, plunger_link.py, rig_forces.py)
use x = X and z = height above the shaft base (Z - SHAFT_BASE), with the pivot at z = -d_p.

Measured from the CAD in mechanical/3d-print (joystick-holder, joystick-component, joystick, joystick-handle-cube,
joystick-1d-axis-constrainer):
- Holder: base 86 x 31.8 x 5 mm (long side along Y), corner posts, top frame z 20.41-25.41 with a 25.3 mm hole.
- Component: body 25.3 mm dia x 11.53 mm drops through the hole, flange (29.75 mm) rests on the frame -> body
  bottom at Z 13.88; stub top at component z 29.3.
- Shaft: 5 mm bore 2.7 mm deep on the stub -> shaft base at Z 40.48; cone r 4 -> 1.5 over 12 mm; 89 mm long.
- Cube handle: middle hole, push face 5.75 mm from the shaft axis, contact at shaft z 92.4 (cube z 87.4-97.4).
- Constrainer: lower 10 mm is a socket (inner 32 mm) over the frame -> spans Z 15.41-71.41; walls 6 mm above the
  socket (inner +-13); top plate Z 68.41-71.41 with the 4 mm slot from X -2 to 17; home wall has an arch 16 mm wide
  (straight to Z 55.41, radius 8, top Z 63.41).
- Pivot: inside the body, not modelled; mid-body (component z 5.77) by default, component z 2-10 tested.
"""
import csv
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CAD = os.path.join(ROOT, "mechanical", "3d-print")
OUT_RES = os.path.join(HERE, "results", "rig")

# ------------------------------------------------------------------ joystick holder and component
HOLDER_BASE_T = 5.0
HOLDER_TOP = 25.41
HOLDER_SQUARE = 31.82
HOLDER_BASE = (86.0, 31.82)          # along Y, along X
COMP_BODY_H, COMP_BODY_D, COMP_FLANGE_D, COMP_TOP = 11.53, 25.3, 29.75, 29.3
COMP_Z0 = HOLDER_TOP - COMP_BODY_H   # body bottom above the breadboard

# ------------------------------------------------------------------ shaft and cube (lever coordinates)
SHAFT_BORE = 2.7
SHAFT_BASE = COMP_Z0 + COMP_TOP - SHAFT_BORE
SHAFT_LEN = 89.0
SHAFT_R = 1.5
SHAFT_CONE = ((0.0, 4.0), (12.0, 1.5))   # (z, r) on the shaft
CUBE_Z = (87.4, 97.4)
HANDLE_Z = sum(CUBE_Z) / 2
HOLES = (("hole y 0.55", 2.05), ("hole y 4.25", 5.75), ("hole y 7.95", 9.45))  # (name, push-face offset mm)
FACE = HOLES[1][1]

# ------------------------------------------------------------------ pivot
PIVOT_COMP_Z = COMP_BODY_H / 2
PIVOT_COMP_RANGE = (2.0, 10.0)
PIVOT_DEPTH = round(SHAFT_BASE - (COMP_Z0 + PIVOT_COMP_Z), 3)
PIVOT_DEPTHS = tuple(round(SHAFT_BASE - (COMP_Z0 + z), 3) for z in (PIVOT_COMP_RANGE[1], PIVOT_COMP_Z,
                                                                       PIVOT_COMP_RANGE[0]))   # low / mid / high

# ------------------------------------------------------------------ constrainer
CON_Z0 = HOLDER_TOP - 10.0
CON_OUTER, CON_INNER_SOCKET, CON_INNER = 19.0, 16.0, 13.0
CON_TOP = (CON_Z0 + 53.0, CON_Z0 + 56.0)
SLOT = (-2.0, 17.0)
SLOT_W = 4.0
SLOT_Z = sum(CON_TOP) / 2 - SHAFT_BASE        # slot mid-plane on the shaft (lever z)
SLOT_HOME_X = SLOT[0] + SHAFT_R               # shaft centre at the home stop (X at the slot)
SLOT_FAR_X = SLOT[1] - SHAFT_R
ARCH_HALF_W, ARCH_R = 8.0, 8.0
ARCH_SPRING = CON_Z0 + 40.0                   # straight sides end, semicircle centre (world Z)
ARCH_TOP = ARCH_SPRING + ARCH_R
ARCH_BOTTOM = HOLDER_TOP                      # the holder frame fills the arch below this

# ------------------------------------------------------------------ washers (target option)
WASHER_RI, WASHER_RO, WASHER_T, N_WASHERS = 1.6, 4.5, 0.8, 10
WASHER_SEAT = 11.5                            # shaft z where the cone radius equals WASHER_RI

# ------------------------------------------------------------------ Ledex 195224-230 (datasheet)
LEDEX = dict(case_r=9.78, case_len=39.37, boss_r=7.0, boss_len=9.52, plunger_r=3.91, protrude=23.81,
             tip_slot_w=2.5, tip_slot_d=9.5, plunger_g=20.1)
NUT_T = 3.5                                   # M14 x 1.5 thin mounting nut (assumed; check the supplied nut)
PLATE_T = 5.0                                 # carriage plate the boss passes through
CLEARANCE = 1.0                               # minimum gap kept between moving or adjustable parts and the CAD

# ------------------------------------------------------------------ plunger link (collar on the 3 mm shaft)
ATTACH_R = 5.0                                # collar pin from the shaft axis, home side (room for a printed collar)
LINK = 10.0                                   # pin-to-pin link length
PIN_FROM_TIP = 3.0                            # cross pin in the plunger's pull-end slot, from the tip (to confirm)
COLLAR_H = 6.0
LINK_Z_MIN = SHAFT_CONE[1][0] + COLLAR_H / 2  # collar (pin at its mid-height) on the straight 3 mm part of the shaft
LINK_Z_MAX = ARCH_SPRING + ARCH_R - LEDEX["plunger_r"] - CLEARANCE - SHAFT_BASE   # plunger passes under the arch top


def world_z(z_shaft):
    return np.asarray(z_shaft) + SHAFT_BASE


def shaft_z(z_world):
    return np.asarray(z_world) - SHAFT_BASE


def rotate(px, pz, d_p, th):
    """Point (px, pz) of the rigid shaft (lever coordinates) after a tilt th (rad) toward +x about (0, -d_p)."""
    h = pz + d_p
    return px * np.cos(th) + h * np.sin(th), -d_p - px * np.sin(th) + h * np.cos(th)


def tilt_for_push(push, d_p, face=FACE):
    """Tilt that moves the push-face point at cube mid-height forward by push (mm, may be negative); exact."""
    th = np.linspace(np.radians(-10), np.radians(35), 45001)
    x, _ = rotate(-face, HANDLE_Z, d_p, th)
    x0, _ = rotate(-face, HANDLE_Z, d_p, 0.0)
    return np.interp(push, x - x0, th)


def push_for_tilt(th, d_p, face=FACE):
    x, _ = rotate(-face, HANDLE_Z, d_p, th)
    x0, _ = rotate(-face, HANDLE_Z, d_p, 0.0)
    return x - x0


def stop_push(d_p, slot_home_x=SLOT_HOME_X):
    """Push at the cube (relative to the vertical shaft) where the shaft touches the slot's home end."""
    th = np.arcsin(slot_home_x / (SLOT_Z + d_p))
    return float(push_for_tilt(th, d_p))


def max_push(d_p):
    th = np.arcsin(SLOT_FAR_X / (SLOT_Z + d_p))
    return float(push_for_tilt(th, d_p))


def shaft_radius(z):
    (z0, r0), (z1, r1) = SHAFT_CONE
    return np.interp(z, [z0, z1, SHAFT_LEN], [r0, r1, r1])


def arch_clear(z_axis, r):
    """True where a disc of radius r centred on the axis (Y = 0, world Z z_axis) passes through the arch."""
    z_axis = np.asarray(z_axis, float)
    return (r <= ARCH_HALF_W) & (z_axis - r >= ARCH_BOTTOM) & (z_axis <= ARCH_SPRING + ARCH_R - r)


# ------------------------------------------------------------------ CAD meshes
def read_stl(path):
    """Triangles (n, 3, 3) from an ASCII or binary STL."""
    b = open(path, "rb").read()
    if b[:5] == b"solid" and b"facet" in b[:400]:
        v = [list(map(float, l.split()[1:4])) for l in b.decode(errors="ignore").splitlines()
             if l.strip().startswith("vertex")]
        return np.array(v).reshape(-1, 3, 3)
    n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(float)


def _swap(t, dx=0.0, dz=0.0):
    """STL (x, y, z) -> world (y + dx, -x, z + dz): the parts' own y axis is the push axis."""
    return np.stack([t[..., 1] + dx, -t[..., 0], t[..., 2] + dz], axis=-1)


# name: (file under CAD, mapping to world at the vertical shaft, moves with the shaft)
PARTS = {
    "holder": ("joystick-holder/joystick_holder.stl", lambda t: _swap(t), False),
    "component": ("joystick-component/joystick_component.stl", lambda t: _swap(t, dz=COMP_Z0), False),
    "constrainer": ("joystick-1d-axis-constrainer/joystick_1d_axis_constrainer_38x38x56.stl",
                    lambda t: _swap(t, dz=CON_Z0), False),
    "shaft": ("joystick/joystick_89mm.stl", lambda t: t + np.array([0.0, 0.0, SHAFT_BASE]), True),
    "cube": ("joystick-handle-cube/joystick_handle_cube.stl",
             lambda t: _swap(t, dx=-4.25, dz=88.9 + SHAFT_BASE), True),
}


def part_mesh(name):
    rel, f, _ = PARTS[name]
    return f(read_stl(os.path.join(CAD, rel)))


def tilt_world(t, d_p, th):
    """Rotate world triangles of a shaft-mounted part by th about the pivot axis (along Y)."""
    x, z = rotate(t[..., 0], t[..., 2] - SHAFT_BASE, d_p, th)
    return np.stack([x, t[..., 1], z + SHAFT_BASE], axis=-1)


def slice_mesh(t, axis, value):
    """Segments (m, 2, 3) where the plane coord[axis] = value cuts the triangles."""
    d = t[:, :, axis] - value
    out = []
    for tri, dd in zip(t, d):
        if (dd > 0).all() or (dd < 0).all():
            continue
        pts = []
        for i in range(3):
            j = (i + 1) % 3
            if dd[i] == 0:
                pts.append(tri[i])
            elif dd[i] * dd[j] < 0:
                pts.append(tri[i] + dd[i] / (dd[i] - dd[j]) * (tri[j] - tri[i]))
        if len(pts) >= 2:
            out.append(pts[:2])
    return np.array(out).reshape(-1, 2, 3)


def stackup():
    d = PIVOT_DEPTH
    rows = [
        ("holder base top", HOLDER_BASE_T, "world Z"),
        ("holder frame top (component flange seat)", HOLDER_TOP, "world Z"),
        ("component body bottom", COMP_Z0, "world Z"),
        ("pivot (mid-body; tested component z 2-10)", SHAFT_BASE - d, "world Z"),
        ("shaft base", SHAFT_BASE, "world Z"),
        ("constrainer bottom (socket ledge rests on the frame top)", CON_Z0, "world Z"),
        ("washer tower (10 x M3 on the cone)", world_z(WASHER_SEAT), "world Z, to %.2f" % world_z(WASHER_SEAT + 8)),
        ("arch top (home wall opening)", ARCH_TOP, "world Z"),
        ("constrainer slot plate", CON_TOP[0], "world Z, to %.2f" % CON_TOP[1]),
        ("cube push contact", world_z(HANDLE_Z), "world Z"),
        ("pivot depth below the shaft base", d, "mm (%.2f-%.2f)" % (PIVOT_DEPTHS[0], PIVOT_DEPTHS[2])),
        ("home stop at the cube (vs vertical shaft)", stop_push(d), "mm push"),
        ("slot limit at the cube", max_push(d), "mm push"),
        ("tilt for a 15 mm push", np.degrees(tilt_for_push(15.0, d)), "deg"),
    ]
    return rows


def main():
    os.makedirs(OUT_RES, exist_ok=True)
    rows = stackup()
    path = os.path.join(OUT_RES, "stackup.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "value_mm", "note"])
        for name, v, note in rows:
            w.writerow([name, "%.2f" % v, note])
    for name, v, note in rows:
        print("{:<46} {:8.2f}  {}".format(name, v, note))
    for name in PARTS:
        t = part_mesh(name).reshape(-1, 3)
        print("{:<12} X {:7.2f}..{:7.2f}  Y {:7.2f}..{:7.2f}  Z {:7.2f}..{:7.2f}".format(
            name, t[:, 0].min(), t[:, 0].max(), t[:, 1].min(), t[:, 1].max(), t[:, 2].min(), t[:, 2].max()))
    print("wrote", os.path.relpath(path, HERE))


if __name__ == "__main__":
    main()
