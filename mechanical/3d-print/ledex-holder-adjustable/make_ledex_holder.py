"""Adjustable Ledex 195224-230 holder (base + upright + carriage), gauges and the plunger-link parts, as STEP + STL.

    /tmp/ngenv/bin/python make_ledex_holder.py          # writes the parts next to this file and checks clearances

Needs netgen (pip install ngsolve) and numpy/scipy; the rig geometry comes from
simulations/ledex_femm/rig_geometry.py. Frames (mm; X along the push, +X toward the joystick, Z up):
- carriage: X from the Ledex body face (the M14 boss side), Y lateral, Z from the Ledex axis.
- upright, base: X from the Ledex body face, Z from the breadboard top.
- gauges, collar, link: their own frames (see README).
Adjustments: distance (X) by the base's two M6 slots along X (33 mm travel, works on 25 mm and 1 inch grids);
lateral (Y) by the upright's two M4 slots on the base (+-12.75 mm); height (Z) by the carriage's two M3 screws in
the upright's vertical slots (Ledex axis 30-70 mm above the breadboard, tick every 1 mm).
"""
import os
import sys

import numpy as np
from netgen.occ import Axis, Box, Cylinder, Dir, OCCGeometry, Pnt, X, Y, Z
from netgen.meshing import MeshingStep

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "simulations", "ledex_femm"))
import rig_geometry as rg  # noqa: E402

LX = rg.LEDEX
BOSS_HOLE_R = 7.25            # M14 boss clearance
M3_R, M4_R, M6_SLOT_W = 1.7, 2.25, 7.0
M4_NUT_AF, M4_NUT_T = 7.3, 3.5
M6_HEAD_W, M6_HEAD_T = 11.5, 6.5
PLATE_T = rg.PLATE_T
CAR_HALF_H = 13.0             # carriage half-height (Z) around the axis
FLANGE_Y = (11.0, 15.0)       # carriage side flange, outside the case (r 9.78)
WALL_Y = (15.4, 20.4)         # upright wall
WALL_X = (-38.0, 6.0)
SCREW_X = (-5.0, -25.0)       # carriage screws through the upright slots
H_RANGE = (30.0, 70.0)        # Ledex axis height above the breadboard
BASE_T, FOOT_T = 10.0, 6.0
BASE_X, BASE_Y = (-40.0, 8.0), (-24.0, 24.0)
M6_SLOT_Y = 12.6              # two slots along X at Y +-12.6 (25 mm and 1 inch grids both fit in 7 mm slots)
M6_SLOT_X = (-36.0, 4.0)
NUT_X = (-25.0, -1.0)         # M4 nut pockets in the base (Y = 0), under the upright's lateral slots
FOOT_Y = (-22.0, 30.0)
LAT_SLOT = 12.75              # lateral travel either way
COLLAR_H, COLLAR_R, BORE_R = 6.0, 4.5, 1.55
PIN_R = rg.PIN_D / 2 + 0.05   # 2.5 mm pin (or M2.5 screw), as the plunger's 2.5/2.6 mm cross hole
LINK_T, LINK_W = 2.0, 5.0     # the plunger's tip slot is 2.5 +-0.3 mm wide
REF_DIR = os.path.join(HERE, "..", "ledex-195224-model")

LAYOUTS = {
    # plunger link at the highest link height, 3 mm stroke at neutral
    "link": dict(H=rg.SHAFT_BASE + 18.0, face=-rg.ATTACH_R - rg.LINK + rg.PIN_FROM_TIP - LX["protrude"] - 3.0),
    # washer tower centred on the axis, 1 mm gap at neutral
    "washers": dict(H=rg.world_z(rg.WASHER_SEAT + rg.N_WASHERS * rg.WASHER_T / 2),
                    face=-rg.WASHER_RO - 1.0 - LX["protrude"]),
}


