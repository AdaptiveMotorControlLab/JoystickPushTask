"""How far the washer tower moves when the mouse pushes the cube handle (rigid lever about the thumbstick pivot).

    python lever.py            # writes results/lever/lever_table.csv and figures/plots/lever_*.png

Geometry (x = push direction, z = up along the shaft at rest, origin at the shaft base) comes from
rig_geometry.py (measured joystick component, holder and printed parts):
- The pivot is inside the component body and not modelled: mid-body is 23.5 mm below the shaft base,
  component z 2-10 gives 19.3-27.3 mm (PIVOT_DEPTHS).
- Shaft: cone r 4 -> 1.5 mm over z 0-12, tip at z 89. M3 washers (ID 3.2) seat where the cone radius is 1.6 mm
  (z 11.5); ten 0.8 mm washers span z 11.5-19.5.
- Cube handle: push face 2.05 / 5.75 / 9.45 mm from the shaft axis (three holes), contact at z 92.4.
- The Ledex sits on the mouse side, axis horizontal at the tower centre, tip facing the washer rims (OD 9 mm),
  so a forward push opens the gap and the pull opposes the push. rig_forces.py covers other Ledex heights.
Force on the tower comes from the 3D model (results/fea3d, best fit, 10 washers, plunger seated), interpolated
linearly in log(force) vs log(gap). Tower tilt is reported but its effect on the force is not modelled.
"""
import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_results import HERE, RES, current_label, load3d, save
from rig_geometry import (HANDLE_Z, HOLES, PIVOT_DEPTH, PIVOT_DEPTHS, WASHER_RO, WASHER_SEAT, WASHER_T, N_WASHERS,
                          rotate, tilt_for_push)

TOWER = (WASHER_SEAT, WASHER_SEAT + N_WASHERS * WASHER_T)   # ten M3 washers on the cone (z, mm)
TOWER_Z = sum(TOWER) / 2
HOME_GAPS = (1.0, 2.0)
CURRENTS = (0.074, 0.106, 0.180, 0.310, 0.580)
TABLE_PUSHES = (1.0, 2.0, 5.0, 10.0, 15.0)
OUT_CSV = os.path.join(RES, "lever", "lever_table.csv")


def geometry(push, d_p, face):
    th = tilt_for_push(push, d_p, face)
    cx, cz = rotate(0.0, TOWER_Z, d_p, th)
    rim = lambda z: rotate(-WASHER_RO, z, d_p, th)[0] + WASHER_RO
    hx, hz = rotate(-face, HANDLE_Z, d_p, th)
    return dict(tilt_deg=np.degrees(th), target_dx_mm=rim(TOWER_Z), target_dz_mm=cz - TOWER_Z,
                tower_bottom_dx_mm=rim(TOWER[0]), tower_top_dx_mm=rim(TOWER[1]),
                arm_target=cz + d_p, arm_handle=hz + d_p)


def force_curves(d):
    """{current: (gaps, forces)} for the fitted model, 10 washers, plunger seated."""
    out = {}
    for a in CURRENTS:
        pts = sorted((k[2], f) for k, f in d.items() if k[0] == "best" and k[1] == 10 and k[3] == 0 and k[4] == a)
        out[a] = tuple(np.array(v) for v in zip(*pts))
    return out


def force_at(curves, a, gap):
    g, f = curves[a]
    if np.any(np.asarray(gap) > g.max()):
        raise ValueError("gap beyond the 3D table ({} mm); run sweep3d.py far".format(g.max()))
    return np.exp(np.interp(np.log(gap), np.log(g), np.log(f)))


def write_table(curves):
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    cols = ["pivot_depth_mm", "hole", "face_offset_mm", "push_mm", "tilt_deg", "target_dx_mm", "target_dz_mm",
            "tower_bottom_dx_mm", "tower_top_dx_mm", "home_gap_mm", "gap_mm", "current_A", "target_force_g",
            "handle_force_g"]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for d_p in PIVOT_DEPTHS:
            for name, face in HOLES:
                for u in TABLE_PUSHES:
                    g = geometry(u, d_p, face)
                    for g0 in HOME_GAPS:
                        gap = g0 + g["target_dx_mm"]
                        for a in CURRENTS:
                            ft = force_at(curves, a, gap)
                            w.writerow(["%g" % d_p, name, "%g" % face, "%g" % u, "%.2f" % g["tilt_deg"],
                                        "%.3f" % g["target_dx_mm"], "%.3f" % g["target_dz_mm"],
                                        "%.3f" % g["tower_bottom_dx_mm"], "%.3f" % g["tower_top_dx_mm"],
                                        "%g" % g0, "%.3f" % gap, "%.3f" % a, "%.4f" % ft,
                                        "%.4f" % (ft * g["arm_target"] / g["arm_handle"])])
    print("wrote", os.path.relpath(OUT_CSV, HERE))


