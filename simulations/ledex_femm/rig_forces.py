"""Washer target vs plunger link on the measured rig: resistance at the handle over the Ledex height and distance.

    python rig_forces.py     # results/rig/{options_force_vs_push,design_map_washers,design_map_link,summary}.csv
                             # figures/rig/{options_force_vs_push,design_maps}.png   (numpy, scipy, matplotlib)

Both options are placed by the same two holder settings: the Ledex body face X (distance, relative to the joystick
axis at neutral) and the Ledex axis height Z above the breadboard (rig_geometry frame).
- Washer target: ten M3 washers on the shaft (tower centre at shaft z 15.5), the seated plunger's pull end faces
  them. Pull from the 3D model: tower offset along its own (vertical) axis at 0.31 A (results/fea3d/
  force_offset_3d.csv, `sweep3d.py offset`), scaled to other currents by the centred sweep (force_sweep_3d.csv;
  the current ratio is the same at every gap within 2 %). Treat as +-40 %.
- Plunger link: plunger_link.py (datasheet-anchored FEMM pull, link kinematics); the link height is the axis
  height and the home stroke follows from the face position.
Feasibility (both): plunger (+1 mm) through the constrainer's arch, M14 nut clear of the constrainer wall by 1 mm,
holder height range; washers: no contact at the home stop (gap >= 0.3 mm); link: collar on the straight shaft,
stroke within the datasheet range (0.75-12.5 mm) from the home stop to a 15 mm push.
"""
import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy.interpolate import RegularGridInterpolator

import plunger_link as pl
import rig_geometry as rg
from plot_results import COMMAND_V, HERE, RES, save

OUT_RES = rg.OUT_RES
OUT_FIG = os.path.join(HERE, "figures", "rig")
G = pl.G
LX = rg.LEDEX
TOWER_Z = rg.WASHER_SEAT + rg.N_WASHERS * rg.WASHER_T / 2      # lever z of the tower centre
H_RANGE = (30.0, 70.0)                                          # adjustable holder (Ledex axis above the breadboard)
CONTACT_MIN = 0.3
STROKE_RANGE = (0.75, 12.5)
MAX_PUSH = 15.0
REC = {"washers": dict(H=float(rg.world_z(TOWER_Z)), face=-rg.WASHER_RO - 1.0 - LX["protrude"]),
       "link": dict(H=float(rg.world_z(pl.REC["z_a"])),
                    face=pl.layout(pl.REC["z_a"], pl.REC["s0"])["face"])}
COMMANDS = pl.COMMANDS
TABLE_PUSHES = pl.TABLE_PUSHES


def command_current(volts):
    """Coil current (A) for an AO0 command (V), measured with Imax at its minimum."""
    a, v = np.array(sorted(COMMAND_V.items())).T
    return np.interp(volts, v, a)


# ---------------------------------------------------------------- washer pull
class WasherForce:
    """Pull (gf, along the plunger axis) on the 10-washer tower vs gap, vertical offset and current."""

    def __init__(self):
        rows = list(csv.DictReader(open(os.path.join(RES, "fea3d", "force_offset_3d.csv"))))
        gaps = sorted({float(r["gap_mm"]) for r in rows})
        offs = sorted({float(r["yoff_mm"]) for r in rows})
        F = np.full((len(gaps), len(offs)), np.nan)
        for r in rows:
            F[gaps.index(float(r["gap_mm"])), offs.index(float(r["yoff_mm"]))] = float(r["force_g"])
        if np.isnan(F).any() or len(gaps) < 2 or len(offs) < 2:
            raise SystemExit("force_offset_3d.csv incomplete: finish `sweep3d.py offset` first")
        self.gaps, self.offs, self.grid = np.array(gaps), np.array(offs), F
        self.lf = RegularGridInterpolator((self.gaps, self.offs), np.log(F), method="pchip")
        cen = {}
        for r in csv.DictReader(open(os.path.join(RES, "fea3d", "force_sweep_3d.csv"))):
            if r["set"] == "best" and r["n_washers"] == "10" and float(r["stroke_mm"]) == 0:
                cen[(float(r["gap_mm"]), round(float(r["current_A"]), 3))] = float(r["force_g"])
        far = sorted((g, f) for (g, a), f in cen.items() if a == 0.31 and g >= gaps[-1])
        self.far = np.array(far)
        cur = sorted({a for _, a in cen})
        rat = [np.mean([cen[(g, a)] / cen[(g, 0.31)] for g, b in cen if b == a and (g, 0.31) in cen]) for a in cur]
        self.cur, self.rat = np.log(cur), np.log(rat)

    def ratio(self, a):
        la = np.log(np.maximum(a, 1e-4))
        slope = (self.rat[1] - self.rat[0]) / (self.cur[1] - self.cur[0])
        r = np.interp(la, self.cur, self.rat)
        r = np.where(la < self.cur[0], self.rat[0] + slope * (la - self.cur[0]), r)
        return np.exp(r)

    def __call__(self, gap, yoff, a=0.31):
        g = np.asarray(gap, float)
        ya = np.abs(np.asarray(yoff, float))
        g, ya = np.broadcast_arrays(g, ya)
        yl, yp = self.offs[-1], self.offs[-2]
        y = np.minimum(ya, yl)
        g0, g1, gl = self.gaps[0], self.gaps[1], self.gaps[-1]
        gc = np.clip(g, g0, gl)
        lf = self.lf(np.stack([gc, y], -1))
        dy = self.lf(np.stack([gc, np.full_like(y, yl)], -1)) - self.lf(np.stack([gc, np.full_like(y, yp)], -1))
        lf = lf + np.where(ya > yl, np.minimum(dy, 0) / (yl - yp) * (ya - yl), 0)
        lo = self.lf(np.stack([np.full_like(y, g0), y], -1))
        hi = self.lf(np.stack([np.full_like(y, g1), y], -1))
        lf = np.where(g < g0, lf + (lo - hi) / (g1 - g0) * (g0 - g), lf)
        fg, ff = self.far[:, 0], np.log(self.far[:, 1])
        tail = np.interp(g, fg, ff) - ff[0]
        tail = np.where(g > fg[-1], ff[-1] - ff[0] + (ff[-1] - ff[-2]) / (fg[-1] - fg[-2]) * (g - fg[-1]), tail)
        lf = np.where(g > gl, lf + tail, lf)
        return np.exp(lf) * self.ratio(a)