def box(x0, x1, y0, y1, z0, z1):
    return Box(Pnt(x0, y0, z0), Pnt(x1, y1, z1))


def cyl(p, d, r, h):
    return Cylinder(Pnt(*p), Dir(*d), r=r, h=h)


def slot(p0, p1, r, axis, h):
    """Stadium slot from p0 to p1 (same plane), extruded h along axis ('x', 'y' or 'z' from p's coordinate)."""
    d = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
    s = cyl(p0, d, r, h) + cyl(p1, d, r, h)
    a, b = np.array(p0, float), np.array(p1, float)
    lo, hi = np.minimum(a, b), np.maximum(a, b)
    ax = "xyz".index(axis)
    lo_, hi_ = lo.copy(), hi.copy()
    for i in range(3):
        if i == ax:
            hi_[i] = lo[i] + h
        elif hi[i] - lo[i] < 1e-9:
            lo_[i] -= r
            hi_[i] += r
    return s + box(lo_[0], hi_[0], lo_[1], hi_[1], lo_[2], hi_[2])


def hex_prism(cx, cy, z0, af, h):
    s = box(cx - af / 2, cx + af / 2, cy - af, cy + af, z0, z0 + h)
    for ang in (60, 120):
        s = s * box(cx - af / 2, cx + af / 2, cy - af, cy + af, z0, z0 + h).Rotate(Axis(Pnt(cx, cy, 0), Z), ang)
    return s


# ------------------------------------------------------------------ parts
def carriage():
    h = CAR_HALF_H
    plate = box(0, PLATE_T, -16, FLANGE_Y[1], -h, h)
    flange = box(-30, PLATE_T, FLANGE_Y[0], FLANGE_Y[1], -h, h)
    cradle = box(-28, -20, -10, FLANGE_Y[1], -h, -6) - cyl((-40, 0, 0), (1, 0, 0), LX["case_r"] + 0.15, 40)
    s = plate + flange + cradle
    s = s - cyl((-1, 0, 0), (1, 0, 0), BOSS_HOLE_R, PLATE_T + 2)
    for x in SCREW_X:
        s = s - cyl((x, FLANGE_Y[0] - 1, 0), (0, 1, 0), M3_R, 10)
    notch = box(-31, -30, FLANGE_Y[0] - 1, FLANGE_Y[1] + 1, -0.6, 0.6).Rotate(Axis(Pnt(-30, 0, 0), Y), 45)
    return s - notch


def upright():
    x0, x1 = WALL_X
    z0 = BASE_T
    foot = box(x0, x1, FOOT_Y[0], FOOT_Y[1], z0, z0 + FOOT_T)
    top = H_RANGE[1] + CAR_HALF_H + 5
    wall = box(x0, x1, WALL_Y[0], WALL_Y[1], z0 + FOOT_T, top)
    s = foot + wall
    for xr in (x0, x1 - 4):                       # two ribs on the outside
        rib = box(xr, xr + 4, WALL_Y[1] - 1, FOOT_Y[1], z0 + FOOT_T, z0 + FOOT_T + 30)
        cut = box(xr - 1, xr + 5, WALL_Y[1], FOOT_Y[1] + 30, z0 + FOOT_T, z0 + FOOT_T + 60).Rotate(
            Axis(Pnt(0, WALL_Y[1], z0 + FOOT_T + 30), X), -np.degrees(np.arctan2(FOOT_Y[1] - WALL_Y[1], 30)))
        s = s + (rib - cut)
    for x in SCREW_X:                             # height slots (Ledex axis H_RANGE)
        s = s - slot((x, WALL_Y[0] - 1, H_RANGE[0]), (x, WALL_Y[0] - 1, H_RANGE[1]), M3_R, "y", 7)
    for x in NUT_X:                               # lateral slots onto the base's M4 nuts
        s = s - slot((x, -LAT_SLOT, z0 - 1), (x, LAT_SLOT, z0 - 1), M4_R, "z", FOOT_T + 2)
    for zt in np.arange(H_RANGE[0], H_RANGE[1] + 0.1, 1.0):   # height scale beside the carriage's rear edge
        k = int(round(zt))
        length = 5.5 if k % 10 == 0 else (3.5 if k % 5 == 0 else 2.0)
        s = s - box(-31.5 - length, -31.5, WALL_Y[0] - 1, WALL_Y[0] + 0.6, zt - 0.2, zt + 0.2)
    return s


