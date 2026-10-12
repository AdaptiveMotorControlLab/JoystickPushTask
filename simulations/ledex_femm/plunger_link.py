"""Ledex plunger linked to the joystick shaft: resistance at the handle, return spring, friction, return to home.

    python plunger_link.py     # results/plunger_link/*.csv and figures/plunger_link/{handle_force_vs_push,
                               # design_space,spring_return,side_view}.png  (numpy + matplotlib;
                               # side_view uses results/plunger_link/apem_ts_outline.csv from plunger_link_3d.py)

Layout (lever.py coordinates: x = push direction, z up the shaft, origin at the shaft base, pivot at z = -d_p):
- The Ledex sits on the home (mouse) side with its axis horizontal at shaft height z_a. On the plate (taken as the
  thumbstick panel; shaft base 15.5 mm above it) the holder puts the axis 30 mm up, i.e. shaft z 14.5, where the
  washer tower was. The 1D constrainer guides the shaft in 4 mm slots in its base and top, so it must sit above
  the link (base at z_a + 6 here, top 56 mm higher, below the cube at z 87.4). Raising the link means raising
  holder and constrainer together, up to z_a ~23.5. This placement is an assumption to confirm on the rig.
- A rigid link (length LINK, pins at both ends) joins the plunger's pull end to a collar pin ATTACH_R from the
  shaft axis. A forward push draws the plunger out by the attach point's travel; the coil pulls it back in.
- Home: the stroke is s0 (never 0: seated, the plunger holds 12.8 N). The top slot of the constrainer ends at
  home, so it is the hard stop that keeps the magnet from pulling the handle toward the mouse.
Plunger pull: FEMM (results/femm/femm_plunger_force_vs_stroke.csv, no target, from `femm_run.py plunger`)
scaled at each stroke by datasheet / FEMM at 0.5734 A (the 100 % duty curve); FEMM reads up to 1.9x high at
long stroke. Spring: handle-equivalent force at the cube, P0 + k * push (what a scale pressed by the cube reads).
Friction: plunger weight on the nylon bearing (mu) plus a small pin allowance; the thumbstick's own friction is
part of the measured spring curve.
"""
import csv
import os
import struct

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_results import HERE, RES, save
from lever import HANDLE_Z, HOLES, PIVOT_DEPTHS, rotate, tilt_for_push

ROOT = os.path.dirname(os.path.dirname(HERE))
CAD = os.path.join(ROOT, "mechanical", "3d-print")
OUT_RES = os.path.join(RES, "plunger_link")
OUT_FIG = os.path.join(HERE, "figures", "plunger_link")

G = 9.80665
COMMANDS = ((0.074, "1 V"), (0.106, "2 V"), (0.180, "5 V"), (0.310, "10 V"), (0.580, "0.58 A (Imax raised)"))
PLUNGER_G = 20.1                 # plunger mass (datasheet)
ATTACH_R = 3.0                   # collar pin, mm from the shaft axis on the Ledex side
LINK = 10.0                      # pin-to-pin link length, mm
PIN_FRICTION_GF = 0.5            # allowance for the two link pins, gf at the plunger
MU = (0.15, 0.3, 0.4)            # plunger in its nylon bearing (dry nylon on steel)
SHAFT_BASE = 15.5               # shaft base above the thumbstick panel (cap removed, on the lever stub; estimate)
ATTACH_Z = (14.5, 19.0, 23.5)    # holder on the plate (axis 30 mm up) / +4.5 mm / +9 mm (constrainer top meets the cube)
HOME_STROKES = (1.5, 2.0, 3.0, 4.0, 5.0)
REC = dict(z_a=14.5, s0=3.0, d_p=10.0)
PIN_FROM_TIP = 3.0               # cross pin in the plunger's pull-end slot, mm from the tip (estimate)
CONSTRAINER_GAP = 6.0            # constrainer base above the link
LEDEX = dict(case_r=9.78, case_len=39.37, boss_r=7.0, boss_len=9.52, plunger_r=3.91, protrude=23.81)
FACE = HOLES[1][1]               # middle cube hole; the hole changes the lever by < 0.1 %
PLA = 1.24e-3                    # g / mm^3 (solid print; scale by the infill if printed hollow)
SAFETY = 2.0                     # spring preload / friction at home
RESTITUTION = 0.3                # bounce at the home stop (PLA on PLA)
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
    """Stroke, link angle and handle force per newton of plunger pull, for push(es) at the cube."""
    push = np.atleast_1d(np.asarray(push, float))
    th = np.array([tilt_for_push(u, d_p, FACE) for u in push])
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