def washer_handle(wf, push, H, face, a, d_p=rg.PIVOT_DEPTH):
    """Resistance at the cube (gf), gap and vertical offset (mm) for the washer target."""
    th = rg.tilt_for_push(push, d_p)
    xt, zt = rg.rotate(0.0, TOWER_Z, d_p, th)
    gap = xt - rg.WASHER_RO - (face + LX["protrude"])
    yoff = rg.world_z(zt) - H
    _, cz = rg.rotate(-rg.FACE, rg.HANDLE_Z, d_p, th)
    return wf(gap, yoff, a) * (zt + d_p) / (cz + d_p), gap, yoff


# ---------------------------------------------------------------- plunger link
def plunger_force_at(tab, a, stroke):
    """Plunger pull (N) at any current, log-interpolated between the FEMM currents."""
    cur = np.array(sorted(tab))
    la = np.log(a)
    i = int(np.clip(np.searchsorted(cur, a) - 1, 0, len(cur) - 2))
    f0 = np.log(pl.plunger_force(tab, cur[i], stroke))
    f1 = np.log(pl.plunger_force(tab, cur[i + 1], stroke))
    w = (la - np.log(cur[i])) / (np.log(cur[i + 1]) - np.log(cur[i]))
    return np.exp(f0 + w * (f1 - f0))


def link_settings(H, face):
    z_a = rg.shaft_z(H)
    s0 = pl.layout(z_a, 0.0)["tip0"] - LX["protrude"] - face
    return z_a, s0


def link_handle(tab, push, H, face, a, d_p=rg.PIVOT_DEPTH):
    z_a, s0 = link_settings(H, face)
    k = pl.kinematics(push, d_p, z_a, s0)
    s = np.clip(k["stroke_mm"], 0.5, 13.0)
    return plunger_force_at(tab, a, s) * k["ratio"] / G * 1e3, k["stroke_mm"]


# ---------------------------------------------------------------- feasibility
def common_ok(H, face):
    H, face = np.broadcast_arrays(np.asarray(H, float), np.asarray(face, float))
    arch = rg.arch_clear(H, LX["plunger_r"] + rg.CLEARANCE)
    nut = face + rg.PLATE_T + rg.NUT_T <= -rg.CON_OUTER - rg.CLEARANCE
    return arch & nut & (H >= H_RANGE[0]) & (H <= H_RANGE[1])


def washers_ok(wf, H, face, d_p=rg.PIVOT_DEPTH):
    _, gap, _ = washer_handle(wf, rg.stop_push(d_p), H, face, 0.31, d_p)
    return common_ok(H, face) & (gap >= CONTACT_MIN)


def link_ok(tab, H, face, d_p=rg.PIVOT_DEPTH):
    z_a, s0 = link_settings(H, face)
    ok = common_ok(H, face) & (z_a >= rg.LINK_Z_MIN - 1e-9) & (z_a <= rg.LINK_Z_MAX + 1e-9)
    s_lo = s0 + (pl.kinematics(rg.stop_push(d_p), d_p, float(np.mean(z_a)), 0.0)["stroke_mm"][0])
    s_hi = s0 + (pl.kinematics(MAX_PUSH, d_p, float(np.mean(z_a)), 0.0)["stroke_mm"][0])
    return ok & (s_lo >= STROKE_RANGE[0]) & (s_hi <= STROKE_RANGE[1])