def base():
    s = box(BASE_X[0], BASE_X[1], BASE_Y[0], BASE_Y[1], 0, BASE_T)
    for y in (-M6_SLOT_Y, M6_SLOT_Y):
        r = M6_SLOT_W / 2
        s = s - slot((M6_SLOT_X[0] + r, y, -1), (M6_SLOT_X[1] - r, y, -1), r, "z", BASE_T + 2)
        rh = M6_HEAD_W / 2
        s = s - slot((M6_SLOT_X[0] + r, y, BASE_T - M6_HEAD_T), (M6_SLOT_X[1] - r, y, BASE_T - M6_HEAD_T), rh, "z",
                     M6_HEAD_T + 1)
    for x in NUT_X:
        s = s - cyl((x, 0, -1), (0, 0, 1), M4_R, BASE_T + 2) - hex_prism(x, 0, -0.01, M4_NUT_AF, M4_NUT_T)
    return s


def gap_gauge(t, n):
    s = box(0, 40, 0, 15, 0, t)
    for i in range(n):
        s = s - box(30 - 3 * i, 31.5 - 3 * i, 13.5, 16, -1, t + 1)
    return s


def stroke_gauge(s0):
    """Fork against the boss front face; its far end is flush with the plunger tip at stroke s0."""
    length = LX["protrude"] - LX["boss_len"] + s0
    s = box(0, length, -9, 9, 0, 2.0) + box(-12, 0, -9, 9, 0, 2.0)
    s = s - box(-1, length + 1, -4.1, 4.1, -1, 3)
    for i in range(int(round(s0))):
        s = s - box(-10 + 2.5 * i, -9 + 2.5 * i, 7.5, 10, -1, 3)
    return s


def ledex_body():
    """Reference model (not for printing), Ledex frame: X from the body face, axis on X. Leads at the rear, down."""
    tpl = 1.58
    s = cyl((-LX["case_len"], 0, 0), (1, 0, 0), LX["case_r"], LX["case_len"])
    s = s + cyl((0, 0, 0), (1, 0, 0), LX["boss_r"], LX["boss_len"])
    s = s - cyl((-LX["case_len"] + tpl, 0, 0), (1, 0, 0), LX["plunger_r"] + 0.1, LX["case_len"] - tpl + LX["boss_len"] + 1)
    for y in (-1.2, 1.2):
        s = s + cyl((-LX["case_len"] + 2.5, y, -LX["case_r"] + 1), (0, 0, -1), 1.1, 15)
    return s


def ledex_plunger():
    """Reference plunger, seated (energised), Ledex frame; slot plane XZ, cross hole along Y."""
    lcyl, conel, _ = rg.plunger_dims()
    tip = LX["protrude"]
    rp, w = LX["plunger_r"], LX["tip_slot_w"]
    s = cyl((tip - lcyl, 0, 0), (1, 0, 0), rp, lcyl)
    s = s + cone_solid(tip - lcyl, conel, rp, LX["cone_flat_r"])
    s = s - box(tip - LX["tip_slot_d"], tip + 1, -w / 2, w / 2, -rp - 1, rp + 1)
    s = s - cyl((tip - LX["hole_from_tip"], -rp - 1, 0), (0, 1, 0), LX["hole_d"] / 2, 2 * rp + 2)
    return s


