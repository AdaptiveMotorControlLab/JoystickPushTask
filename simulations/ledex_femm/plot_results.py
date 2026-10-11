"""Plot the Ledex FEMM results in results/ (needs numpy and matplotlib; Python 3.6+).

    python plot_results.py            # writes PNGs to figures/plots/
    python plot_results.py --show     # also opens the figures

All data come from results/sweeps.csv (one row per FEMM solve) and results/fieldgrid_*.csv
(r, z, Br, Bz, |B| on a 0.25 mm grid). See README.md for the columns and the model caveats.
"""
import argparse
import csv
import glob
import os
import re

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(HERE, "figures", "plots")

# measured coil current at each AO command (Checkpoint 4, 11 Oct 2026, Imax at its minimum)
COMMAND_V = {0.053: 0.5, 0.074: 1, 0.106: 2, 0.121: 3, 0.147: 4, 0.180: 5,
             0.201: 6, 0.273: 8, 0.310: 10}
PROTRUDE = 9.5  # default plunger protrusion in the model (mm)


def current_label(a):
    v = COMMAND_V.get(round(a, 3))
    return "{:g} V ({:.3f} A)".format(v, a) if v is not None else "{:.2f} A (Imax raised)".format(a)


def load_sweeps():
    with open(os.path.join(RES, "sweeps.csv")) as f:
        rows = list(csv.DictReader(f))
    num = ["target_id_mm", "target_od_mm", "target_t_mm", "protrude_mm", "seat_mm", "stroke_mm",
           "target_mesh_mm", "gap_mm", "current_A", "target_force_N", "target_force_g", "plunger_force_N"]
    for r in rows:
        for k in num:
            r[k] = float(r[k])
    return rows


def select(rows, **conds):
    out = rows
    for k, v in conds.items():
        if callable(v):
            out = [r for r in out if v(r[k])]
        else:
            out = [r for r in out if r[k] == v]
    return out


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print("wrote", os.path.relpath(path, HERE))


