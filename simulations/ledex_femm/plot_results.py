"""Plot the Ledex FEMM results in results/ (needs numpy and matplotlib; Python 3.6+).

    python plot_results.py            # writes PNGs to figures/plots/ and figures/readable/
    python plot_results.py --show     # also opens the figures

Data: results/sweeps.csv (one row per FEMM solve), results/fieldgrid_*.csv (r, z, Br, Bz, |B| on a
0.25 mm grid), results/calibration/ (datasheet fit and the target-force band) and
results/uncalibrated/ (the first, uncalibrated model, for comparison). See README.md.
"""
import argparse
import csv
import json
import os

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
CAL = os.path.join(RES, "calibration")
OUT = os.path.join(HERE, "figures", "plots")
READABLE = os.path.join(HERE, "figures", "readable")

# measured coil current at each AO command (Checkpoint 4, 11 Oct 2026, Imax at its minimum)
COMMAND_V = {0.053: 0.5, 0.074: 1, 0.106: 2, 0.121: 3, 0.147: 4, 0.180: 5,
             0.201: 6, 0.273: 8, 0.310: 10}

# published geometry (mm), same as ledex_washer.lua
PROTRUDE, RP, RO, LBOSS, RBOSS, SLOTR, SLOTD = 23.81, 3.91, 9.78, 9.52, 6.6, 2.43, 9.5
GEOM = dict(SEAT=0.1, CLR=0.15, TPL=2.5, WALL=1.5)
if os.path.exists(os.path.join(CAL, "best_params.json")):
    with open(os.path.join(CAL, "best_params.json")) as _f:
        GEOM.update(json.load(_f)["params"])


def current_label(a):
    v = COMMAND_V.get(round(a, 3))
    return "{:g} V ({:.3f} A)".format(v, a) if v is not None else "{:.2f} A (Imax raised)".format(a)


def read_csv(path, num=None):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in (num or r.keys()):
            try:
                r[k] = float(r[k])
            except (TypeError, ValueError):
                pass
    return rows


def load_sweeps(path=os.path.join(RES, "sweeps.csv")):
    return read_csv(path, ["target_id_mm", "target_od_mm", "target_t_mm", "protrude_mm", "seat_mm",
                           "stroke_mm", "target_mesh_mm", "gap_mm", "current_A", "target_force_N",
                           "target_force_g", "plunger_force_N"])


def select(rows, **conds):
    out = rows
    for k, v in conds.items():
        if callable(v):
            out = [r for r in out if v(r[k])]
        else:
            out = [r for r in out if r[k] == v]
    return out


def save(fig, name, folder=OUT):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", os.path.relpath(path, HERE))


def load_band():
    path = os.path.join(CAL, "target_band.csv")
    if not os.path.exists(path):
        return None
    band = {}
    for r in read_csv(path):
        band.setdefault((r["gap_mm"], round(r["current_A"], 3)), []).append(r["target_force_g"])
    return {k: (min(v), max(v)) for k, v in band.items()}