def cone_solid(x_base, length, r_base, r_apex):
    """Truncated cone along -X from x_base (radius r_base) to x_base - length (radius r_apex)."""
    from netgen.occ import Face, Wire, Segment, Pnt as P3
    pts = [P3(x_base, 0, 0), P3(x_base, 0, r_base), P3(x_base - length, 0, r_apex), P3(x_base - length, 0, 0)]
    w = Wire([Segment(pts[i], pts[(i + 1) % 4]) for i in range(4)])
    return Face(w).Revolve(Axis(Pnt(0, 0, 0), X), 360)


def collar():
    """Split collar for the 3 mm shaft; clevis pin ATTACH_R on the -X (home) side, axis along Y.
    The clamp ear points along +Y: on the +X side it would hit the constrainer's far wall near a 15 mm push."""
    h = COLLAR_H / 2
    s = cyl((0, 0, -h), (0, 0, 1), COLLAR_R, COLLAR_H)
    s = s + box(-3, 3, 2.5, 8.5, -h, h) + box(-rg.ATTACH_R - 3.5, -2.5, -3.5, 3.5, -h, h)
    s = s - cyl((0, 0, -h - 1), (0, 0, 1), BORE_R, COLLAR_H + 2)
    s = s - box(-0.4, 0.4, 0, 9, -h - 1, h + 1)
    s = s - cyl((-4, 6, 0), (1, 0, 0), 1.1, 8)
    s = s - box(-rg.ATTACH_R - 4, -3.2, -LINK_T / 2 - 0.15, LINK_T / 2 + 0.15, -h - 1, h + 1)
    s = s - cyl((-rg.ATTACH_R, -4, 0), (0, 1, 0), PIN_R, 8)
    return s


def link():
    L = rg.LINK
    s = box(0, L, -LINK_T / 2, LINK_T / 2, -LINK_W / 2, LINK_W / 2)
    s = s + cyl((0, -LINK_T / 2, 0), (0, 1, 0), LINK_W / 2, LINK_T) + cyl((L, -LINK_T / 2, 0), (0, 1, 0), LINK_W / 2, LINK_T)
    for x in (0, L):
        s = s - cyl((x, -2, 0), (0, 1, 0), PIN_R, 4)
    return s


PARTS = {
    "ledex_holder_carriage": carriage,
    "ledex_holder_upright": upright,
    "ledex_holder_base": base,
    "gap_gauge_0.5mm": lambda: gap_gauge(0.5, 1),
    "gap_gauge_1mm": lambda: gap_gauge(1.0, 2),
    "gap_gauge_2mm": lambda: gap_gauge(2.0, 3),
    "gap_gauge_3mm": lambda: gap_gauge(3.0, 4),
    "stroke_gauge_2mm": lambda: stroke_gauge(2.0),
    "stroke_gauge_3mm": lambda: stroke_gauge(3.0),
    "stroke_gauge_4mm": lambda: stroke_gauge(4.0),
    "link_collar": collar,
    "link_bar": link,
}
REFERENCE = {"ledex_body": ledex_body, "ledex_plunger": ledex_plunger}
PIN_LEN = 10.0                # plunger pin along Y; must stay inside the arch (+-8 mm)


# ------------------------------------------------------------------ export
def triangles(shape, maxh):
    m = OCCGeometry(shape).GenerateMesh(maxh=maxh, perfstepsend=MeshingStep.MESHSURFACE)
    P = np.array([p.p for p in m.Points()])
    F = np.array([[v.nr - 1 for v in el.vertices] for el in m.Elements2D()])
    T = P[F]
    vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6
    return T if vol > 0 else T[:, ::-1]


def write_stl(path, T):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(T), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    rec["n"], rec["v"] = n, T.reshape(-1, 9)
    with open(path, "wb") as f:
        f.write(b"Ledex holder, JoystickPushTask (make_ledex_holder.py)".ljust(80, b" "))
        f.write(np.uint32(len(T)).tobytes())
        f.write(rec.tobytes())