# ---------------------------------------------------------------- outputs
def push_axis(d_p=rg.PIVOT_DEPTH):
    return np.linspace(rg.stop_push(d_p), MAX_PUSH, 161)


def write_options(wf, tab):
    os.makedirs(OUT_RES, exist_ok=True)
    path = os.path.join(OUT_RES, "options_force_vs_push.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["option", "pivot_depth_mm", "ledex_axis_z_mm", "ledex_face_x_mm", "command", "current_A",
                    "push_mm", "gap_or_stroke_mm", "handle_gf"])
        for d_p in rg.PIVOT_DEPTHS:
            pushes = np.unique(np.r_[rg.stop_push(d_p), TABLE_PUSHES])
            for a, name in COMMANDS:
                fw, gap, _ = washer_handle(wf, pushes, REC["washers"]["H"], REC["washers"]["face"], a, d_p)
                fl, st = link_handle(tab, pushes, REC["link"]["H"], REC["link"]["face"], a, d_p)
                for opt, F, s in (("washers", fw, gap), ("link", fl, st)):
                    for u, v, x in zip(pushes, F, s):
                        w.writerow([opt, d_p, round(REC[opt]["H"], 2), round(REC[opt]["face"], 2), name, a,
                                    round(float(u), 3), round(float(x), 3), round(float(v), 4)])
    print("wrote", os.path.relpath(path, HERE))


def map_grid(opt):
    if opt == "washers":
        return np.arange(-36.0, -25.95, 0.1), np.arange(44.0, 62.01, 0.1)
    return np.arange(-44.0, -35.95, 0.1), np.arange(52.0, 62.01, 0.1)


def design_map(wf, tab, opt, pushes=(0.0, 10.0), a=0.31):
    fx, hz = map_grid(opt)
    FX, HZ = np.meshgrid(fx, hz)
    out = {}
    for u in pushes:
        if opt == "washers":
            out[u] = washer_handle(wf, u, HZ, FX, a)[0]
        else:
            out[u] = np.vstack([link_handle(tab, u, h, fx, a)[0] for h in hz])
    ok = washers_ok(wf, HZ, FX) if opt == "washers" else np.vstack([link_ok(tab, h, fx) for h in hz])
    return fx, hz, out, ok


def write_maps(maps):
    for opt, (fx, hz, F, ok) in maps.items():
        path = os.path.join(OUT_RES, "design_map_%s.csv" % opt)
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ledex_face_x_mm", "ledex_axis_z_mm", "setting_mm", "feasible"]
                       + ["handle_gf_10V_push_%g" % u for u in F])
            for i, h in enumerate(hz[::5]):
                for j, x in enumerate(fx[::5]):
                    ii, jj = 5 * i, 5 * j
                    if opt == "washers":
                        setting = -rg.WASHER_RO - LX["protrude"] - x
                    else:
                        setting = link_settings(h, x)[1]
                    w.writerow([round(x, 2), round(h, 2), round(float(setting), 2), int(ok[ii, jj])]
                               + [round(float(F[u][ii, jj]), 4) for u in F])
        print("wrote", os.path.relpath(path, HERE))


def write_summary(wf, tab, maps):
    path = os.path.join(OUT_RES, "summary.csv")
    rows = []
    for opt in ("washers", "link"):
        H, face = REC[opt]["H"], REC[opt]["face"]
        fx, hz, F, ok = maps[opt]
        best = np.unravel_index(np.argmax(np.where(ok, F[0.0], -1)), ok.shape)
        for a, name in COMMANDS:
            for d_p in rg.PIVOT_DEPTHS:
                pushes = np.array(TABLE_PUSHES)
                fn = washer_handle(wf, pushes, H, face, a, d_p)[0] if opt == "washers" else \
                    link_handle(tab, pushes, H, face, a, d_p)[0]
                rows.append([opt, d_p, round(H, 2), round(face, 2), name, a]
                            + [round(float(v), 3) for v in fn]
                            + [round(float(fx[best[1]]), 2), round(float(hz[best[0]]), 2)])
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["option", "pivot_depth_mm", "ledex_axis_z_mm", "ledex_face_x_mm", "command", "current_A"]
                   + ["handle_gf_push_%g" % u for u in TABLE_PUSHES]
                   + ["strongest_feasible_face_x_mm", "strongest_feasible_axis_z_mm"])
        w.writerows(rows)
    print("wrote", os.path.relpath(path, HERE))
    return rows


