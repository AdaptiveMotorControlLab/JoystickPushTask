"""How far the washer tower moves when the mouse pushes the cube handle (rigid lever about the thumbstick pivot).

    python lever.py            # writes results/lever/lever_table.csv and figures/plots/lever_*.png

Geometry (x = push direction, z = up along the shaft at rest, origin at the shaft base):
- Thumbstick: APEM TS-1D1S00A-1294 (Mathis 2017 base, Digi-Key 679-2501-ND), castle cap removed, printed
  shaft screwed onto the lever stub. The pivot is inside the body and not given by APEM (their STEP is the
  outer envelope only), so it is a parameter: PIVOT_DEPTHS below the shaft base.
- Shaft (mechanical/3d-print/joystick/joystick_89mm.step): cone r 4 -> 1.5 mm over z 0-12, tip at z 89.
  M3 washers (ID 3.2) seat where the cone radius is 1.6 mm (z 11.5); ten 0.8 mm washers span z 11.5-19.5.
- Cube handle (mechanical/3d-print/joystick-handle-cube/joystick_handle_cube.step): 1.6 mm deep holes at
  y 0.55 / 4.25 / 7.95 mm, so it spans z 87.4-97.4; the push face is 2.05 / 5.75 / 9.45 mm from the shaft axis.
- The Ledex sits on the mouse side, axis horizontal at tower height, tip facing the washer rims (OD 9 mm),
  so a forward push opens the gap and the pull opposes the push.
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

PIVOT_DEPTHS = (5.0, 10.0, 20.0)       # pivot below the shaft base (mm): low / mid / high estimate
TOWER = (11.5, 19.5)                   # ten M3 washers on the cone (z, mm)
TOWER_Z = sum(TOWER) / 2
WASHER_RO = 4.5
HANDLE_Z = (87.4 + 97.4) / 2           # cube mid-height (push contact)
HOLES = (("hole y 0.55", 2.05), ("hole y 4.25", 5.75), ("hole y 7.95", 9.45))  # (name, push-face offset mm)
HOME_GAPS = (1.0, 2.0)
CURRENTS = (0.074, 0.106, 0.180, 0.310, 0.580)
TABLE_PUSHES = (1.0, 2.0, 5.0, 10.0, 15.0)
OUT_CSV = os.path.join(RES, "lever", "lever_table.csv")


def rotate(px, pz, d_p, th):
    """Point (px, pz) of the rigid shaft after a tilt th (rad) toward +x about the pivot at (0, -d_p)."""
    h = pz + d_p
    return px * np.cos(th) + h * np.sin(th), -d_p - px * np.sin(th) + h * np.cos(th)


def tilt_for_push(push, d_p, face):
    """Tilt that moves the push-face point at cube mid-height forward by push (mm); exact, not small-angle."""
    th = np.linspace(0, np.radians(30), 30001)
    x, _ = rotate(-face, HANDLE_Z, d_p, th)
    return np.interp(push, x - x[0], th)


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
DP_COLOR = {5.0: "tab:green", 10.0: "tab:blue", 20.0: "tab:red"}
HOLE_STYLE = {"hole y 0.55": "-", "hole y 4.25": "--", "hole y 7.95": ":"}


def plot_motion():
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.5, 4.6))
    for d_p in PIVOT_DEPTHS:
        g = geometry(PUSH, d_p, HOLES[1][1])
        for name, face in HOLES:
            ax.plot(PUSH, geometry(PUSH, d_p, face)["target_dx_mm"], HOLE_STYLE[name], color=DP_COLOR[d_p],
                    label="pivot {:g} mm below the shaft base (tilt {:.1f} deg at 15 mm)".format(
                        d_p, g["tilt_deg"][-1]) if name == HOLES[0][0] else None)
        for g0, ls in zip(HOME_GAPS, ("-", "--")):
            bx.plot(PUSH, g0 + g["target_dx_mm"], ls, color=DP_COLOR[d_p],
                    label="pivot {:g} mm, home gap {:g} mm".format(d_p, g0))
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
    fig.suptitle("Joystick as a rigid lever about the thumbstick pivot (tower at z 11.5-19.5 mm, push at z 92.4 mm "
                 "above the shaft base)")
    save(fig, "lever_target_motion.png")


def plot_force(curves):
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8), sharex=True)
    face = HOLES[1][1]
    for row, g0 in zip(axes, HOME_GAPS):
        for a, c in ((0.310, "tab:blue"), (0.580, "tab:red")):
            vals = {}
            for d_p in PIVOT_DEPTHS:
                g = geometry(PUSH, d_p, face)
                ft = force_at(curves, a, g0 + g["target_dx_mm"])
                vals[d_p] = (ft, ft * g["arm_target"] / g["arm_handle"])
            for ax, k in zip(row, (0, 1)):
                ax.fill_between(PUSH, vals[5.0][k], vals[20.0][k], color=c, alpha=0.15, lw=0)
                ax.plot(PUSH, vals[10.0][k], color=c, label=current_label(a))
        row[0].set_ylabel("home gap {:g} mm\npull on the 10-washer tower (g-force)".format(g0))
        row[1].set_ylabel("resistance felt at the cube handle (g-force)")
        for ax in row:
            ax.set_yscale("log")
            ax.grid(True, which="both", alpha=0.3)
    axes[0, 0].set_title("Force on the washer tower")
    axes[0, 1].set_title("Resistance at the handle (torque balance)")
    for ax in axes[1]:
        ax.set_xlabel("push at the cube handle (mm), middle cube hole")
    axes[0, 0].legend(fontsize=8, title="line = pivot 10 mm below shaft base;\nshading = pivot 5-20 mm",
                      title_fontsize=7)
    fig.suptitle("Ledex resistance vs push (3D model, best fit, plunger seated, coil current held constant)")
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