def placed(name, H, face):
    """World triangles of a holder part for a Ledex axis height H and body face at X = face."""
    T = rg.read_stl(os.path.join(HERE, name + ".stl"))
    dz = H if name == "ledex_holder_carriage" else 0.0
    return T + np.array([face, 0.0, dz])


def surface_points(T, step=0.6):
    """Points spread over the triangles (vertices, edge midpoints and centroids, subdivided to ~step)."""
    pts = [T.reshape(-1, 3), T.mean(axis=1)]
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    size = np.max(np.linalg.norm(np.stack([b - a, c - a]), axis=2), axis=0)
    k = int(np.clip(np.ceil(size.max() / step), 1, 12))
    for i in range(k + 1):
        for j in range(k + 1 - i):
            u, v = i / k, j / k
            sel = size > step
            pts.append(a[sel] + u * (b[sel] - a[sel]) + v * (c[sel] - a[sel]))
    return np.vstack(pts)


def crop(T, lo, hi):
    """Triangles with at least one vertex inside the box lo..hi (world mm)."""
    inside = ((T >= np.asarray(lo)) & (T <= np.asarray(hi))).all(axis=2).any(axis=1)
    return T[inside]


def clearance_report():
    from scipy.spatial import cKDTree
    rig = {n: crop(rg.part_mesh(n), (-80, -40, 0), (20, 40, 90)) for n in ("holder", "constrainer", "component")}
    trees = {n: cKDTree(surface_points(t)) for n, t in rig.items()}
    ok = True
    for lay, p in LAYOUTS.items():
        line = []
        for name in ("ledex_holder_carriage", "ledex_holder_upright", "ledex_holder_base"):
            pts = surface_points(placed(name, p["H"], p["face"]))
            d = min(trees[n].query(pts, distance_upper_bound=20.0)[0].min() for n in trees)
            line.append("{} {:.1f} mm".format(name.split("_")[-1], d))
            ok &= d >= rg.CLEARANCE
        nut_front = p["face"] + PLATE_T + rg.NUT_T
        line.append("nut front X {:.1f} (constrainer wall {:.0f})".format(nut_front, -rg.CON_OUTER))
        ok &= nut_front <= -rg.CON_OUTER - rg.CLEARANCE
        print("{:8s} axis Z {:.2f}, face X {:.2f}: ".format(lay, p["H"], p["face"]) + ", ".join(line))
    print("clearances OK" if ok else "CLEARANCE PROBLEM")
    return ok


def link_parts(push, H, face, d_p=rg.PIVOT_DEPTH):
    """World triangles of the moving link-layout parts at a push (mm at the cube, from neutral)."""
    import plunger_link as pl
    z_a = H - rg.SHAFT_BASE
    s0 = -rg.ATTACH_R - rg.LINK + rg.PIN_FROM_TIP - LX["protrude"] - face
    k = pl.kinematics(push, d_p, z_a, s0)
    th = np.radians(k["tilt_deg"][0])
    sx, sz, px = k["collar_x"][0], k["collar_z"][0], k["pin_x"][0]
    stroke = k["stroke_mm"][0]
    ref = lambda n: rg.read_stl(os.path.join(REF_DIR, n + ".stl"))
    out = {"plunger": ref("ledex_plunger") + np.array([face + stroke, 0, H])}
    pin = triangles(cyl((0, -PIN_LEN / 2, 0), (0, 1, 0), rg.PIN_D / 2, PIN_LEN), 0.4)
    out["pin"] = pin + np.array([px, 0, H])
    col = rg.read_stl(os.path.join(HERE, "link_collar.stl")) + np.array([0, 0, rg.SHAFT_BASE + z_a])
    out["collar"] = rg.tilt_world(col, d_p, th)
    out["shaft"] = rg.tilt_world(rg.part_mesh("shaft"), d_p, th)
    phi = np.arctan2(sz - z_a, sx - px)
    t = rg.read_stl(os.path.join(HERE, "link_bar.stl"))
    x, z = t[..., 0] * np.cos(phi) - t[..., 2] * np.sin(phi), t[..., 0] * np.sin(phi) + t[..., 2] * np.cos(phi)
    out["link"] = np.stack([x + px, t[..., 1], z + H], axis=-1)
    return out, stroke