def layout(z_a=REC["z_a"], s0=REC["s0"]):
    """Fixed positions (lever coordinates, mm) of the Ledex parts and the constrainer for a given link height."""
    pin0 = -ATTACH_R - LINK
    tip0 = pin0 + PIN_FROM_TIP
    return dict(z_a=z_a, s0=s0, pin0=pin0, tip0=tip0, face=tip0 - LEDEX["protrude"] - s0, panel=-SHAFT_BASE,
                constrainer=z_a + CONSTRAINER_GAP)


def friction_plunger_N(mu):
    return mu * PLUNGER_G * 1e-3 * G + PIN_FRICTION_GF * 1e-3 * G


# ---------------------------------------------------------------- moving mass
def stl_tetra(path):
    """Signed tetra volumes (mm^3) and centroids of a binary STL, origin as apex."""
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        data = np.frombuffer(f.read(50 * n), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    v = data["v"].reshape(-1, 3, 3).astype(float)
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


def effective_mass_g(d_p, z_a, s0):
    k = kinematics(0.0, d_p, z_a, s0)
    arm = HANDLE_Z + d_p
    return inertia_about_pivot(d_p) / arm ** 2 + PLUNGER_G * k["ratio"][0] ** 2


# ---------------------------------------------------------------- spring and return
def spring_gf(push, p0, k):
    return p0 + k * np.asarray(push)


def min_preload_gf(mu, d_p, z_a, s0):
    k = kinematics(PUSH, d_p, z_a, s0)
    return SAFETY * np.max(friction_plunger_N(mu) * k["ratio"]) / G * 1e3


def release(p0, k_spring, mu, d_p, z_a, s0, u0=15.0, a=0.0, tab=None, t_end=0.6, dt=2e-6):
    """Let go of the cube at push u0: Coulomb friction, spring, optional magnet, bounce on the home stop."""
    m = effective_mass_g(d_p, z_a, s0) * 1e-3
    uu = np.linspace(0, u0, 301)
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
        if u <= 0:
            u, v = 0.0, -RESTITUTION * v
            t_home = t_home if t_home is not None else t
            if v < 1e-4:
                v = 0.0
                ts.append(t); us.append(0.0)
                break
        if len(ts) == 0 or t - ts[-1] >= 5e-4:
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
            for z_a in ATTACH_Z:
                for s0 in HOME_STROKES:
                    k = kinematics(TABLE_PUSHES, d_p, z_a, s0)
                    for a, name in COMMANDS:
                        fp = plunger_force(tab, a, k["stroke_mm"])
                        for i, u in enumerate(TABLE_PUSHES):
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
                    "rest_push_mm"])
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
                                "%.0f" % (th * 1e3) if th else "", "%.2f" % rest])
    print("wrote", os.path.relpath(path, HERE))


