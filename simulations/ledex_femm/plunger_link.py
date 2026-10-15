"""Ledex plunger linked to the joystick shaft: resistance at the handle, return spring, friction, return to home.

    python plunger_link.py     # results/plunger_link/*.csv and figures/plunger_link/{handle_force_vs_push,
                               # design_space,spring_return}.png  (numpy + matplotlib)

Geometry from rig_geometry.py (measured component, holder and constrainer; lever coordinates: x = push direction,
z up the shaft from the shaft base, pivot at z = -d_p):
- The Ledex stands on the breadboard on the home (mouse) side, axis horizontal at shaft height z_a. A collar on
  the 3 mm part of the shaft carries a pin ATTACH_R from the axis; a rigid link (LINK, pins at both ends) joins it
  to the plunger's pull end, which runs through the arch in the constrainer's home wall. A forward push draws
  the plunger out; the coil pulls it back in. Link heights: shaft z 12 (end of the cone) to ~18 (plunger 1 mm under
  the arch top).
- Push u is measured at the cube from the vertical shaft (the spring's neutral). s0 is the stroke at u = 0 (never
  0: seated, the plunger holds 12.8 N). The constrainer slot's home end stops the shaft at u_stop (-1.1 mm with the
  current constrainer, rig_geometry.stop_push): the magnet pulls the handle back onto it whenever its pull at home
  beats the spring's centring preload.
Plunger pull: FEMM (results/femm/femm_plunger_force_vs_stroke.csv, no target, from `femm_run.py plunger`) scaled
at each stroke by datasheet / FEMM at 0.5734 A (the 100 % duty curve); FEMM reads up to 1.9x high at long stroke.
Spring: centring spring as felt at the cube (what a scale pressed by the cube reads): preload P0 on each side of
neutral plus k per mm. Friction: plunger weight on the nylon bearing (mu) plus a pin allowance; the thumbstick's
own friction is part of the measured spring curve.
"""
import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_results import HERE, RES, save
import rig_geometry as rg
from rig_geometry import (ATTACH_R, CAD, FACE, HANDLE_Z, LINK, PIN_FROM_TIP, PIVOT_DEPTH, PIVOT_DEPTHS, read_stl,
                          rotate, stop_push, tilt_for_push)

OUT_RES = os.path.join(RES, "plunger_link")
OUT_FIG = os.path.join(HERE, "figures", "plunger_link")

G = 9.80665
COMMANDS = ((0.074, "1 V"), (0.106, "2 V"), (0.180, "5 V"), (0.310, "10 V"), (0.580, "0.58 A (Imax raised)"))
PLUNGER_G = rg.LEDEX["plunger_g"]
PIN_FRICTION_GF = 0.5            # allowance for the two link pins, gf at the plunger
MU = (0.15, 0.3, 0.4)            # plunger in its nylon bearing (dry nylon on steel)
ATTACH_Z = (rg.LINK_Z_MIN, round((rg.LINK_Z_MIN + rg.LINK_Z_MAX) / 2, 1), round(rg.LINK_Z_MAX, 1))
HOME_STROKES = (1.5, 2.0, 3.0, 4.0, 5.0)
REC = dict(z_a=ATTACH_Z[-1], s0=3.0, d_p=PIVOT_DEPTH)
PLA = 1.24e-3                    # g / mm^3 (solid print; scale by the infill if printed hollow)
SAFETY = 2.0                     # spring preload / friction at home
RESTITUTION = 0.3                # bounce at the home stop (PLA on PLA)
U_SMOOTH = 0.02                  # mm: the centring preload switches sign over this width around neutral
TABLE_PUSHES = (0.0, 1.0, 2.0, 5.0, 10.0, 15.0)
PUSH = np.linspace(0, 15, 151)


