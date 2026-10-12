"""Plot the Ledex FEMM results in results/ (needs numpy and matplotlib; Python 3.6+).

    python plot_results.py            # writes PNGs to figures/plots/ (field maps: plot_target_across.py)
    python plot_results.py --show     # also opens the figures

Force and field figures come from the 3D model (washer tower standing across the axis):
results/fea3d.csv and results/fea3d_sweep.csv (sweep3d.py) and results/axial_B3d.csv.
calibration_fit.png and sensitivity.png stay on the 2D FEMM model: results/calibration/ and
results/sweeps.csv. results/uncalibrated/ is the first model, kept for the record (not plotted).
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

# measured coil current at each AO command (Checkpoint 4, 11 Oct 2026, Imax at its minimum)
COMMAND_V = {0.053: 0.5, 0.074: 1, 0.106: 2, 0.121: 3, 0.147: 4, 0.180: 5,
             0.201: 6, 0.273: 8, 0.310: 10}

# fitted internals, used for the outlines in the field figures
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
    for ax in fig.axes:
        if ax.get_yscale() == "log":
            plain_log(ax)
    path = os.path.join(folder, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", os.path.relpath(path, HERE))


def plain_log(ax):
    """Log y axis with plain-number labels at 1-2-5 steps (0.05, 0.1, 0.2, 0.5, 1, 2, 5, ...)."""
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
    lo, hi = ax.get_ylim()
    ticks = [m * 10.0 ** e for e in range(-4, 4) for m in (1, 2, 5) if lo / 1.01 <= m * 10.0 ** e <= hi * 1.01]
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "{:g}".format(v)))
    ax.grid(True, axis="y", which="major", alpha=0.3)


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
        ax.set_title("{} % duty, {} ({:.2f} A)".format(duty, txt, cur), fontsize=10)
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
    for ax in axes[1]:
        ax.set_xlabel("stroke: plunger out from its seat (mm)")
    for ax in axes[:, 0]:
        ax.set_ylabel("force on plunger (N)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.suptitle("Plunger force: datasheet vs model (60-degree plunger)\n"
                 "RMS error of ln(model/datasheet): fit {:.2f}, held-out curve {:.2f}".format(
                     best["err_fit"], best["err_holdout"]), y=1.0)
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.95), ncol=2, fontsize=8, frameon=True)
    fig.subplots_adjust(top=0.84, hspace=0.12, wspace=0.18)
    save(fig, "calibration_fit.png")


LBL10 = "pull on the 10-washer tower (g-force)"


def load3d():
    """3D results (washer tower across the axis): {(set, n, gap, stroke, current): force_g}."""
    d = {}
    old = os.path.join(RES, "fea3d.csv")
    if os.path.exists(old):
        for r in read_csv(old):
            if r["kind"] == "across":
                d[("best", int(r["n_washers"]), r["gap_mm"], 0.0, round(r["current_A"], 3))] = r["force_g"]
    path = os.path.join(RES, "fea3d_sweep.csv")
    if os.path.exists(path):
        for r in read_csv(path):
            s = r["set"] if isinstance(r["set"], str) else "%d" % r["set"]
            d[(s, int(r["n_washers"]), r["gap_mm"], r["stroke_mm"], round(r["current_A"], 3))] = r["force_g"]
    return d


def band3d(d, gap, a):
    """Range of the 10-washer pull over the accepted calibration sets (3D), or None."""
    v = [f for (s, n, g, st, i), f in d.items() if n == 10 and g == gap and st == 0 and i == round(a, 3)]
    return (min(v), max(v)) if len(v) > 2 else None


def series(d, n=10, a=0.31):
    """Gap and pull for the fitted model, plunger seated."""
    pts = sorted((k[2], f) for k, f in d.items() if k[0] == "best" and k[1] == n and k[3] == 0 and k[4] == round(a, 3))
    return list(zip(*pts)) if pts else ([], [])


def plot_force_vs_gap(d):
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for a in [0.074, 0.106, 0.180, 0.310, 0.580]:
        g, f = series(d, a=a)
        line, = ax.plot(g, f, "o-", ms=3, label=current_label(a))
        bg = [x for x in (1.0, 2.0, 3.0) if band3d(d, x, a)]
        if bg:
            lo, hi = zip(*[band3d(d, x, a) for x in bg])
            ax.errorbar(bg, [(l + h) / 2 for l, h in zip(lo, hi)], yerr=[[(h - l) / 2 for l, h in zip(lo, hi)]] * 2,
                        fmt="none", ecolor=line.get_color(), capsize=3, lw=1.2)
    ax.set_yscale("log")
    ax.set_xlabel("gap between plunger tip and washer rims (mm)")
    ax.set_ylabel(LBL10)
    ax.set_title("Seated plunger: washer pull vs gap (3D model; bars = accepted calibration fits)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7, ncol=2)
    save(fig, "force_vs_gap.png")


def plot_force_vs_current(d):
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for g in [0.5, 1.0, 2.0, 3.0, 5.0]:
        pts = sorted((k[4], f) for k, f in d.items() if k[0] == "best" and k[1] == 10 and k[2] == g and k[3] == 0)
        if not pts:
            continue
        a, f = zip(*pts)
        line, = ax.plot(a, f, "o-", ms=3, label="gap {:g} mm".format(g))
        ba = [x for x in (0.074, 0.310, 0.580) if band3d(d, g, x)]
        if len(ba) > 1:
            ax.fill_between(ba, [band3d(d, g, x)[0] for x in ba], [band3d(d, g, x)[1] for x in ba],
                            color=line.get_color(), alpha=0.2, lw=0)
    for a, v in COMMAND_V.items():
        ax.axvline(a, color="grey", lw=0.5, alpha=0.4)
        ax.text(a, 1.0, "{:g} V".format(v), transform=matplotlib.transforms.blended_transform_factory(ax.transData, ax.transAxes),
                rotation=90, fontsize=6, va="top", ha="right", color="grey")
    ax.axvline(0.31, color="k", ls="--", lw=0.8)
    ax.set_yscale("log")
    ax.set_xlabel("coil current (A); dashed = maximum at the current Imax setting")
    ax.set_ylabel(LBL10)
    ax.set_title("Washer pull vs coil current (3D model; shading = accepted calibration fits)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    save(fig, "force_vs_current.png")


def plot_targets(d):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.5), sharey=True)
    for ax, a in zip(axes, [0.310, 0.580]):
        for n in (1, 5, 10, 20, 40):
            g, f = series(d, n=n, a=a)
            g, f = zip(*[(x, y) for x, y in zip(g, f) if x in (1, 2, 3, 5)]) if g else ((), ())
            if g:
                ax.plot(g, f, "o-", ms=3, label="{} washer{}".format(n, "" if n == 1 else "s"))
        ax.set_yscale("log")
        ax.set_title(current_label(a))
        ax.set_xlabel("gap (mm)")
        ax.grid(True, which="both", alpha=0.3)
    axes[0].set_ylabel("pull on the washer tower (g-force)")
    axes[1].legend(fontsize=7, loc="center left", bbox_to_anchor=(1.02, 0.5),
                   title="M3 washers in the tower\n(0.8 mm thick each)", title_fontsize=7)
    fig.suptitle("Pull on washer towers of different height standing across the axis (3D model, plunger seated)")
    save(fig, "targets.png")


def plot_stroke(d):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for a in [0.074, 0.180, 0.310, 0.580]:
        pts = sorted((k[3], f) for k, f in d.items() if k[0] == "best" and k[1] == 10 and k[2] == 2.0 and k[4] == round(a, 3))
        if len(pts) > 1:
            ax.plot(*zip(*pts), "o-", ms=3, label=current_label(a))
    ax.set_yscale("log")
    ax.set_xlabel("plunger held out from its seat (mm); washers stay 2 mm from the tip")
    ax.set_ylabel(LBL10)
    ax.set_title("Seated plunger gives the strongest washer pull (3D model)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7)
    save(fig, "stroke.png")


def plot_force_vs_washers(d):
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2), sharey=True)
    for ax, g in zip(axs, (1.0, 2.0, 3.0)):
        for a, c in ((0.31, "tab:blue"), (0.58, "tab:red")):
            pts = sorted((k[1], f) for k, f in d.items() if k[0] == "best" and k[2] == g and k[3] == 0 and k[4] == a)
            ax.plot(*zip(*pts), marker="o", color=c, label="{} A".format(a))
        ax.set_title("gap {:g} mm".format(g))
        ax.set_xlabel("washers in the tower")
        ax.grid(alpha=0.3)
    axs[0].set_ylabel("pull on the washer tower (g-force)")
    axs[0].legend(fontsize=8)
    save(fig, "force_vs_washers_across.png")


def plot_target_band(d):
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    for ax, g in zip(axes, [1.0, 2.0, 3.0]):
        ba = [x for x in (0.074, 0.310, 0.580) if band3d(d, g, x)]
        if len(ba) > 1:
            ax.fill_between(ba, [band3d(d, g, a)[0] for a in ba], [band3d(d, g, a)[1] for a in ba],
                            color="C0", alpha=0.25, lw=0, label="accepted fits (range)")
        a, f = zip(*sorted((k[4], v) for k, v in d.items() if k[0] == "best" and k[1] == 10 and k[2] == g and k[3] == 0))
        ax.plot(a, f, "o-", color="C0", ms=3, label="best fit")
        ax.set_title("gap {:g} mm".format(g))
        ax.set_xlabel("coil current (A); 10 V = 0.31 A")
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
    axes[0].set_ylabel(LBL10)
    axes[0].legend(fontsize=7)
    fig.suptitle("Washer pull with the calibration uncertainty (3D model, 16 accepted calibration sets)")
    save(fig, "target_force_band.png")


def plot_axial_profile():
    path = os.path.join(RES, "axial_B3d.csv")
    if not os.path.exists(path):
        return
    rows = read_csv(path)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for a in sorted({r["current_A"] for r in rows}):
        pts = sorted((r["dist_mm"], r["B_T"] * 1000) for r in rows if r["current_A"] == a)
        ax.plot(*zip(*pts), label=current_label(a))
    ax.set_xlabel("distance in front of the plunger tip, along its outer edge r = 3.9 mm (mm)")
    ax.set_ylabel("|B| (mT)")
    ax.set_title("Field in front of the tip along the plunger edge, no target (3D model)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7)
    save(fig, "axial_profile.png")


def style_colorbar(cb):
    cb.set_ticks([0, 10, 20, 30, 40, 50])
    cb.set_ticklabels(["0 mT (no field)", "10 mT", "20 mT", "30 mT", "40 mT", "50 mT or more"])
    cb.set_label("field strength |B| in mT (brighter = stronger)", fontsize=9)
    cb.ax.tick_params(labelsize=8)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--show", action="store_true")
    args = p.parse_args()
    if args.show:
        plt.close = lambda *a, **k: None
    rows = load_sweeps()
    d = load3d()
    plot_force_vs_gap(d)
    plot_force_vs_current(d)
    plot_targets(d)
    plot_force_vs_washers(d)
    plot_stroke(d)
    plot_sensitivity(rows)          # FEMM (2D) on purpose, like the calibration fit
    plot_calibration_fit()
    plot_target_band(d)
    plot_axial_profile()
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
