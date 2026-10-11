"""Calibrate the unpublished Ledex model parameters against the datasheet force-stroke curves.

    python calibrate.py screen      # Latin-hypercube screen of the parameter box
    python calibrate.py refine      # Nelder-Mead from the best screened sets
    python calibrate.py explore     # random sets around the optimum (maps the accepted region)
    python calibrate.py band        # target force (washers, 1/2/3 mm) for the accepted sets
    python calibrate.py all         # all four in order (resumes: finished phases are skipped)

Data: datasheet/ledex_195224_60deg_force_stroke.csv (60-degree plunger, 7/14/28/70 W curves plus
the 12.8 N holding force). The 100/25/10 % curves and the holding force are fitted; the 50 % curve
is held out as a check. Error = RMS of ln(model / datasheet), so every point counts equally.

Outputs in results/calibration/: fit_log.csv (one row per evaluated parameter set), fit_points.csv
(model vs datasheet for every point), best_params.json, accepted_sets.csv, target_band.csv.
"""
import csv
import json
import math
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor

import femm_run as fr

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "datasheet", "ledex_195224_60deg_force_stroke.csv")
OUT = os.path.join(HERE, "results", "calibration")
LOG = os.path.join(OUT, "fit_log.csv")
POINTS = os.path.join(OUT, "fit_points.csv")

# free parameters and their physical bounds
PARAMS = [
    ("SEAT", 0.03, 1.0),    # air-gap spacer between cone and stop, mm (STA has a built-in spacer)
    ("CLR", 0.05, 0.8),     # radial non-magnetic gap plunger to front plate/boss (nylon bearing), mm
    ("BSCALE", 0.6, 1.15),  # B multiplier on the 1010 B-H curve (steel grade / saturation)
    ("TPL", 1.5, 3.5),      # end-plate thickness, mm
    ("WALL", 0.8, 2.0),     # case wall thickness, mm
    ("CONEA", 25.0, 65.0),  # cone half-angle from the axis, deg ("60 deg" plunger; 30 = 60 included)
]
NAMES = [p[0] for p in PARAMS]
HOLDOUT_DUTY = 50
ACCEPT = 1.2          # accepted sets: error within this factor of the best
WORKERS = fr.WORKERS


def load_data():
    with open(DATA) as f:
        rows = list(csv.DictReader(f))
    pts = []
    for r in rows:
        pts.append(dict(duty=int(r["duty_pct"]), current=round(float(r["current_A"]), 4),
                        stroke=float(r["stroke_mm"]), force=float(r["force_N"]), source=r["source"]))
    return pts


DATA_PTS = load_data()
STROKES = sorted({p["stroke"] for p in DATA_PTS})
CURRENTS = sorted({p["current"] for p in DATA_PTS})


def to_params(x):
    return {n: lo + min(max(v, 0.0), 1.0) * (hi - lo) for (n, lo, hi), v in zip(PARAMS, x)}


def to_unit(params):
    return [(params[n] - lo) / (hi - lo) for n, lo, hi in PARAMS]


def errors(forces):
    fit, hold = [], []
    for p in DATA_PTS:
        m = forces.get((p["stroke"], p["current"]))
        if m is None or m <= 0:
            return float("inf"), float("inf"), float("inf")
        e = math.log(m / p["force"])
        (hold if p["duty"] == HOLDOUT_DUTY else fit).append(e)
    rms = lambda v: math.sqrt(sum(x * x for x in v) / len(v))
    return rms(fit), rms(hold), rms(fit + hold)


def read_log():
    if not os.path.exists(LOG):
        return []
    with open(LOG) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in NAMES + ["err_fit", "err_holdout", "err_all"]:
            r[k] = float(r[k])
        r["eval"] = int(r["eval"])
    return rows