def plot_force_vs_gap(rows, band):
    base = select(rows, case=lambda c: c.startswith("baseline_gap"))
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for a in sorted({r["current_A"] for r in base}):
        pts = sorted((r["gap_mm"], r["target_force_g"]) for r in select(base, current_A=a))
        g, f = zip(*pts)
        line, = ax.plot(g, f, "o-", ms=3, label=current_label(a))
        if band:
            bg = [k[0] for k in sorted(band) if k[1] == round(a, 3)]
            if bg:
                lo = [band[(x, round(a, 3))][0] for x in bg]
                hi = [band[(x, round(a, 3))][1] for x in bg]
                ax.errorbar(bg, [(l + h) / 2 for l, h in zip(lo, hi)],
                            yerr=[[(h - l) / 2 for l, h in zip(lo, hi)]] * 2, fmt="none",
                            ecolor=line.get_color(), capsize=3, lw=1.2)
    ax.set_yscale("log")
    ax.set_xlabel("gap between plunger tip and washer stack (mm)")
    ax.set_ylabel("pull on five M3 washers (g-force)")
    ax.set_title("Seated plunger: washer pull vs gap (calibrated model; bars = accepted-fit range)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7, ncol=2)
    save(fig, "force_vs_gap.png")


def plot_force_vs_current(rows, band):
    base = select(rows, case=lambda c: c.startswith("baseline_gap"))
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for g in [0.5, 1, 2, 3, 5]:
        pts = sorted((r["current_A"], r["target_force_g"]) for r in select(base, gap_mm=g))
        if not pts:
            continue
        a, f = zip(*pts)
        line, = ax.plot(a, f, "o-", ms=3, label="gap {:g} mm".format(g))
        if band:
            ba = sorted(k[1] for k in band if k[0] == g)
            if ba:
                ax.fill_between(ba, [band[(g, x)][0] for x in ba], [band[(g, x)][1] for x in ba],
                                color=line.get_color(), alpha=0.2, lw=0)
    for a, v in COMMAND_V.items():
        ax.axvline(a, color="grey", lw=0.5, alpha=0.4)
        ax.text(a, 1.0, "{:g} V".format(v), transform=matplotlib.transforms.blended_transform_factory(ax.transData, ax.transAxes),
                rotation=90, fontsize=6, va="top", ha="right", color="grey")
    ax.axvline(0.31, color="k", ls="--", lw=0.8)
    ax.set_yscale("log")
    ax.set_xlabel("coil current (A); dashed = maximum at the current Imax setting")
    ax.set_ylabel("pull on five M3 washers (g-force)")
    ax.set_title("Washer pull vs coil current (shading = accepted-fit range)")
    ax.grid(True, which="both", alpha=0.3)
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
    for a in sorted({r["current_A"] for r in select(rows, case=lambda c: c.startswith("stroke_"))}):
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
    ax.set_title("Sensitivity of the calibrated model (washers 2 mm)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=7)
    save(fig, "sensitivity.png")


def plot_calibration_fit():
    pts_path = os.path.join(CAL, "fit_points.csv")
    if not os.path.exists(pts_path):
        return
    with open(os.path.join(CAL, "best_params.json")) as f:
        best = json.load(f)
    pts = read_csv(pts_path)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), sharex=True)
    duties = [(100, "7 W"), (50, "14 W, held out of the fit"), (25, "28 W"), (10, "70 W")]
    for ax, (duty, txt) in zip(axes.flat, duties):
        sel = [p for p in pts if p["duty_pct"] == duty]
        cur = sel[0]["current_A"]
        for eid, style, lab in [(0, "--", "model before calibration (published geometry, guessed internals)"),
                                (best["eval"], "-", "calibrated model")]:
            m = sorted((p["stroke_mm"], p["model_N"]) for p in sel if p["eval"] == eid)
            ax.plot(*zip(*m), style, color="C0" if eid else "grey", label=lab)
        d = sorted((p["stroke_mm"], p["datasheet_N"]) for p in sel if p["eval"] == 0)
        ax.plot(*zip(*d), "o", color="C3", ms=4, label="datasheet (digitized)")
        if duty == 100 and os.path.exists(os.path.join(RES, "uncalibrated", "stroke.csv")):
            old = read_csv(os.path.join(RES, "uncalibrated", "stroke.csv"))
            o = sorted((r["stroke_mm"], r["plunger_force_N"]) for r in old if abs(r["current_A"] - 0.58) < 1e-3)
            ax.plot(*zip(*o), "x", color="k", ms=6, label="first model (9.5 mm protrusion), 0.58 A")
        ax.set_title("{} % duty, {} ({:.2f} A)".format(duty, txt, cur), fontsize=10)
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
    for ax in axes[1]:
        ax.set_xlabel("stroke: plunger out from its seat (mm)")
    for ax in axes[:, 0]:
        ax.set_ylabel("force on plunger (N)")
    axes[0, 0].legend(fontsize=7, loc="upper right")
    fig.suptitle("Plunger force: datasheet vs model (60-degree plunger)\n"
                 "RMS error of ln(model/datasheet): fit {:.2f}, held-out curve {:.2f}".format(
                     best["err_fit"], best["err_holdout"]))
    save(fig, "calibration_fit.png")


