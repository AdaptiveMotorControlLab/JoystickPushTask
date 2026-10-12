"""3D field figures for the washer column standing across the Ledex axis.

Run with the NGSolve venv: /tmp/ngenv/bin/python plot_fea3d.py
Writes figures/readable/across_*.png (|B| in two cut planes through the tip) and
figures/plots/across_vs_axial.png (force table from results/fea3d.csv).
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
from matplotlib.patches import Rectangle, Circle

import fea3d

HERE = os.path.dirname(os.path.abspath(__file__))
READ = os.path.join(HERE, "figures", "readable")
PLOTS = os.path.join(HERE, "figures", "plots")
N, GAP = 10, 2.0
AMPS = [0.074, 0.31, 0.58]
VMAX = 2.0


def field(m, X, Y, Z):
    """|B| in tesla at mirrored points (the quarter model is symmetric in x and y)."""
    mip = m.mesh(np.abs(X).ravel(), np.abs(Y).ravel(), Z.ravel())
    B = fea3d.curl(m.gfu)
    gf = fea3d.GridFunction(fea3d.L2(m.mesh, order=1))
    return None


def sample(m, X, Y, Z):
    from ngsolve import CoefficientFunction, sqrt
    B = fea3d.curl(m.gfu)
    bm = sqrt(B * B)
    out = np.full(X.size, np.nan)
    for k, (a, b, c) in enumerate(zip(np.abs(X.ravel()), np.abs(Y.ravel()), Z.ravel())):
        try:
            out[k] = bm(m.mesh(a, b, c))
        except Exception:
            pass
    return out.reshape(X.shape)


def main():
    p = fea3d.fitted()
    os.makedirs(READ, exist_ok=True)
    data = {}
    for a in AMPS:
        m = fea3d.Model(p, "across", N, GAP, a)
        fz = m.solve(verbose=False)
        zt = m.zt
        zc = m.tgeo[1]
        wro, ht = m.tgeo[3], m.tgeo[2] * 2
        xs = np.linspace(-13, 13, 130)
        zs = np.linspace(zc - wro - 3, zt + 40, 140)
        Xa, Za = np.meshgrid(xs, zs)
        top = sample(m, Xa, np.zeros_like(Xa), Za)           # plane y = 0: washers seen face-on
        ys = np.linspace(-13, 13, 130)
        Ya, Zb = np.meshgrid(ys, zs)
        side = sample(m, np.zeros_like(Ya), Ya, Zb)          # plane x = 0: column seen edge-on
        data[a] = (fz, xs, ys, zs, top, side, zt, zc, wro, ht)
        print("done", a, fz, flush=True)
    fig, axs = plt.subplots(2, 3, figsize=(16, 8.5), constrained_layout=True)
    im = None
    for j, a in enumerate(AMPS):
        fz, xs, ys, zs, top, side, zt, zc, wro, ht = data[a]
        h = -zs[::-1]                      # horizontal axis = -z: solenoid body on the left, tip pointing right
        for i, (arr, ax_, lab) in enumerate([(side, ys, "side view: tower of washers standing vertically"),
                                              (top, xs, "view from above the tower: washers as rings")]):
            ax = axs[i, j]
            im = ax.pcolormesh(h, ax_, np.clip(arr.T[:, ::-1], 0.005, VMAX), cmap="viridis",
                               norm=LogNorm(0.005, VMAX), shading="auto")
            if i == 0:
                ax.add_patch(Rectangle((-zc - wro, -ht / 2), 2 * wro, ht, fill=False, ec="w", lw=1.2))
                ax.set_ylabel("height up the tower (mm)")
            else:
                ax.add_patch(Circle((-zc, 0), wro, fill=False, ec="w", lw=1.2))
                ax.add_patch(Circle((-zc, 0), 1.6, fill=False, ec="w", lw=1.0, ls=":"))
                ax.set_ylabel("sideways (mm)")
            ax.axvline(-zt, color="w", lw=0.5, ls="--")
            ax.set_aspect("equal")
            ax.set_xlabel("distance along the solenoid axis (mm), tip to the right")
            ax.set_title("{:.3f} A, {} washers, 2 mm: {:.2f} g\n{}".format(a, N, fz, lab), fontsize=9)
    cb = fig.colorbar(im, ax=axs, shrink=0.7, pad=0.02, extend="max")
    cb.set_label("|B| (T), log scale")
    fig.suptitle("Ledex tip and a 10-washer tower standing across the axis (3D model; white outline = washers, "
                 "dashed line = plunger tip)", fontsize=11)
    fig.savefig(os.path.join(READ, "across_field_10washers_gap2mm.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)
    # force vs washers, across vs axial
    rows = list(csv.DictReader(open(os.path.join(HERE, "results", "fea3d.csv"))))
    d = {(r["kind"], int(r["n_washers"]), float(r["gap_mm"]), float(r["current_A"])): float(r["force_g"]) for r in rows}
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2), sharey=True)
    for ax, g in zip(axs, (1.0, 2.0, 3.0)):
        for kind, mk, ls in (("across", "o", "-"), ("axial", "s", "--")):
            for I, c in ((0.31, "tab:blue"), (0.58, "tab:red")):
                ns = [n for n in (1, 5, 10, 20) if (kind, n, g, I) in d]
                ax.plot(ns, [d[(kind, n, g, I)] for n in ns], marker=mk, ls=ls, color=c,
                        label="{} stack, {} A".format("across-axis" if kind == "across" else "coaxial", I))
        ax.set_title("gap {:g} mm".format(g))
        ax.set_xlabel("washers in the stack")
        ax.grid(alpha=0.3)
    axs[0].set_ylabel("pull on the washers (g-force)")
    axs[0].legend(fontsize=8)
    fig.savefig(os.path.join(PLOTS, "across_vs_axial.png"), dpi=140, bbox_inches="tight")
    print("figures written")


if __name__ == "__main__":
    main()