# ---------------------------------------------------------------- plunger force
def plunger_table():
    """{current: (strokes, force_N)}, FEMM anchored to the 100 % duty datasheet curve."""
    femm = {}
    with open(os.path.join(RES, "femm", "femm_plunger_force_vs_stroke.csv")) as f:
        for r in csv.DictReader(f):
            femm.setdefault(round(float(r["current_A"]), 4), []).append((float(r["stroke_mm"]), float(r["plunger_force_N"])))
    with open(os.path.join(HERE, "datasheet", "ledex_195224_60deg_force_stroke.csv")) as f:
        ds = sorted((float(r["stroke_mm"]), float(r["force_N"])) for r in csv.DictReader(f)
                    if r["duty_pct"] == "100" and r["source"] == "curve")
    ref = np.array(sorted(femm[0.5734]))
    ds = np.array(ds)
    ratio = ds[:, 1] / np.exp(np.interp(np.log(ds[:, 0]), np.log(ref[:, 0]), np.log(ref[:, 1])))
    fit = np.polyfit(np.log(ds[:, 0]), np.log(ratio), 2)          # smooth anchor, datasheet range 0.75-12.5 mm
    out = {}
    for a, pts in femm.items():
        s, fp = np.array(sorted(pts)).T
        ls = np.clip(np.log(s), np.log(ds[0, 0]), np.log(ds[-1, 0]))
        out[a] = (s, fp * np.exp(np.polyval(fit, ls)))
    return out


def plunger_force(tab, a, stroke):
    s, fp = tab[round(a, 4)]
    stroke = np.asarray(stroke, float)
    if np.any(stroke < s[0] - 1e-9) or np.any(stroke > s[-1] + 1e-9):
        raise ValueError("stroke outside {}-{} mm".format(s[0], s[-1]))
    return np.exp(np.interp(np.log(stroke), np.log(s), np.log(fp)))


# ---------------------------------------------------------------- kinematics
def kinematics(push, d_p, z_a, s0):
    """Stroke, link angle and handle force per newton of plunger pull, for push(es) at the cube (from neutral)."""
    push = np.atleast_1d(np.asarray(push, float))
    th = tilt_for_push(push, d_p, FACE)
    sx, sz = rotate(-ATTACH_R, z_a, d_p, th)                     # collar pin
    px = sx - np.sqrt(LINK ** 2 - (sz - z_a) ** 2)                # plunger pin stays on the axis z = z_a
    stroke = s0 + px - (-ATTACH_R - LINK)
    tx, tz = (px - sx) / LINK, (z_a - sz) / LINK                  # unit tension direction, shaft pin -> plunger
    tension = 1.0 / np.abs(tx)                                    # the bearing carries the vertical part
    torque = (sx * tz - (sz + d_p) * tx) * tension                # about the pivot, per newton of axial pull
    cx, cz = rotate(-FACE, HANDLE_Z, d_p, th)
    ratio = torque / (cz + d_p)                                   # horizontal push force at the cube per newton
    return dict(tilt_deg=np.degrees(th), stroke_mm=stroke, link_deg=np.degrees(np.arcsin((sz - z_a) / LINK)),
                ratio=ratio, side_N_per_N=np.abs(tz / tx), collar_x=sx, collar_z=sz, pin_x=px)


def layout(z_a, s0):
    """Ledex positions at neutral (lever coordinates, mm)."""
    pin0 = -ATTACH_R - LINK
    tip0 = pin0 + PIN_FROM_TIP
    return dict(z_a=z_a, s0=s0, pin0=pin0, tip0=tip0, face=tip0 - rg.LEDEX["protrude"] - s0)


def friction_plunger_N(mu):
    return mu * PLUNGER_G * 1e-3 * G + PIN_FRICTION_GF * 1e-3 * G


# ---------------------------------------------------------------- moving mass
def stl_tetra(path):
    """Signed tetra volumes (mm^3) and centroids of an STL, origin as apex."""
    v = read_stl(path)
    vol = np.einsum("ij,ij->i", v[:, 0], np.cross(v[:, 1], v[:, 2])) / 6.0
    return vol, v.sum(axis=1) / 4.0