def handle_curves(tab, a, d_p, z_a, s0, push=PUSH):
    k = kinematics(push, d_p, z_a, s0)
    return plunger_force(tab, a, k["stroke_mm"]) * k["ratio"] / G * 1e3


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
    ax.set_title("Magnet only (line: pivot 10 mm; shading: pivot 5-20 mm)")
    ax.legend(fontsize=8)
    mu = MU[1]
    kin = kinematics(PUSH, d_p, z_a, s0)
    fric = friction_plunger_N(mu) * kin["ratio"] / G * 1e3
    p_min = min_preload_gf(mu, d_p, z_a, s0)
    springs = (("weakest safe spring: {:.1f} gf at home + 0.2 gf/mm".format(p_min), p_min, 0.2, "-"),
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
        a_.set_xlabel("push at the cube handle (mm)")
        a_.grid(True, which="both", alpha=0.3)
    fig.suptitle("Plunger linked at shaft height {:g} mm, home stroke {:g} mm (datasheet-anchored FEMM pull, current held "
                 "constant)".format(z_a, s0))
    save(fig, "handle_force_vs_push.png", OUT_FIG)


def plot_design_space(tab):
    d_p = REC["d_p"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    for ax, (a, name) in zip(axes, (COMMANDS[3], COMMANDS[4])):
        for z_a, c in zip(ATTACH_Z, ("tab:blue", "tab:orange", "tab:green")):
            f0 = [handle_curves(tab, a, d_p, z_a, s0, np.array([0.0]))[0] for s0 in HOME_STROKES]
            f15 = [handle_curves(tab, a, d_p, z_a, s0, np.array([15.0]))[0] for s0 in HOME_STROKES]
            ax.plot(HOME_STROKES, f0, "o-", color=c, label="attach at shaft z {:g} mm, at home".format(z_a))
            ax.plot(HOME_STROKES, f15, "s--", color=c, label="attach at shaft z {:g} mm, after a 15 mm push".format(z_a))
        ax.axhspan(10, 20, color="grey", alpha=0.15, lw=0)
        ax.text(HOME_STROKES[-1], 14, "Mathis spring\n10-20 gf", ha="right", va="center", fontsize=7, color="dimgrey")
        ax.set_yscale("log")
        ax.set_title(name if "A" in name else "{} ({:.2f} A)".format(name, a))
        ax.set_xlabel("home stroke s0: plunger out from its seat at home (mm)")
        ax.grid(True, which="both", alpha=0.3)
    axes[0].set_ylabel("magnet resistance at the cube handle (g-force)")
    axes[1].legend(fontsize=7, loc="upper right")
    fig.suptitle("Design space: home stroke and link height (pivot 10 mm below the shaft base)")
    save(fig, "design_space.png", OUT_FIG)


def plot_spring_return(tab):
    s0, d_p = REC["s0"], REC["d_p"]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 4.6))
    mus = np.linspace(0.1, 0.5, 41)
    for z_a, c in zip(ATTACH_Z, ("tab:blue", "tab:orange", "tab:green")):
        ax.plot(mus, [min_preload_gf(m, d_p, z_a, s0) for m in mus], color=c,
                label="attach at shaft z {:g} mm".format(z_a))
    ax.axvspan(MU[0], MU[-1], color="grey", alpha=0.12, lw=0)
    ax.set_xlabel("friction coefficient, plunger in its nylon bearing")
    ax.set_ylabel("weakest spring force at home, at the cube (g-force)")
    ax.set_title("Weakest spring that still returns home (= {:g} x friction)".format(SAFETY))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    z_a, mu = REC["z_a"], MU[1]
    p_min = min_preload_gf(mu, d_p, z_a, s0)
    cases = (("weakest safe spring {:.1f} gf + 0.2 gf/mm".format(p_min), p_min, 0.2, 0.0, "k", "-"),
             ("same spring, preload halved", p_min / 2, 0.2, 0.0, "tab:red", "-"),
             ("no preload, 0.5 gf/mm only", 0.0, 0.5, 0.0, "tab:purple", "-"),
             ("Mathis-like 10 gf + 0.67 gf/mm", 10.0, 10.0 / 15, 0.0, "tab:blue", "--"),
             ("weakest spring with 10 V on", p_min, 0.2, 0.310, "tab:green", "-."))
    for lab, p0, k, a, c, ls in cases:
        t, u, th, rest = release(p0, k, mu, d_p, z_a, s0, a=a, tab=tab)
        tag = "reaches home in {:.0f} ms".format(th * 1e3) if th else "never reaches home"
        tag += ", rests at home" if rest < 0.05 else ", stuck at {:.1f} mm after the bounce".format(rest)
        bx.plot(t * 1e3, u, ls, color=c, label="{} ({})".format(lab, tag))
    bx.set_xlabel("time after release (ms)")
    bx.set_ylabel("push (mm)")
    bx.set_xlim(0, 260)
    bx.set_title("Release from 15 mm (attach z {:g} mm, mu {:g}, m_eff {:.1f} g, bounce {:g} at the stop)".format(
        z_a, mu, effective_mass_g(d_p, z_a, s0), RESTITUTION), fontsize=10)
    bx.grid(alpha=0.3)
    bx.legend(fontsize=7, loc="upper right", bbox_to_anchor=(1.0, 0.98))
    bx.set_ylim(-0.5, 22)
    save(fig, "spring_return.png", OUT_FIG)