def plot_target_band(rows, band):
    if not band:
        return
    old = load_sweeps(os.path.join(RES, "uncalibrated", "sweeps.csv"))
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    for ax, g in zip(axes, [1, 2, 3]):
        ba = sorted(k[1] for k in band if k[0] == g)
        ax.fill_between(ba, [band[(g, a)][0] for a in ba], [band[(g, a)][1] for a in ba],
                        color="C0", alpha=0.25, lw=0, label="accepted fits (range)")
        cal = sorted((r["current_A"], r["target_force_g"]) for r in rows
                     if r["case"] == "baseline_gap{:g}".format(g))
        ax.plot(*zip(*cal), "o-", color="C0", ms=3, label="best fit")
        un = sorted((r["current_A"], r["target_force_g"]) for r in old if r["case"] == "baseline_gap{:g}".format(g))
        ax.plot(*zip(*un), "--", color="grey", label="first model (uncalibrated)")
        ax.set_title("gap {} mm".format(g))
        ax.set_xlabel("coil current (A); 10 V = 0.31 A")
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
    axes[0].set_ylabel("pull on five M3 washers (g-force)")
    axes[0].legend(fontsize=7)
    fig.suptitle("Target force after calibration against the datasheet")
    save(fig, "target_force_band.png")


def load_grid(path):
    d = np.loadtxt(path, delimiter=",", skiprows=1)
    r = np.unique(d[:, 0])
    z = np.unique(d[:, 1])
    shape = (len(z), len(r))
    return r, z, d[:, 2].reshape(shape), d[:, 3].reshape(shape), d[:, 4].reshape(shape)


def plot_axial_profile():
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for a in [0.074, 0.106, 0.180, 0.310, 0.580]:
        path = os.path.join(RES, "fieldgrid_notarget_{:.3f}A.csv".format(a))
        if not os.path.exists(path):
            continue
        r, z, br, bz, bm = load_grid(path)
        sel = z <= -PROTRUDE
        ax.plot(-PROTRUDE - z[sel], bm[sel, 0] * 1000, label=current_label(a))
    ax.set_xlabel("distance in front of the plunger tip, on axis (mm)")
    ax.set_ylabel("|B| (mT)")
    ax.set_title("On-axis field in front of the tip, no target")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7)
    save(fig, "axial_profile.png")


XMIN, XMAX, YMAX = -5, 40, 14