PUSH = np.linspace(0, 15, 151)
DP_COLOR = dict(zip(PIVOT_DEPTHS, ("tab:green", "tab:blue", "tab:red")))
HOLE_STYLE = {"hole y 0.55": "-", "hole y 4.25": "--", "hole y 7.95": ":"}


def plot_motion():
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.5, 4.6))
    for d_p in PIVOT_DEPTHS:
        g = geometry(PUSH, d_p, HOLES[1][1])
        for name, face in HOLES:
            ax.plot(PUSH, geometry(PUSH, d_p, face)["target_dx_mm"], HOLE_STYLE[name], color=DP_COLOR[d_p],
                    label="pivot {:.1f} mm below the shaft base (tilt {:.1f} deg at 15 mm)".format(
                        d_p, g["tilt_deg"][-1]) if name == HOLES[0][0] else None)
        for g0, ls in zip(HOME_GAPS, ("-", "--")):
            bx.plot(PUSH, g0 + g["target_dx_mm"], ls, color=DP_COLOR[d_p],
                    label="pivot {:.1f} mm, home gap {:g} mm".format(d_p, g0))
    ax.set_xlabel("push: forward travel of the cube face at mid-height (mm)")
    ax.set_ylabel("washer tower moves away from the plunger tip (mm)")
    ax.set_title("Tower displacement (centre of the 10-washer tower)")
    ax.text(0.98, 0.03, "the three cube holes (solid / dashed / dotted)\nchange it by < 0.02 mm, so the lines overlap",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left")
    bx.set_xlabel("push (mm), middle cube hole")
    bx.set_ylabel("gap between plunger tip and washer rims (mm)")
    bx.set_title("Gap during the push")
    bx.grid(alpha=0.3)
    bx.legend(fontsize=7, loc="upper left")
    fig.suptitle("Joystick as a rigid lever about the thumbstick pivot (tower at z {:g}-{:g} mm, push at z {:g} mm "
                 "above the shaft base)".format(TOWER[0], TOWER[1], HANDLE_Z))
    save(fig, "lever_target_motion.png")


def plot_force(curves):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), sharex=True)
    face, a = HOLES[1][1], 0.580
    for g0, ls, alpha in zip(HOME_GAPS, ("-", "--"), (0.18, 0.09)):
        vals = {}
        for d_p in PIVOT_DEPTHS:
            g = geometry(PUSH, d_p, face)
            ft = force_at(curves, a, g0 + g["target_dx_mm"])
            vals[d_p] = (ft, ft * g["arm_target"] / g["arm_handle"])
        for ax, k in zip(axes, (0, 1)):
            lo, hi = vals[PIVOT_DEPTHS[0]][k], vals[PIVOT_DEPTHS[2]][k]
            ax.fill_between(PUSH, np.minimum(lo, hi), np.maximum(lo, hi), color="tab:red", alpha=alpha, lw=0)
            ax.plot(PUSH, vals[PIVOT_DEPTH][k], ls, color="tab:red", label="home gap {:g} mm".format(g0))
    axes[0].set_ylabel("pull on the 10-washer tower (g-force)")
    axes[1].set_ylabel("resistance felt at the cube handle (g-force)")
    axes[0].set_title("Force on the washer tower")
    axes[1].set_title("Resistance at the handle (torque balance)")
    for ax in axes:
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
        ax.set_xlabel("push at the cube handle (mm), middle cube hole")
    axes[0].legend(fontsize=8, title="line = pivot {:.1f} mm below shaft base (mid-body);\nshading = pivot "
                   "{:.1f}-{:.1f} mm".format(PIVOT_DEPTH, PIVOT_DEPTHS[0], PIVOT_DEPTHS[2]), title_fontsize=7)
    fig.suptitle("Ledex resistance vs push at {} (3D model, best fit, plunger seated)".format(current_label(a)))
    save(fig, "lever_force_vs_push.png")


def main():
    curves = force_curves(load3d())
    write_table(curves)
    plot_motion()
    plot_force(curves)
    for d_p in PIVOT_DEPTHS:
        g = geometry(np.array(TABLE_PUSHES), d_p, HOLES[1][1])
        print("pivot {:g} mm: push {} -> tower {} mm, tilt {} deg".format(
            d_p, TABLE_PUSHES, np.round(g["target_dx_mm"], 2), np.round(g["tilt_deg"], 1)))


if __name__ == "__main__":
    main()