def shaft_outline():
    """Half-section of the printed shaft (joystick_89mm.step): cone r 4 -> 1.5 over z 0-12, r 1.5 to the tip."""
    z = [0, 12, 89]
    r = [4.0, 1.5, 1.5]
    return np.r_[r, -np.array(r[::-1])], np.r_[z, z[::-1]]


def plot_side_view(tab):
    z_a, s0, d_p = REC["z_a"], REC["s0"], REC["d_p"]
    L = layout(z_a, s0)
    lx = LEDEX
    fig, ax = plt.subplots(figsize=(12, 10))
    grey = dict(color="0.75", lw=0)
    ax.fill_between([-100, 32], L["panel"] - 3, L["panel"], **grey)
    ax.text(-98, L["panel"] - 1.5, "plate / thumbstick panel", va="center", fontsize=8)
    path = os.path.join(OUT_RES, "apem_ts_outline.csv")
    if os.path.exists(path):
        h, w = np.loadtxt(path, delimiter=",", skiprows=1).T
        ax.fill(np.r_[w, -w[::-1]], np.r_[h, h[::-1]] + L["panel"], color="0.25", alpha=0.85, lw=0)
        ax.text(14, L["panel"] - 9, "APEM TS thumbstick\n(cap removed)", fontsize=8)
    zc = L["constrainer"]
    for x0, x1, z0, z1 in ((-19, -16, 0, 10), (-19, -16, 48, 56), (16, 19, 0, 56), (-19, -2, 53, 56), (17, 19, 53, 56),
                           (-16, -2, 0, 10)):
        ax.add_patch(plt.Rectangle((x0, zc + z0), x1 - x0, z1 - z0, color="tab:blue", alpha=0.25, lw=0))
    ax.text(20, zc + 28, "1D constrainer\n(section; 4 mm slots\nin base and top)", fontsize=8, color="tab:blue")
    ax.annotate("hard stop at home:\nslot ends", (-2, zc + 54.5), xytext=(-48, zc + 62), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    hx = L["face"] - 10
    ax.add_patch(plt.Rectangle((hx - 50, L["panel"]), 65, 6, color="tab:orange", alpha=0.35, lw=0))
    ax.add_patch(plt.Rectangle((hx + 10, L["panel"]), 5, 48, color="tab:orange", alpha=0.35, lw=0))
    ax.text(hx - 48, L["panel"] + 8, "Ledex holder", fontsize=8, color="tab:orange")
    ax.add_patch(plt.Rectangle((L["face"] - lx["case_len"], z_a - lx["case_r"]), lx["case_len"], 2 * lx["case_r"],
                               color="0.6", lw=0))
    ax.add_patch(plt.Rectangle((L["face"], z_a - lx["boss_r"]), lx["boss_len"], 2 * lx["boss_r"], color="0.5", lw=0))
    ax.text(L["face"] - lx["case_len"] / 2, z_a, "Ledex 195224-230", ha="center", va="center", fontsize=8)
    poses = ((0.0, 1.0), (7.5, 0.55), (15.0, 0.3))
    k = kinematics([p for p, _ in poses], d_p, z_a, s0)
    f10 = plunger_force(tab, 0.310, k["stroke_mm"]) * k["ratio"] / G * 1e3
    rs, zs = shaft_outline()
    for i, (u, alpha) in enumerate(poses):
        th = np.radians(k["tilt_deg"][i])
        x, z = rotate(rs, zs, d_p, th)
        ax.fill(x, z, color="0.9", ec="0.3", lw=0.8, alpha=alpha)
        cx = np.array([-5.75, 5.75, 5.75, -5.75])
        cz = np.array([87.4, 87.4, 97.4, 97.4])
        x, z = rotate(cx, cz, d_p, th)
        ax.fill(x, z, color="#45b5aa", alpha=alpha, lw=0)
        px = k["pin_x"][i]
        ax.add_patch(plt.Rectangle((L["face"] - 2, z_a - lx["plunger_r"]), px + PIN_FROM_TIP - L["face"] + 2,
                                   2 * lx["plunger_r"], color="0.3", alpha=alpha, lw=0))
        ax.plot([px, k["collar_x"][i]], [z_a, k["collar_z"][i]], color="#d4a017", lw=3, alpha=alpha,
                solid_capstyle="round")
        ax.plot(k["collar_x"][i], k["collar_z"][i], "o", color="#cc0000", ms=5, alpha=alpha)
        hx_, hz_ = rotate(-5.75, 92.4, d_p, th)
        ax.annotate("push {:g} mm: stroke {:.1f} mm,\n10 V resistance {:.0f} gf".format(u, k["stroke_mm"][i], f10[i]),
                    (hx_ + 12.5, hz_ + 4), xytext=(24, 103 - 9 * i), fontsize=8, alpha=max(alpha, 0.6),
                    arrowprops=dict(arrowstyle="-", lw=0.5, alpha=0.5))
    ax.annotate("", xy=(-6, 92.4), xytext=(-24, 92.4), arrowprops=dict(arrowstyle="-|>", lw=2, color="tab:red"))
    ax.text(-25, 95, "mouse pushes", ha="right", fontsize=9, color="tab:red")
    ax.plot(0, -d_p, "o", color="m", ms=7)
    t = np.linspace(0, 4 * np.pi, 200)
    ax.plot(2.5 * np.cos(t), -d_p + 2.5 * np.sin(t) * 0.5 + t / 4 - 1.5, color="m", lw=0.8)
    ax.annotate("pivot (10 mm below the shaft base; 5-20 mm possible)\n+ centring spring inside the thumbstick",
                (0, -d_p), xytext=(-98, -d_p - 18), fontsize=8, color="m", arrowprops=dict(arrowstyle="->", color="m"))
    ax.annotate("rigid link, pinned to the plunger's pull end\nand to a collar on the shaft",
                ((L["pin0"] - ATTACH_R) / 2, z_a + 1), xytext=(-98, z_a + 30), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.set_aspect("equal")
    ax.set_xlim(-100, 62)
    ax.set_ylim(L["panel"] - 32, 112)
    ax.set_xlabel("push direction x (mm); shaft axis at home = 0")
    ax.set_ylabel("height above the shaft base (mm)")
    ax.set_title("Plunger link, side view to scale: push 0 / 7.5 / 15 mm (fainter = further)\n"
                 "link at shaft z {:g} mm, home stroke {:g} mm; constrainer and holder placement assumed".format(z_a, s0))
    ax.grid(alpha=0.2)
    save(fig, "side_view.png", OUT_FIG)


def main():
    tab = plunger_table()
    write_tables(tab)
    plot_handle_force(tab)
    plot_design_space(tab)
    plot_spring_return(tab)
    plot_side_view(tab)
    z_a, s0, d_p = REC["z_a"], REC["s0"], REC["d_p"]
    for a, name in COMMANDS:
        f = handle_curves(tab, a, d_p, z_a, s0, np.array(TABLE_PUSHES))
        print("{:>22}: handle gf at push {} = {}".format(name, TABLE_PUSHES, np.round(f, 2)))
    k = kinematics(np.array(TABLE_PUSHES), d_p, z_a, s0)
    print("stroke", np.round(k["stroke_mm"], 2), "ratio", np.round(k["ratio"], 3), "link deg", np.round(k["link_deg"], 2))
    for mu in MU:
        print("mu", mu, "friction at handle %.2f gf, weakest preload %.2f gf" % (
            friction_plunger_N(mu) * k["ratio"][0] / G * 1e3, min_preload_gf(mu, d_p, z_a, s0)))
    print("effective mass at the cube %.2f g (inertia %.0f g mm^2)" % (effective_mass_g(d_p, z_a, s0),
                                                                      inertia_about_pivot(d_p)))


if __name__ == "__main__":
    main()