def append_log(phase, params, forces):
    os.makedirs(OUT, exist_ok=True)
    log = read_log()
    eid = len(log)
    ef, eh, ea = errors(forces)
    new = not os.path.exists(LOG)
    with open(LOG, "a") as f:
        if new:
            f.write("eval,phase," + ",".join(NAMES) + ",err_fit,err_holdout,err_all\n")
        f.write("{},{},{},{:.5f},{:.5f},{:.5f}\n".format(
            eid, phase, ",".join("{:.5f}".format(params[n]) for n in NAMES), ef, eh, ea))
    new = not os.path.exists(POINTS)
    with open(POINTS, "a") as f:
        if new:
            f.write("eval,duty_pct,current_A,stroke_mm,datasheet_N,model_N\n")
        for p in DATA_PTS:
            m = forces.get((p["stroke"], p["current"]), float("nan"))
            f.write("{},{},{},{:g},{},{:.4f}\n".format(eid, p["duty"], p["current"], p["stroke"], p["force"], m))
    print("eval {:3d} {:8s} ".format(eid, phase) + " ".join("{}={:.3f}".format(n, params[n]) for n in NAMES)
          + "  err_fit={:.3f} holdout={:.3f}".format(ef, eh), flush=True)
    return ef


def evaluate_many(param_sets, phase):
    """Evaluate several parameter sets; all (set, stroke) jobs share one worker pool."""
    jobs = [(i, s) for i in range(len(param_sets)) for s in STROKES]
    with ThreadPoolExecutor(WORKERS) as ex:
        parts = list(ex.map(lambda j: (j[0], fr.plunger_job(param_sets[j[0]], [j[1]], CURRENTS, phase)), jobs))
    forces = [dict() for _ in param_sets]
    for i, rows in parts:
        for line in rows:
            p = line.split(",")
            forces[i][(float(p[9]), round(float(p[10]), 4))] = float(p[11])
    return [append_log(phase, ps, fc) for ps, fc in zip(param_sets, forces)]


def lhs(n, seed=1):
    rnd = random.Random(seed)
    cols = []
    for _ in PARAMS:
        c = [(k + rnd.random()) / n for k in range(n)]
        rnd.shuffle(c)
        cols.append(c)
    return [[cols[d][k] for d in range(len(PARAMS))] for k in range(n)]


def phase_done(phase):
    return any(r["phase"] == phase for r in read_log())


def screen(n=60):
    if phase_done("screen"):
        print("screen: done")
        return
    base = {"SEAT": 0.1, "CLR": 0.15, "BSCALE": 1.0, "TPL": 2.5, "WALL": 1.5, "CONEA": 30.0}
    evaluate_many([base], "initial")
    evaluate_many([to_params(x) for x in lhs(n)], "screen")


def nelder_mead(f, x0, step=0.15, max_eval=70, tol=0.002):
    d = len(x0)
    simplex = [list(x0)]
    for i in range(d):
        x = list(x0)
        x[i] = x[i] + step if x[i] + step <= 1 else x[i] - step
        simplex.append(x)
    vals = f(simplex)
    n_eval = len(simplex)
    while n_eval < max_eval:
        order = sorted(range(d + 1), key=lambda i: vals[i])
        simplex = [simplex[i] for i in order]
        vals = [vals[i] for i in order]
        if vals[-1] - vals[0] < tol:
            break
        c = [sum(x[k] for x in simplex[:-1]) / d for k in range(d)]
        clip = lambda x: [min(max(v, 0.0), 1.0) for v in x]
        xr = clip([c[k] + (c[k] - simplex[-1][k]) for k in range(d)])
        xe = clip([c[k] + 2 * (c[k] - simplex[-1][k]) for k in range(d)])
        xc = clip([c[k] + 0.5 * (simplex[-1][k] - c[k]) for k in range(d)])
        fr_, fe, fc = f([xr, xe, xc])   # evaluated together to use the worker pool
        n_eval += 3
        if fr_ < vals[0] and fe < fr_:
            simplex[-1], vals[-1] = xe, fe
        elif fr_ < vals[-2]:
            simplex[-1], vals[-1] = xr, fr_
        elif fc < vals[-1]:
            simplex[-1], vals[-1] = xc, fc
        else:
            shrunk = [[simplex[0][k] + 0.5 * (x[k] - simplex[0][k]) for k in range(d)] for x in simplex[1:]]
            sv = f(shrunk)
            n_eval += d
            simplex = [simplex[0]] + shrunk
            vals = [vals[0]] + sv
    i = min(range(d + 1), key=lambda i: vals[i])
    return simplex[i], vals[i]