def draw_half_panel(ax, tag, gap, a, vmax=50.0):
    """Side view with the solenoid axis horizontal (bottom edge). Body on the left, plunger tip pointing
    right toward the target. Only the half above the axis (r >= 0) is drawn."""
    r, z, br, bz, bm = load_grid(os.path.join(RES, "fieldgrid_{}_{:.3f}A.csv".format(tag, a)))
    x = -z[::-1]                          # x = distance along the axis, increasing toward the tip side
    flip = lambda m: m[::-1, :].T         # shape (len(r), len(x))
    im = ax.pcolormesh(x, r, np.clip(flip(bm) * 1000, 0, vmax), vmin=0, vmax=vmax, cmap="inferno", shading="auto")
    ax.streamplot(x, r, -flip(bz), flip(br), color="w", linewidth=0.4, density=1.0, arrowsize=0.5)
    rb = RP + GEOM["CLR"]
    rki = RO - GEOM["WALL"]
    tpl = GEOM["TPL"]
    kw = dict(color="c", lw=0.9)
    ax.plot([XMIN, PROTRUDE, PROTRUDE, PROTRUDE - SLOTD, PROTRUDE - SLOTD],
            [RP, RP, SLOTR, SLOTR, 0], **kw)                                    # plunger with tip slot
    ax.plot([XMIN, LBOSS, LBOSS, 0, 0, XMIN], [rb, rb, RBOSS, RBOSS, RO, RO], **kw)  # bore, boss, body face
    ax.plot([XMIN, -tpl, -tpl], [rki, rki, rb], **kw)                          # case wall, front plate
    if gap is not None:
        x2 = PROTRUDE + gap
        ax.add_patch(plt.Rectangle((x2, 1.6), 4, 2.9, fill=False, ec="c", lw=1.2))
        ax.text(x2 + 2, 5.0, "target", color="c", fontsize=7, ha="center", va="bottom")
    ax.text(LBOSS / 2, RBOSS + 0.3, "boss", color="c", fontsize=7, ha="center", va="bottom")
    ax.text(XMIN + 0.3, RO + 0.3, "body", color="c", fontsize=7, ha="left", va="bottom")
    ax.axhline(0, color="grey", lw=0.6, ls=":")
    ax.set_aspect("equal")
    ax.set_xlim(XMIN, XMAX)
    ax.set_ylim(0, YMAX)
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
        "part is round: spin it around the bottom edge to get the full shape.\n0 mm = front face of the solenoid body, "
        "plunger tip (23.8 mm out) points right. White lines = field direction; cyan = body, boss, plunger, target.")


def plot_readable():
    """Readable field figures in figures/readable/: one overview (half sections) and one PNG per panel."""
    top = [0.074, 0.106, 0.180, 0.310, 0.580]
    bottom = [0.074, 0.310, 0.580]
    panels = [("notarget", None, a) for a in top] + [("washers5_gap2mm", 2, a) for a in bottom]
    if not all(os.path.exists(os.path.join(RES, "fieldgrid_{}_{:.3f}A.csv".format(t, a))) for t, _, a in panels):
        return
    os.makedirs(READABLE, exist_ok=True)
    fig = plt.figure(figsize=(20, 7))
    gs = fig.add_gridspec(2, 6, width_ratios=[1, 1, 1, 1, 1, 0.04], wspace=0.25, hspace=0.35)
    im = None
    for j, p in enumerate(panels[:5]):
        im = draw_half_panel(fig.add_subplot(gs[0, j]), *p)
    for j, p in enumerate(panels[5:]):
        im = draw_half_panel(fig.add_subplot(gs[1, j]), *p)
    style_colorbar(fig.colorbar(im, cax=fig.add_subplot(gs[:, 5]), extend="max"))
    fig.suptitle("Ledex field around the plunger tip (calibrated model)\n" + NOTE, fontsize=10)
    save(fig, "overview_readable.png", READABLE)
    for tag, gap, a in panels:
        fig, ax = plt.subplots(figsize=(10, 4))
        im = draw_half_panel(ax, tag, gap, a)
        style_colorbar(fig.colorbar(im, ax=ax, extend="max", shrink=0.8, pad=0.03))
        fig.text(0.5, 0.0, NOTE, ha="center", va="top", fontsize=6.5)
        name = "{}_{:.3f}A.png".format("notarget" if gap is None else "target_gap2mm", a)
        save(fig, name, READABLE)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--show", action="store_true")
    args = p.parse_args()
    if args.show:
        plt.close = lambda *a, **k: None
    rows = load_sweeps()
    band = load_band()
    plot_force_vs_gap(rows, band)
    plot_force_vs_current(rows, band)
    plot_targets(rows)
    plot_stroke(rows)
    plot_sensitivity(rows)
    plot_calibration_fit()
    plot_target_band(rows, band)
    plot_axial_profile()
    plot_readable()
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