def inertia_about_pivot(d_p):
    """Moment of inertia (g mm^2) of the printed shaft + cube about the pivot axis (solid PLA)."""
    total = 0.0
    parts = [("joystick/joystick_89mm.stl", lambda c: (c[:, 0], c[:, 2])),
             ("joystick-handle-cube/joystick_handle_cube.stl", lambda c: (c[:, 1] - 4.25, c[:, 2] + 88.9))]
    for rel, xz in parts:
        vol, cen = stl_tetra(os.path.join(CAD, rel))
        x, z = xz(cen)
        total += np.sum(PLA * vol * (x ** 2 + (z + d_p) ** 2))
    return abs(total)


def effective_mass_g(d_p, z_a, s0, plunger=True):
    arm = HANDLE_Z + d_p
    m = inertia_about_pivot(d_p) / arm ** 2
    if plunger:
        m += PLUNGER_G * kinematics(0.0, d_p, z_a, s0)["ratio"][0] ** 2
    return m


# ---------------------------------------------------------------- spring and return
def spring_gf(push, p0, k):
    """Centring spring at the cube: preload p0 toward neutral on either side, plus k per mm."""
    u = np.asarray(push, float)
    return p0 * np.tanh(u / U_SMOOTH) + k * u


def min_preload_gf(mu, d_p, z_a, s0):
    k = kinematics(PUSH, d_p, z_a, s0)
    return SAFETY * np.max(friction_plunger_N(mu) * k["ratio"]) / G * 1e3


def home_with_magnet(tab, a, p0, k, mu, d_p, z_a, s0, home_stop=None):
    """Where the handle sits at home with current a on: neutral (0) or pulled back onto the stop."""
    u_stop = stop_push(d_p) if home_stop is None else home_stop
    if u_stop >= 0:
        return 0.0
    kin = kinematics(0.0, d_p, z_a, s0)
    mag = plunger_force(tab, a, kin["stroke_mm"])[0] * kin["ratio"][0] / G * 1e3
    fric = friction_plunger_N(mu) * kin["ratio"][0] / G * 1e3
    return u_stop if mag > p0 + fric else 0.0


def release(p0, k_spring, mu, d_p, z_a, s0, u0=15.0, a=0.0, tab=None, home_stop=None, t_end=0.6, dt=2e-6):
    """Let go of the cube at push u0: Coulomb friction, centring spring, optional magnet, bounce on the home stop.

    Returns (t, u, t_home, rest): t_home = first time the handle is back at neutral, rest = final push (mm)."""
    u_stop = stop_push(d_p) if home_stop is None else home_stop
    m = effective_mass_g(d_p, z_a, s0) * 1e-3
    uu = np.linspace(min(u_stop, 0.0) - 0.5, u0, 401)
    kin = kinematics(uu, d_p, z_a, s0)
    fric = friction_plunger_N(mu) * kin["ratio"]
    mag = plunger_force(tab, a, kin["stroke_mm"]) * kin["ratio"] if a > 0 else 0 * uu
    u, v, t, ts, us = u0 * 1e-3, 0.0, 0.0, [0.0], [u0]
    t_home = None
    while t < t_end:
        um = u * 1e3
        drive = -(spring_gf(um, p0, k_spring) * 1e-3 * G + np.interp(um, uu, mag))
        f = np.interp(um, uu, fric)
        if v == 0.0 and abs(drive) <= f:
            break                                                    # stuck by friction
        acc = (drive - np.sign(v if v != 0 else drive) * f) / m
        v_new = v + acc * dt
        if v != 0 and np.sign(v_new) != np.sign(v):
            v_new = 0.0
        v = v_new
        u += v * dt
        t += dt
        if t_home is None and u <= 0.05e-3:
            t_home = t
        if u <= u_stop * 1e-3:
            u, v = u_stop * 1e-3, -RESTITUTION * v
            if abs(v) < 1e-4:
                v = 0.0
        if t - ts[-1] >= 5e-4:
            ts.append(t); us.append(u * 1e3)
    ts.append(t); us.append(u * 1e3)
    return np.array(ts), np.array(us), t_home, u * 1e3


