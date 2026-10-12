"""Readable field figures with the washer tower in its real orientation (3D model).

The tower of ten washers stands across the solenoid axis (its own axis is vertical in the figure) and
its rim faces the plunger tip. Needs the 3D model, so run with the NGSolve venv:
    /tmp/ngenv/bin/python plot_target_across.py
Optional args: currents in A (default 0.074 0.310 0.580). Overwrites figures/readable/target_gap2mm_{0.074,0.310,0.580}A.png (same style as the no-target figures).
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
N, GAP = 10, 2.0
AMPS = [0.074, 0.310, 0.580]
PROTRUDE, RP, RO, LBOSS, RBOSS, SLOTD = 23.81, 3.91, 9.78, 9.52, 6.6, 9.5
XMIN, XMAX, YMAX = -5, 40, 14

NOTE = ("Side view, cut through the solenoid axis (horizontal, dotted) and the axis of the washer tower (vertical).\n"
        "0 mm = front face of the solenoid body, plunger tip (23.8 mm out) points right. Target = ten M3 washers "
        "(8 mm tall, 9 mm across) standing\non top of each other across the axis, rim 2 mm from the tip.\n"
        "White lines = field direction; cyan = body, boss, plunger, washers (dotted = hole).")


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


def draw(ax, xs, ys, mag, by, bz, a, zc_pos, wro, ht):
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
    ax.set_title("10 washers standing across the axis at 2 mm, " + current_label(a), fontsize=9)
    ax.set_xlabel("position along the axis (mm)", fontsize=7)
    ax.set_ylabel("height up the washer tower (mm)", fontsize=8)
    return im


def main():
    p = fea3d.fitted()
    xs = np.arange(XMIN, XMAX + 0.01, 0.4)
    ys = np.arange(-YMAX, YMAX + 0.01, 0.4)
    os.makedirs(READ, exist_ok=True)
    for a in ([float(v) for v in sys.argv[1:]] or AMPS):
        m = fea3d.Model(p, "across", N, GAP, a)
        fz = m.solve(verbose=False)
        mag, by, bz = sample(m, xs, ys)
        zc, ht, wro = -m.tgeo[1], m.tgeo[2] * 2, m.tgeo[3]
        fig, ax = plt.subplots(figsize=(10, 6))
        im = draw(ax, xs, ys, mag, by, bz, a, zc, wro, ht)
        style_colorbar(fig.colorbar(im, ax=ax, extend="max", shrink=0.8, pad=0.03))
        fig.text(0.5, 0.0, NOTE, ha="center", va="top", fontsize=6.5)
        fig.savefig(os.path.join(READ, "target_gap2mm_{:.3f}A.png".format(a)), dpi=100, bbox_inches="tight")
        plt.close(fig)
        print("done", a, "{:.2f} g".format(fz), flush=True)


if __name__ == "__main__":
    main()
