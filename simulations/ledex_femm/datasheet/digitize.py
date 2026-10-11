"""Digitize the 60-degree plunger force-stroke curves from the Ledex 195224 datasheet (page F19).

    python digitize.py      # reads chart_60deg_force_stroke.png, writes ledex_195224_60deg_force_stroke.csv
                            # and digitize_check.png (traced points over the chart)

The chart crop is page F19 of ledex_195224_sta_pull_20x40.pdf rendered at 4x (288 dpi). The y axis has
1 N grid lines from 0 to 24 N (the label printed "9" sits on the 8 N line), the x axis 0.5 mm grid lines
from 0 to 17.5 mm. The thick blue curves are separated from the thin leader lines by erosion and then
tracked column by column; columns where two curves touch are skipped for those curves.
"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CHART = os.path.join(HERE, "chart_60deg_force_stroke.png")
OUT = os.path.join(HERE, "ledex_195224_60deg_force_stroke.csv")

# frame / grid in chart pixels (detected from the black grid lines)
Y_TOP, Y_BOT, F_TOP = 74.5, 1224.5, 24.0
X_LEFT, X_RIGHT, S_RIGHT = 106.5, 1726.5, 17.5
TURNS = 1491
# top to bottom on the chart: duty cycle (%), watts, ampere-turns at 20 C
CURVES = [(10, 70, 2700), (25, 28, 1700), (50, 14, 1200), (100, 7, 855)]
STROKES = [0.75, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 7, 8, 10, 12.5, 15]
HOLDING_N = 12.8  # published holding force, 60-degree plunger, 20 C (taken at rated 7 W)


def erode(m, k):
    o = m.copy()
    for d in range(1, k + 1):
        o &= np.roll(m, d, 0) & np.roll(m, -d, 0) & np.roll(m, d, 1) & np.roll(m, -d, 1)
    return o


def trace(img):
    r, b = img[..., 0], img[..., 2]
    mask = erode((b - r > 50) & (b > 70) & (r < 120), 2)
    dil = mask.copy()
    for d in range(1, 4):
        dil |= np.roll(mask, d, 0) | np.roll(mask, -d, 0)
    mask = dil
    tracks = [dict() for _ in CURVES]
    prev = None
    for x in range(115, int(X_RIGHT) - 4):
        ys = np.where(mask[:, x])[0]
        if len(ys) == 0:
            continue
        runs = [(g[0], g[-1]) for g in np.split(ys, np.where(np.diff(ys) > 2)[0] + 1) if g[-1] - g[0] >= 4]
        if len(runs) == len(CURVES):
            prev = [(p + q) / 2.0 for p, q in runs]
            for i, c in enumerate(prev):
                tracks[i][x] = c
        elif prev is not None:
            new = list(prev)
            for i in range(len(CURVES)):
                hit = [(p, q) for p, q in runs if p - 12 <= prev[i] <= q + 12]
                if not hit or hit[-1][1] - hit[-1][0] >= 30:
                    continue
                p, q = hit[-1]
                if any(p - 12 <= prev[j] <= q + 12 for j in range(len(CURVES)) if j != i):
                    continue
                tracks[i][x] = new[i] = (p + q) / 2.0
            prev = new
    return tracks


def to_stroke(x):
    return (x - X_LEFT) / (X_RIGHT - X_LEFT) * S_RIGHT


def to_force(y):
    return (Y_BOT - y) / (Y_BOT - Y_TOP) * F_TOP


def main():
    img = np.asarray(Image.open(CHART).convert("RGB")).astype(int)
    tracks = trace(img)
    rows = [(100, 7, 855, 0.0, HOLDING_N, "holding")]
    for (duty, watts, at), tr in zip(CURVES, tracks):
        xs = np.array(sorted(tr))
        s = to_stroke(xs)
        f = to_force(np.array([tr[x] for x in xs]))
        for target in STROKES:
            sel = np.abs(s - target) < 0.08
            if sel.sum() >= 3:
                rows.append((duty, watts, at, target, round(float(np.median(f[sel])), 2), "curve"))
    with open(OUT, "w") as fh:
        fh.write("duty_pct,watts,ampere_turns,current_A,stroke_mm,force_N,source\n")
        for duty, watts, at, s, f, src in sorted(rows, key=lambda r: (-r[0], r[3])):
            fh.write("{},{},{},{:.4f},{:g},{},{}\n".format(duty, watts, at, at / TURNS, s, f, src))
    print("wrote", os.path.relpath(OUT, HERE), len(rows), "rows")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.imshow(img.astype(np.uint8))
    for tr, col in zip(tracks, ["r", "lime", "orange", "magenta"]):
        xs = np.array(sorted(tr))
        ax.plot(xs, [tr[x] for x in xs], ".", ms=1.5, color=col)
    ax.axis("off")
    fig.savefig(os.path.join(HERE, "digitize_check.png"), dpi=90, bbox_inches="tight")


if __name__ == "__main__":
    main()