def motion_report(lay="link", n=9):
    """Smallest gaps between the moving link parts and everything they must not touch, home stop to 15 mm."""
    from scipy.spatial import cKDTree
    p = LAYOUTS[lay]
    lo, hi = (-60, -20, p["H"] - 20), (15, 20, p["H"] + 20)
    fixed = {nm: crop(rg.part_mesh(nm), lo, hi) for nm in ("holder", "constrainer", "component")}
    fixed["ledex"] = rg.read_stl(os.path.join(REF_DIR, "ledex_body.stl")) + np.array([p["face"], 0, p["H"]])
    trees = {nm: cKDTree(surface_points(t, 0.5)) for nm, t in fixed.items() if len(t)}
    pairs = [("plunger", "collar"), ("plunger", "shaft"), ("pin", "collar"), ("pin", "shaft"), ("link", "shaft")]
    pushes = np.linspace(rg.stop_push(rg.PIVOT_DEPTH), 15.0, n)
    worst = {}
    for push in pushes:
        parts, stroke = link_parts(push, p["H"], p["face"])
        parts["shaft"] = crop(parts["shaft"], lo, hi)
        pts = {nm: surface_points(t, 0.4) for nm, t in parts.items()}
        for a, b in pairs:
            d = cKDTree(pts[b]).query(pts[a], distance_upper_bound=5.0)[0].min()
            worst[(a, b)] = min(worst.get((a, b), (np.inf,))[0], d), push
        for a in ("plunger", "pin", "link", "collar"):
            for b, tr in trees.items():
                if (a, b) == ("plunger", "ledex"):
                    continue
                d = tr.query(pts[a], distance_upper_bound=5.0)[0].min()
                if d < worst.get((a, b), (np.inf,))[0]:
                    worst[(a, b)] = d, push
    print("moving parts, push {:.2f} to 15 mm (smallest gap, at push):".format(pushes[0]))
    ok = True
    for (a, b), (d, at) in sorted(worst.items(), key=lambda kv: kv[1][0]):
        if np.isfinite(d):
            print("  {:8s} - {:12s} {:5.2f} mm at {:5.2f}".format(a, b, d, at))
        ok &= d >= 0.5
    print("  (all other pairs > 5 mm)")
    print("moving clearances OK" if ok else "MOVING CLEARANCE PROBLEM")
    return ok


def main():
    if sys.argv[1:] == ["check"]:
        clearance_report()
        motion_report()
        return
    os.makedirs(REF_DIR, exist_ok=True)
    for name, make in REFERENCE.items():
        shape = make()
        shape.WriteStep(os.path.join(REF_DIR, name + ".step"))
        T = triangles(shape, 0.5)
        write_stl(os.path.join(REF_DIR, name + ".stl"), T)
        vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6
        print("{:24s} {:6d} tris  steel mass {:.1f} g".format(name, len(T), vol * LX["steel_g_mm3"]))
    for name, make in PARTS.items():
        shape = make()
        shape.WriteStep(os.path.join(HERE, name + ".step"))
        maxh = 1.0 if name.startswith(("ledex_holder", "gap", "stroke")) else 0.4
        T = triangles(shape, maxh)
        write_stl(os.path.join(HERE, name + ".stl"), T)
        bb = T.reshape(-1, 3)
        print("{:24s} {:6d} tris  size {} mm".format(name, len(T), np.round(bb.max(0) - bb.min(0), 1)))
    clearance_report()
    motion_report()


if __name__ == "__main__":
    main()
