"""All readable field figures from the 3D model (washer tower standing across the axis).

The tower of ten washers stands across the solenoid axis (its own axis is vertical in the figure) and
its rim faces the plunger tip. Needs the 3D model, so run with the NGSolve venv:
    /tmp/ngenv/bin/python plot_target_across.py
Optional args: currents in A (default 0.074 0.310 0.580). Writes figures/readable/notarget_*A.png, target_gap2mm_*A.png and overview_readable.png.
Solved fields are cached in results/fieldcache3d_*.npz.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import fea3d
from plot_results import current_label, style_colorbar, GEOM

HERE = os.path.dirname(os.path.abspath(__file__))
READ = os.path.join(HERE, "figures", "readable")
N, GAPS = 10, (1.0, 2.0, 3.0)
AMPS = [0.074, 0.106, 0.180, 0.310, 0.580]
PROTRUDE, RP, RO, LBOSS, RBOSS, SLOTD = 23.81, 3.91, 9.78, 9.52, 6.6, 9.5
XMIN, XMAX, YMAX = -5, 40, 14

NOTE = ("Side view, cut through the solenoid axis (horizontal, dotted) and the axis of the washer tower (vertical).\n"
        "0 mm = front face of the solenoid body, plunger tip (23.8 mm out) points right. Target = ten M3 washers "
        "(8 mm tall, 9 mm across) standing\non top of each other across the axis, rim 1, 2 or 3 mm from the tip (see panel title).\n"
        "White lines = field direction; cyan = body, boss, plunger, washers (dotted = hole).")


NOTE_NT = ("Side view, cut through the solenoid axis (horizontal, dotted).\n"
           "0 mm = front face of the solenoid body, plunger tip (23.8 mm out) points right; no target.\n"
           "White lines = field direction; cyan = body, boss, plunger.")


def sample(m, xs, ys):
    """Bx-free field in the plane x = 0: returns |B|, B_axis (toward +position), B_y in tesla."""
    B = fea3d.curl(m.gfu)
    zs = -xs
    mag = np.full((len(ys), len(xs)), np.nan)
    by = np.zeros_like(mag)
    bz = np.zeros_like(mag)
    for i, y in enumerate(ys):
        for j, z in enumerate(zs):
            try:
                v = B(m.mesh(0.0, abs(y), z))
            except Exception:
                continue
            mag[i, j] = np.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
            by[i, j] = v[1] * (1 if y >= 0 else -1)     # B_y is odd under the y mirror, B_z even
            bz[i, j] = v[2]
    return mag, by, bz


def draw(ax, xs, ys, mag, by, bz, a, tgt, gap=2.0):
    im = ax.pcolormesh(xs, ys, np.clip(np.nan_to_num(mag) * 1000, 0, 50), vmin=0, vmax=50, cmap="inferno",
                       shading="auto")
    ax.streamplot(xs, ys, -np.nan_to_num(bz), np.nan_to_num(by), color="w", linewidth=0.4, density=1.3,
                  arrowsize=0.5)
    rb = RP + GEOM["CLR"]
    rki = RO - GEOM["WALL"]
    tpl = GEOM["TPL"]
    kw = dict(color="c", lw=0.9)
    for s in (1, -1):
        ax.plot([XMIN, PROTRUDE, PROTRUDE], [s * RP, s * RP, 0], **kw)
        ax.plot([XMIN, LBOSS, LBOSS, 0, 0, XMIN], [s * rb, s * rb, s * RBOSS, s * RBOSS, s * RO, s * RO], **kw)
        ax.plot([XMIN, -tpl, -tpl], [s * rki, s * rki, s * rb], **kw)
    if tgt is not None:
        zc_pos, wro, ht = tgt
        ax.add_patch(plt.Rectangle((zc_pos - wro, -ht / 2), 2 * wro, ht, fill=False, ec="c", lw=1.2))
        for s in (-1, 1):
            ax.plot([zc_pos + s * 1.6] * 2, [-ht / 2, ht / 2], color="c", lw=0.8, ls=":")
        ax.text(zc_pos, ht / 2 + 0.6, "washers", color="c", fontsize=7, ha="center", va="bottom")
    ax.text(LBOSS / 2, RBOSS + 0.3, "boss", color="c", fontsize=7, ha="center", va="bottom")
    ax.text(XMIN + 0.3, RO + 0.3, "body", color="c", fontsize=7, ha="left", va="bottom")
    ax.axhline(0, color="grey", lw=0.6, ls=":")
    ax.set_aspect("equal")
    ax.set_xlim(XMIN, XMAX)
    ax.set_ylim(-YMAX, YMAX)
    ax.set_title(("No target, " if tgt is None else "10 washers standing across the axis at {:g} mm, ".format(gap))
                 + current_label(a), fontsize=9)
    ax.set_xlabel("position along the axis (mm)", fontsize=7)
    ax.set_ylabel("height up the washer tower (mm)", fontsize=8)
    return im


def solved(p, xs, ys, a, n, gap=2.0):
    """Field in the cut plane for n washers (0 = no target), cached on disk."""
    path = os.path.join(HERE, "results", "fieldcache3d_{}_{:.3f}A.npz".format(
        "notarget" if not n else "washers%d" % n + ("" if gap == 2.0 else "_gap%gmm" % gap), a))
    if os.path.exists(path):
        d = np.load(path)
        return d["mag"], d["by"], d["bz"], float(d["fz"]), d["tgt"]
    m = fea3d.Model(p, "across", n, gap, a)
    fz = m.solve(verbose=False) if n else 0.0
    if not n:
        m.solve(verbose=False)
    mag, by, bz = sample(m, xs, ys)
    tgt = np.array([-m.tgeo[1], m.tgeo[3], m.tgeo[2] * 2]) if n else np.zeros(3)
    np.savez(path, mag=mag, by=by, bz=bz, fz=fz, tgt=tgt)
    print("solved", n, a, flush=True)
    return mag, by, bz, fz, tgt


def main():
    p = fea3d.fitted()
    xs = np.arange(XMIN, XMAX + 0.01, 0.4)
    ys = np.arange(-YMAX, YMAX + 0.01, 0.4)
    os.makedirs(READ, exist_ok=True)
    amps = [float(v) for v in sys.argv[1:]] or AMPS
    res = {}
    cases = [(0, 2.0)] + [(N, g) for g in GAPS]
    for n, gap in cases:
        for a in amps:
            mag, by, bz, fz, tgt = solved(p, xs, ys, a, n, gap)
            res[(n, gap, a)] = (mag, by, bz, (tuple(tgt) if n else None))
            fig, ax = plt.subplots(figsize=(10, 6))
            im = draw(ax, xs, ys, mag, by, bz, a, res[(n, gap, a)][3], gap)
            style_colorbar(fig.colorbar(im, ax=ax, extend="max", shrink=0.8, pad=0.03))
            fig.text(0.5, 0.0, NOTE if n else NOTE_NT, ha="center", va="top", fontsize=6.5)
            name = "{}_{:.3f}A.png".format("notarget" if not n else "target_gap%gmm" % gap, a)
            fig.savefig(os.path.join(READ, name), dpi=100, bbox_inches="tight")
            plt.close(fig)
            print("done", name, "{:.2f} g".format(fz), flush=True)
    if len(amps) == len(AMPS):
        fig, axs = plt.subplots(4, 5, figsize=(20, 10.5), sharex=True, sharey=True, constrained_layout=True)
        fig.set_constrained_layout_pads(h_pad=0.02, hspace=0.0)
        im = None
        for r, (n, gap) in enumerate(cases):
            for j, a in enumerate(AMPS):
                mag, by, bz, tgt = res[(n, gap, a)]
                im = draw(axs[r, j], xs, ys, mag, by, bz, a, tgt, gap)
                axs[r, j].set_title(axs[r, j].get_title().replace(" standing across the axis", ""), fontsize=9)
                if j:
                    axs[r, j].set_ylabel("")
                if r < 3:
                    axs[r, j].set_xlabel("")
        style_colorbar(fig.colorbar(im, ax=axs, extend="max", shrink=0.5, pad=0.01))
        fig.suptitle("Ledex field around the plunger tip (calibrated 3D model)", fontsize=12)
        fig.text(0.5, -0.005, NOTE, ha="center", va="top", fontsize=8)
        fig.savefig(os.path.join(READ, "overview_readable.png"), dpi=100, bbox_inches="tight")
        plt.close(fig)


if __name__ == "__main__":
    main()