def plot_options(wf, tab):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(COMMANDS)))
    for ax, opt in zip(axes, ("washers", "link")):
        H, face = REC[opt]["H"], REC[opt]["face"]
        for (a, name), c in zip(COMMANDS, colors):
            curves = []
            for d_p in rg.PIVOT_DEPTHS:
                u = push_axis(d_p)
                F = washer_handle(wf, u, H, face, a, d_p)[0] if opt == "washers" else link_handle(tab, u, H, face, a, d_p)[0]
                curves.append((u, F))
            u, F = curves[1]
            ax.plot(u, F, color=c, label=name)
            ax.fill_between(curves[0][0], curves[0][1], np.interp(curves[0][0], curves[2][0], curves[2][1]),
                            color=c, alpha=0.15, lw=0)
        ax.axvline(rg.stop_push(rg.PIVOT_DEPTH), color="0.4", ls=":", lw=1)
        ax.axvline(0, color="0.4", ls="--", lw=0.8)
        ax.set_yscale("log")
        ax.set_xlabel("push at the cube from neutral (mm); dotted: home stop")
        ax.grid(alpha=0.3, which="both")
        if opt == "washers":
            ax.set_title("Washer target: axis Z %.1f, face X %.1f (gap 1 mm at neutral)" % (H, face), fontsize=10)
        else:
            ax.set_title("Plunger link: axis Z %.1f, face X %.1f (link z %.0f, stroke 3 mm)"
                         % (H, face, pl.REC["z_a"]), fontsize=10)
    axes[0].set_ylabel("resistance at the cube (gf)")
    axes[1].legend(title="AO0 command", fontsize=8)
    fig.suptitle("Washer target vs plunger link on the measured rig (band: pivot depth %.1f-%.1f mm)"
                 % (rg.PIVOT_DEPTHS[0], rg.PIVOT_DEPTHS[-1]))
    save(fig, "options_force_vs_push.png", OUT_FIG)
    plt.close(fig)


def plot_maps(maps):
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    norm = LogNorm(0.1, 100)
    for row, opt in enumerate(("washers", "link")):
        fx, hz, F, ok = maps[opt]
        for col, u in enumerate(F):
            ax = axes[row, col]
            Z = np.clip(F[u], 0.05, 200)
            im = ax.pcolormesh(fx, hz, Z, norm=norm, cmap="magma", shading="auto")
            ax.contourf(fx, hz, (~ok).astype(float), levels=[0.5, 1.5], colors="white", alpha=0.65)
            ax.contour(fx, hz, ok.astype(float), levels=[0.5], colors="cyan", linewidths=1)
            cs = ax.contour(fx, hz, Z, levels=[0.3, 1, 3, 10, 30], colors="0.8", linewidths=0.7)
            ax.clabel(cs, fmt="%g gf", fontsize=7)
            ax.plot(REC[opt]["face"], REC[opt]["H"], "*", color="lime", ms=12, mec="k")
            ax.set_xlabel("Ledex body face X (mm, joystick axis = 0)")
            ax.set_ylabel("Ledex axis Z above the breadboard (mm)")
            ax.set_title("%s, 10 V, push %g mm (pale: not feasible)" % ("Washer target" if opt == "washers"
                                                                         else "Plunger link", u), fontsize=10)
    fig.colorbar(im, ax=axes, label="resistance at the cube (gf)", shrink=0.8)
    save(fig, "design_maps.png", OUT_FIG)
    plt.close(fig)


def main():
    wf = WasherForce()
    tab = pl.plunger_table()
    write_options(wf, tab)
    maps = {opt: design_map(wf, tab, opt) for opt in ("washers", "link")}
    write_maps(maps)
    write_summary(wf, tab, maps)
    plot_options(wf, tab)
    plot_maps(maps)
    u = np.array(TABLE_PUSHES)
    for opt in ("washers", "link"):
        H, face = REC[opt]["H"], REC[opt]["face"]
        for a, name in ((0.074, "1 V"), (0.31, "10 V")):
            F = washer_handle(wf, u, H, face, a)[0] if opt == "washers" else link_handle(tab, u, H, face, a)[0]
            print("%-8s %-5s axis Z %.2f face X %.2f: gf at push %s = %s" % (opt, name, H, face, TABLE_PUSHES,
                                                                          np.round(F, 3)))
    fw = washer_handle(wf, 0.0, REC["washers"]["H"], REC["washers"]["face"], 0.31)[0]
    fl = link_handle(tab, 0.0, REC["link"]["H"], REC["link"]["face"], 0.31)[0]
    print("link / washers at neutral, 10 V: %.0fx" % (np.ravel(fl)[0] / np.ravel(fw)[0]))


if __name__ == "__main__":
    main()