# ---------------------------------------------------------------- outputs
def write_tables(tab):
    os.makedirs(OUT_RES, exist_ok=True)
    path = os.path.join(OUT_RES, "plunger_link_table.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pivot_depth_mm", "attach_z_mm", "home_stroke_mm", "push_mm", "tilt_deg", "stroke_mm",
                    "link_angle_deg", "handle_per_plunger", "current_A", "command", "plunger_force_N",
                    "magnet_at_handle_gf", "plunger_side_load_N"])
        for d_p in PIVOT_DEPTHS:
            pushes = (round(stop_push(d_p), 2),) + TABLE_PUSHES
            for z_a in ATTACH_Z:
                for s0 in HOME_STROKES:
                    k = kinematics(pushes, d_p, z_a, s0)
                    for a, name in COMMANDS:
                        fp = plunger_force(tab, a, k["stroke_mm"])
                        for i, u in enumerate(pushes):
                            w.writerow(["%g" % d_p, "%g" % z_a, "%g" % s0, "%g" % u, "%.2f" % k["tilt_deg"][i],
                                        "%.3f" % k["stroke_mm"][i], "%.2f" % k["link_deg"][i], "%.4f" % k["ratio"][i],
                                        "%.3f" % a, name, "%.4f" % fp[i], "%.2f" % (fp[i] * k["ratio"][i] / G * 1e3),
                                        "%.4f" % (fp[i] * k["side_N_per_N"][i])])
    print("wrote", os.path.relpath(path, HERE))
    path = os.path.join(OUT_RES, "spring_requirement.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pivot_depth_mm", "attach_z_mm", "home_stroke_mm", "mu", "friction_at_plunger_gf",
                    "friction_at_handle_gf", "min_preload_gf", "effective_mass_g", "return_time_ms",
                    "rest_push_mm", "home_stop_mm", "home_with_10V_mm"])
        for d_p in PIVOT_DEPTHS:
            for z_a in ATTACH_Z:
                s0 = REC["s0"]
                for mu in MU:
                    kin = kinematics(0.0, d_p, z_a, s0)
                    fpl = friction_plunger_N(mu) / G * 1e3
                    p0 = min_preload_gf(mu, d_p, z_a, s0)
                    _, _, th, rest = release(p0, 0.2, mu, d_p, z_a, s0)
                    w.writerow(["%g" % d_p, "%g" % z_a, "%g" % s0, "%g" % mu, "%.2f" % fpl,
                                "%.2f" % (fpl * kin["ratio"][0]), "%.2f" % p0,
                                "%.2f" % effective_mass_g(d_p, z_a, s0),
                                "%.0f" % (th * 1e3) if th else "", "%.2f" % rest, "%.2f" % stop_push(d_p),
                                "%.2f" % home_with_magnet(tab, 0.310, p0, 0.2, mu, d_p, z_a, s0)])
    print("wrote", os.path.relpath(path, HERE))


def handle_curves(tab, a, d_p, z_a, s0, push=PUSH):
    k = kinematics(push, d_p, z_a, s0)
    return plunger_force(tab, a, k["stroke_mm"]) * k["ratio"] / G * 1e3


def pivot_text():
    return "pivot {:.1f} mm below the shaft base (mid-body); shading {:.1f}-{:.1f} mm".format(
        PIVOT_DEPTH, PIVOT_DEPTHS[0], PIVOT_DEPTHS[2])