def plot_force_vs_gap(rows):
    base = select(rows, case=lambda c: c.startswith("baseline_gap"))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for a in sorted({r["current_A"] for r in base}):
        pts = sorted((r["gap_mm"], r["target_force_g"]) for r in select(base, current_A=a))
        g, f = zip(*pts)
        ax.plot(g, f, "o-", ms=3, label=current_label(a))
    ax.set_yscale("log")
    ax.set_xlabel("gap between plunger tip and washer stack (mm)")
    ax.set_ylabel("pull on five M3 washers (g-force)")
    ax.set_title("Seated plunger: washer pull vs gap (1 g = 9.81 mN)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7, ncol=2)
    save(fig, "force_vs_gap.png")


def plot_force_vs_current(rows):
    base = select(rows, case=lambda c: c.startswith("baseline_gap"))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for g in [0.5, 1, 2, 3, 5]:
        pts = sorted((r["current_A"], r["target_force_g"]) for r in select(base, gap_mm=g))
        if pts:
            a, f = zip(*pts)
            ax.plot(a, f, "o-", ms=3, label="gap {:g} mm".format(g))
    for a, v in COMMAND_V.items():
        ax.axvline(a, color="grey", lw=0.5, alpha=0.4)
        ax.text(a, 1.0, "{:g} V".format(v), transform=matplotlib.transforms.blended_transform_factory(ax.transData, ax.transAxes),
                rotation=90, fontsize=6, va="top", ha="right", color="grey")
    ax.axvline(0.31, color="k", ls="--", lw=0.8)
    ax.set_xlabel("coil current (A); dashed = maximum at the current Imax setting")
    ax.set_ylabel("pull on five M3 washers (g-force)")
    ax.set_title("Washer pull vs coil current")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    save(fig, "force_vs_current.png")


def plot_targets(rows):
    tg = select(rows, case=lambda c: c.startswith("target_") or c.startswith("baseline_gap"))
    names = ["washers1_M3", "washers3_M3", "washers5_M3", "disc_8x4_solid", "disc_9x4_solid",
             "disc_12x4_solid", "disc_16x6_solid"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, a in zip(axes, [0.310, 0.58]):
        for n in names:
            pts = sorted({(r["gap_mm"], r["target_force_g"]) for r in select(tg, target=n, current_A=a)
                          if r["gap_mm"] in (1, 2, 3, 5)})
            if pts:
                g, f = zip(*pts)
                ax.plot(g, f, "o-", ms=3, label=n)
        ax.set_yscale("log")
        ax.set_title(current_label(a))
        ax.set_xlabel("gap (mm)")
        ax.grid(True, which="both", alpha=0.3)
    axes[0].set_ylabel("pull on target (g-force)")
    axes[1].legend(fontsize=7)
    fig.suptitle("Effect of the steel target (mild steel, plunger seated)")
    save(fig, "targets.png")


def plot_stroke(rows):
    st = select(rows, case=lambda c: c.startswith("stroke_") or c == "baseline_gap2")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for a in sorted({r["current_A"] for r in st}):
        pts = sorted({(r["stroke_mm"], r["target_force_g"], r["plunger_force_N"])
                      for r in select(st, current_A=a)})
        if len(pts) < 2:
            continue
        s, fw, fp = zip(*pts)
        axes[0].plot(s, fw, "o-", ms=3, label=current_label(a))
        axes[1].plot(s, fp, "o-", ms=3, label=current_label(a))
    axes[0].set_ylabel("pull on washers 2 mm from the tip (g-force)")
    axes[1].set_ylabel("force on plunger (N)")
    for ax in axes:
        ax.set_xlabel("plunger held out from its seat (mm)")
        ax.grid(True, alpha=0.3)
    axes[0].legend(fontsize=7)
    fig.suptitle("Seated plunger gives the strongest washer pull")
    save(fig, "stroke.png")


def plot_sensitivity(rows):
    sens = select(rows, case=lambda c: c.startswith("sens_"))
    ref = {r["current_A"]: r["target_force_N"] for r in select(sens, case="sens_reference")}
    cases = [c for c in dict.fromkeys(r["case"] for r in sens) if c != "sens_reference"]
    amps = sorted(ref)
    fig, ax = plt.subplots(figsize=(9, 4))
    w = 0.8 / len(amps)
    for i, a in enumerate(amps):
        vals = []
        for c in cases:
            m = select(sens, case=c, current_A=a)
            vals.append(m[0]["target_force_N"] / ref[a] if m else np.nan)
        ax.bar(np.arange(len(cases)) + i * w, vals, w, label=current_label(a))
    ax.axhline(1, color="k", lw=0.8)
    ax.set_xticks(np.arange(len(cases)) + w * (len(amps) - 1) / 2)
    ax.set_xticklabels([c.replace("sens_", "") for c in cases], rotation=30, ha="right")
    ax.set_ylabel("washer pull / reference")
    ax.set_title("Sensitivity to assumed parameters (washers 2 mm)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=7)
    save(fig, "sensitivity.png")


def load_grid(path):
    d = np.loadtxt(path, delimiter=",", skiprows=1)
    r = np.unique(d[:, 0])
    z = np.unique(d[:, 1])
    shape = (len(z), len(r))
    return r, z, d[:, 2].reshape(shape), d[:, 3].reshape(shape), d[:, 4].reshape(shape)


def draw_outline(ax, gap=None):
    kw = dict(color="c", lw=0.7)
    for s in (1, -1):
        ax.plot([s * 3.91, s * 3.91, 0], [5, -PROTRUDE, -PROTRUDE], **kw)        # plunger side and tip
        ax.plot([s * 4.06, s * 9.78, s * 9.78], [0, 0, 5], **kw)                  # front face, case wall
        ax.plot([s * 4.06, s * 4.06, s * 8.28, s * 8.28], [0, 2.5, 2.5, 5], **kw)  # bore, front plate
        if gap is not None:
            z2 = -PROTRUDE - gap
            ax.add_patch(plt.Rectangle((1.6 if s > 0 else -4.5, z2 - 4), 2.9, 4, fill=False, ec="c", lw=0.8))


def plot_fieldmaps():
    files = sorted(glob.glob(os.path.join(RES, "fieldgrid_*.csv")))
    if not files:
        return
    groups = [("notarget", None), ("washers5_gap2mm", 2)]
    amps = sorted({float(re.search(r"_([0-9.]+)A\.csv$", f).group(1)) for f in files})
    fig, axes = plt.subplots(len(groups), len(amps), figsize=(2.9 * len(amps) + 1, 3.6 * len(groups)),
                             squeeze=False, constrained_layout=True)
    norm = LogNorm(vmin=1e-3, vmax=0.3)
    im = None
    for gi, (tag, gap) in enumerate(groups):
        for ai, a in enumerate(amps):
            ax = axes[gi][ai]
            path = os.path.join(RES, "fieldgrid_{}_{:.3f}A.csv".format(tag, a))
            if not os.path.exists(path):
                ax.axis("off")
                continue
            r, z, br, bz, bm = load_grid(path)
            rr = np.concatenate([-r[:0:-1], r])
            bmf = np.concatenate([bm[:, :0:-1], bm], axis=1)
            brf = np.concatenate([-br[:, :0:-1], br], axis=1)
            bzf = np.concatenate([bz[:, :0:-1], bz], axis=1)
            im = ax.pcolormesh(rr, z, np.clip(bmf, 1e-4, None), norm=norm, cmap="magma", shading="auto")
            ax.streamplot(rr, z, brf, bzf, color="w", linewidth=0.4, density=1.2, arrowsize=0.5)
            draw_outline(ax, gap)
            ax.set_aspect("equal")
            ax.set_xlim(-14, 14)
            ax.set_ylim(-25, 5)
            ax.set_title(("no target, " if gap is None else "washers 2 mm, ") + current_label(a), fontsize=8)
            ax.set_xlabel("r (mm)", fontsize=7)
            if ai == 0:
                ax.set_ylabel("z (mm), case front face at 0", fontsize=7)
            ax.tick_params(labelsize=6)
    fig.colorbar(im, ax=axes, shrink=0.6, label="|B| (T), log scale")
    fig.suptitle("Field around the seated plunger tip (model, axisymmetric)")
    save(fig, "fieldmaps.png")


def draw_half_panel(ax, tag, gap, a, vmax=50.0):
    """Side view with the solenoid axis horizontal (bottom edge). Back of the coil on the left, plunger tip pointing
    right toward the target. Only the half above the axis (r >= 0) is drawn."""
    r, z, br, bz, bm = load_grid(os.path.join(RES, "fieldgrid_{}_{:.3f}A.csv".format(tag, a)))
    x = -z[::-1]                          # x = distance along the axis, increasing toward the tip side
    flip = lambda m: m[::-1, :].T         # shape (len(r), len(x))
    im = ax.pcolormesh(x, r, np.clip(flip(bm) * 1000, 0, vmax), vmin=0, vmax=vmax, cmap="inferno", shading="auto")
    ax.streamplot(x, r, -flip(bz), flip(br), color="w", linewidth=0.4, density=1.0, arrowsize=0.5)
    kw = dict(color="c", lw=0.9)
    ax.plot([-5, PROTRUDE, PROTRUDE], [3.91, 3.91, 0], **kw)           # plunger side and tip
    ax.plot([0, 0, -5], [4.06, 9.78, 9.78], **kw)                      # front face, case wall
    ax.plot([0, -2.5, -2.5, -5], [4.06, 4.06, 8.28, 8.28], **kw)       # bore, front plate
    if gap is not None:
        x2 = PROTRUDE + gap
        ax.add_patch(plt.Rectangle((x2, 1.6), 4, 2.9, fill=False, ec="c", lw=1.2))
        ax.text(x2 + 2, 5.0, "target", color="c", fontsize=7, ha="center", va="bottom")
    ax.axhline(0, color="grey", lw=0.6, ls=":")
    ax.set_aspect("equal")
    ax.set_xlim(-5, 25)
    ax.set_ylim(0, 14)
    ax.set_title(("No target, " if gap is None else "Target 2 mm from tip, ") + current_label(a), fontsize=9)
    ax.set_xlabel("position along the axis (mm)", fontsize=7)
    ax.set_ylabel("distance from axis (mm)", fontsize=8)
    return im


def style_colorbar(cb):
    cb.set_ticks([0, 10, 20, 30, 40, 50])
    cb.set_ticklabels(["0 mT (no field)", "10 mT", "20 mT", "30 mT", "40 mT", "50 mT or more"])
    cb.set_label("field strength |B| in mT (brighter = stronger)", fontsize=9)
    cb.ax.tick_params(labelsize=8)


NOTE = ("Side view, cut through the solenoid axis (bottom edge, dotted); only the half above the axis is drawn because the\n"
        "part is round: spin it around the bottom edge to get the full shape.\n0 mm = front face of the solenoid, plunger tip points right. White lines = field direction; cyan = case, plunger, target.")


def plot_readable():
    """Readable field figures in figures/readable/: one overview (half sections) and one PNG per panel."""
    top = [0.074, 0.106, 0.180, 0.310, 0.580]
    bottom = [0.074, 0.310, 0.580]
    panels = [("notarget", None, a) for a in top] + [("washers5_gap2mm", 2, a) for a in bottom]
    if not all(os.path.exists(os.path.join(RES, "fieldgrid_{}_{:.3f}A.csv".format(t, a))) for t, _, a in panels):
        return
    out = os.path.join(HERE, "figures", "readable")
    os.makedirs(out, exist_ok=True)
    no_target = panels[:5]
    with_target = panels[5:]
    fig = plt.figure(figsize=(18, 8))
    gs = fig.add_gridspec(2, 6, width_ratios=[1, 1, 1, 1, 1, 0.05], wspace=0.25, hspace=0.35)
    im = None
    for j, p in enumerate(no_target):
        im = draw_half_panel(fig.add_subplot(gs[0, j]), *p)
    for j, p in enumerate(with_target):
        im = draw_half_panel(fig.add_subplot(gs[1, j]), *p)
    style_colorbar(fig.colorbar(im, cax=fig.add_subplot(gs[:, 5]), extend="max"))
    fig.suptitle("Ledex field around the plunger tip\n" + NOTE, fontsize=10)
    path = os.path.join(out, "overview_readable.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", os.path.relpath(path, HERE))
    for tag, gap, a in panels:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        im = draw_half_panel(ax, tag, gap, a)
        style_colorbar(fig.colorbar(im, ax=ax, extend="max", shrink=0.8, pad=0.03))
        fig.text(0.5, 0.0, NOTE, ha="center", va="top", fontsize=6.5)
        name = "{}_{:.3f}A.png".format("notarget" if gap is None else "target_gap2mm", a)
        fig.savefig(os.path.join(out, name), dpi=150, bbox_inches="tight")
        plt.close(fig)
        print("wrote figures/readable/" + name)


def plot_axial_profile():
    files = sorted(glob.glob(os.path.join(RES, "fieldgrid_notarget_*.csv")))
    if not files:
        return
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for f in files:
        a = float(re.search(r"_([0-9.]+)A\.csv$", f).group(1))
        r, z, br, bz, bm = load_grid(f)
        sel = z <= -PROTRUDE
        ax.plot(-PROTRUDE - z[sel], bm[sel, 0] * 1000, label=current_label(a))
    ax.set_xlabel("distance in front of the plunger tip, on axis (mm)")
    ax.set_ylabel("|B| (mT)")
    ax.set_title("On-axis field in front of the tip, no target")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7)
    save(fig, "axial_profile.png")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--show", action="store_true")
    args = p.parse_args()
    rows = load_sweeps()
    plot_force_vs_gap(rows)
    plot_force_vs_current(rows)
    plot_targets(rows)
    plot_stroke(rows)
    plot_sensitivity(rows)
    plot_fieldmaps()
    plot_readable()
    plot_axial_profile()
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