def refine(starts=2):
    if phase_done("refine"):
        print("refine: done")
        return
    log = sorted(read_log(), key=lambda r: r["err_fit"])
    picked = []
    for r in log:   # best sets that are not near-duplicates
        x = to_unit(r)
        if all(sum((a - b) ** 2 for a, b in zip(x, y)) > 0.05 for y in picked):
            picked.append(x)
        if len(picked) == starts:
            break
    for x0 in picked:
        nelder_mead(lambda xs: evaluate_many([to_params(x) for x in xs], "refine"), x0)


def best():
    return min(read_log(), key=lambda r: r["err_fit"])


def explore(n=48, width=0.12, seed=7):
    if phase_done("explore"):
        print("explore: done")
        return
    b = to_unit(best())
    rnd = random.Random(seed)
    sets = [[min(max(v + rnd.uniform(-width, width), 0.0), 1.0) for v in b] for _ in range(n)]
    evaluate_many([to_params(x) for x in sets], "explore")


def accepted():
    log = read_log()
    e0 = best()["err_fit"]
    return [r for r in log if r["err_fit"] <= ACCEPT * e0]


def write_best():
    b = best()
    acc = accepted()
    info = dict(params={n: round(b[n], 4) for n in NAMES}, err_fit=b["err_fit"], err_holdout=b["err_holdout"],
                err_all=b["err_all"], eval=b["eval"], n_evaluated=len(read_log()), n_accepted=len(acc),
                accept_rule="err_fit <= {} x best".format(ACCEPT),
                ranges_accepted={n: [round(min(r[n] for r in acc), 4), round(max(r[n] for r in acc), 4)] for n in NAMES},
                note="err = RMS of ln(model/datasheet); fitted: 100/25/10 % curves + holding force; held out: 50 % curve")
    with open(os.path.join(OUT, "best_params.json"), "w") as f:
        json.dump(info, f, indent=2)
    with open(os.path.join(OUT, "accepted_sets.csv"), "w") as f:
        f.write("eval,phase," + ",".join(NAMES) + ",err_fit,err_holdout\n")
        for r in sorted(acc, key=lambda r: r["err_fit"]):
            f.write("{},{},{},{:.5f},{:.5f}\n".format(r["eval"], r["phase"], ",".join("{:.5f}".format(r[n]) for n in NAMES),
                                                    r["err_fit"], r["err_holdout"]))
    print(json.dumps(info, indent=2))


def spread_subset(rows, k):
    """Up to k rows: the best plus farthest-point picks in the unit parameter cube."""
    rows = sorted(rows, key=lambda r: r["err_fit"])
    pick = [rows[0]]
    while len(pick) < min(k, len(rows)):
        cand = max((r for r in rows if r not in pick),
                   key=lambda r: min(sum((a - b) ** 2 for a, b in zip(to_unit(r), to_unit(p))) for p in pick))
        pick.append(cand)
    return pick


def band(k=16):
    path = os.path.join(OUT, "target_band.csv")
    if os.path.exists(path):
        print("band: done")
        return
    sets = spread_subset(accepted(), k)
    amps = fr.AMPS_KEY
    jobs = [(r, g) for r in sets for g in [1, 2, 3]]

    def run(job):
        r, g = job
        over = {n: r[n] for n in NAMES}
        return r["eval"], fr.sweep_job("band_eval{}_gap{}".format(r["eval"], g), "washers5_M3", over, [g], amps)

    with ThreadPoolExecutor(WORKERS) as ex:
        parts = list(ex.map(run, jobs))
    with open(path, "w") as f:
        f.write("eval,gap_mm,current_A,target_force_N,target_force_g,plunger_force_N\n")
        for eid, rows in parts:
            for line in rows:
                p = line.split(",")
                f.write("{},{},{},{},{},{}\n".format(eid, p[13], p[14], p[15], p[16], p[17]))
    print("wrote", os.path.relpath(path, HERE))


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("screen", "all"):
        screen()
    if what in ("refine", "all"):
        refine()
    if what in ("explore", "all"):
        explore()
    if what in ("band", "all"):
        write_best()
        band()
    if what == "best":
        write_best()


if __name__ == "__main__":
    main()