def plot_handle_force(tab):
    z_a, s0, d_p = REC["z_a"], REC["s0"], REC["d_p"]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 4.8))
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(COMMANDS)))
    for (a, name), c in zip(COMMANDS, colors):
        lo, mid, hi = (handle_curves(tab, a, dp, z_a, s0) for dp in PIVOT_DEPTHS)
        ax.fill_between(PUSH, np.minimum(lo, hi), np.maximum(lo, hi), color=c, alpha=0.15, lw=0)
        ax.plot(PUSH, mid, color=c, label="{} ({:.3f} A)".format(name, a) if "A" not in name else name)
    ax.set_yscale("log")
    ax.set_ylabel("magnet resistance at the cube handle (g-force)")
    ax.set_title("Magnet only ({})".format(pivot_text()), fontsize=9)
    ax.legend(fontsize=8)
    mu = MU[1]
    kin = kinematics(PUSH, d_p, z_a, s0)
    fric = friction_plunger_N(mu) * kin["ratio"] / G * 1e3
    p_min = min_preload_gf(mu, d_p, z_a, s0)
    springs = (("weakest safe spring: {:.1f} gf preload + 0.2 gf/mm".format(p_min), p_min, 0.2, "-"),
               ("Mathis 2017 range: 10 gf at home -> 20 gf at 15 mm", 10.0, 10.0 / 15, "--"))
    for lab, p0, k, ls in springs:
        bx.plot(PUSH, spring_gf(PUSH, p0, k) + fric, ls, color="k", label="0 V, " + lab)
    base = spring_gf(PUSH, p_min, 0.2) + fric
    for (a, name), c in list(zip(COMMANDS, colors))[1:]:
        bx.plot(PUSH, base + handle_curves(tab, a, d_p, z_a, s0), color=c,
                label="{} + weakest safe spring".format(name.split(" (")[0]))
    bx.set_ylabel("total push force at the cube (g-force)")
    bx.set_title("What the mouse pushes against (spring + friction mu {:g} + magnet)".format(mu))
    bx.set_yscale("log")
    bx.legend(fontsize=7)
    for a_ in (ax, bx):
        a_.set_xlabel("push at the cube handle from neutral (mm)")
        a_.grid(True, which="both", alpha=0.3)
    fig.suptitle("Plunger linked at shaft z {:g} mm (Ledex axis {:.1f} mm above the breadboard), stroke {:g} mm at "
                 "neutral (datasheet-anchored FEMM pull)".format(z_a, rg.world_z(z_a), s0))
    save(fig, "handle_force_vs_push.png", OUT_FIG)


def plot_design_space(tab):
    d_p = REC["d_p"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    for ax, (a, name) in zip(axes, (COMMANDS[3], COMMANDS[4])):
        for z_a, c in zip(ATTACH_Z, ("tab:blue", "tab:orange", "tab:green")):
            f0 = [handle_curves(tab, a, d_p, z_a, s0, np.array([0.0]))[0] for s0 in HOME_STROKES]
            f15 = [handle_curves(tab, a, d_p, z_a, s0, np.array([15.0]))[0] for s0 in HOME_STROKES]
            ax.plot(HOME_STROKES, f0, "o-", color=c, label="link at shaft z {:g} mm, at home".format(z_a))
            ax.plot(HOME_STROKES, f15, "s--", color=c, label="link at shaft z {:g} mm, after a 15 mm push".format(z_a))
        ax.axhspan(10, 20, color="grey", alpha=0.15, lw=0)
        ax.text(HOME_STROKES[-1], 14, "Mathis spring\n10-20 gf", ha="right", va="center", fontsize=7, color="dimgrey")
        ax.set_yscale("log")
        ax.set_title(name if "A" in name else "{} ({:.2f} A)".format(name, a))
        ax.set_xlabel("stroke at neutral s0: plunger out from its seat (mm)")
        ax.grid(True, which="both", alpha=0.3)
    axes[0].set_ylabel("magnet resistance at the cube handle (g-force)")
    axes[1].legend(fontsize=7, loc="upper right")
    fig.suptitle("Design space: stroke at neutral and link height (pivot {:.1f} mm below the shaft base)".format(d_p))
    save(fig, "design_space.png", OUT_FIG)


def plot_spring_return(tab):
    s0, d_p = REC["s0"], REC["d_p"]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 4.6))
    mus = np.linspace(0.1, 0.5, 41)
    for z_a, c in zip(ATTACH_Z, ("tab:blue", "tab:orange", "tab:green")):
        ax.plot(mus, [min_preload_gf(m, d_p, z_a, s0) for m in mus], color=c,
                label="link at shaft z {:g} mm".format(z_a))
    ax.axvspan(MU[0], MU[-1], color="grey", alpha=0.12, lw=0)
    ax.set_xlabel("friction coefficient, plunger in its nylon bearing")
    ax.set_ylabel("weakest centring preload, at the cube (g-force)")
    ax.set_title("Weakest spring that still returns home (= {:g} x friction)".format(SAFETY))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    z_a, mu = REC["z_a"], MU[1]
    p_min = min_preload_gf(mu, d_p, z_a, s0)
    u_stop = stop_push(d_p)
    cases = (("weakest safe spring {:.1f} gf + 0.2 gf/mm".format(p_min), p_min, 0.2, 0.0, None, "k", "-"),
             ("same spring, preload halved", p_min / 2, 0.2, 0.0, None, "tab:red", "-"),
             ("no preload, 0.5 gf/mm only", 0.0, 0.5, 0.0, None, "tab:purple", "-"),
             ("Mathis-like 10 gf + 0.67 gf/mm", 10.0, 10.0 / 15, 0.0, None, "tab:blue", "--"),
             ("weakest spring with 10 V on", p_min, 0.2, 0.310, None, "tab:green", "-."),
             ("10 V on, stop moved to neutral", p_min, 0.2, 0.310, 0.0, "tab:olive", ":"))
    for lab, p0, k, a, hs, c, ls in cases:
        t, u, th, rest = release(p0, k, mu, d_p, z_a, s0, a=a, tab=tab, home_stop=hs)
        tag = "home in {:.0f} ms".format(th * 1e3) if th else "never reaches home"
        tag += ", rests at {:+.2f} mm".format(rest)
        bx.plot(t * 1e3, u, ls, color=c, label="{} ({})".format(lab, tag))
    bx.axhline(u_stop, color="0.4", lw=0.8)
    bx.text(258, u_stop - 0.3, "home stop (slot end) {:.2f} mm".format(u_stop), ha="right", va="top", fontsize=7)
    bx.set_xlabel("time after release (ms)")
    bx.set_ylabel("push from neutral (mm)")
    bx.set_xlim(0, 260)
    bx.set_title("Release from 15 mm (link z {:g} mm, mu {:g}, m_eff {:.1f} g, bounce {:g} at the stop)".format(
        z_a, mu, effective_mass_g(d_p, z_a, s0), RESTITUTION), fontsize=10)
    bx.grid(alpha=0.3)
    bx.legend(fontsize=7, loc="upper right", bbox_to_anchor=(1.0, 0.98))
    bx.set_ylim(u_stop - 1.5, 22)
    save(fig, "spring_return.png", OUT_FIG)


def main():
    tab = plunger_table()
    write_tables(tab)
    plot_handle_force(tab)
    plot_design_space(tab)
    plot_spring_return(tab)
    z_a, s0, d_p = REC["z_a"], REC["s0"], REC["d_p"]
    for a, name in COMMANDS:
        f = handle_curves(tab, a, d_p, z_a, s0, np.array(TABLE_PUSHES))
        print("{:>22}: handle gf at push {} = {}".format(name, TABLE_PUSHES, np.round(f, 2)))
    k = kinematics(np.array(TABLE_PUSHES), d_p, z_a, s0)
    print("link z", z_a, "stroke", np.round(k["stroke_mm"], 2), "ratio", np.round(k["ratio"], 3),
          "link deg", np.round(k["link_deg"], 2), "home stop", round(stop_push(d_p), 2))
    for mu in MU:
        print("mu", mu, "friction at handle %.2f gf, weakest preload %.2f gf" % (
            friction_plunger_N(mu) * k["ratio"][0] / G * 1e3, min_preload_gf(mu, d_p, z_a, s0)))
    print("effective mass at the cube %.2f g (inertia %.0f g mm^2)" % (effective_mass_g(d_p, z_a, s0),
                                                                      inertia_about_pivot(d_p)))


if __name__ == "__main__":
    main()
