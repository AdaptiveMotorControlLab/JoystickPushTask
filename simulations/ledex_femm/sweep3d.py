"""Resumable 3D sweeps (washer tower standing across the axis) for the summary figures.

Run with the NGSolve venv:  /tmp/ngenv/bin/python sweep3d.py [group ...] [budget_s] [part=i/n]
Groups: grid (gap and current, 10 washers), far (gaps 6-10 mm), stacks (stack height), stroke (plunger held out),
band (the accepted calibration sets, for the uncertainty band), axial (|B| along the plunger edge),
offset (10 washers, Ledex axis offset vertically from the tower centre; half model, 0.31 A; written to
results/fea3d/force_offset_3d.csv: set,n_washers,gap_mm,yoff_mm,current_A,force_g). part=i/n runs every n-th
offset job starting at i, so several processes can share the sweep.
Results are appended to results/fea3d/force_sweep_3d.csv (set,n_washers,gap_mm,stroke_mm,current_A,force_g);
set 'best' is the fitted model, others are accepted calibration sets (their FEMM eval number).
Jobs already in the file (or in the older results/fea3d/force_first_runs_3d.csv, best set, no stroke) are skipped.
"""
import csv
import os
import sys
import time

import numpy as np

import fea3d

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "fea3d", "force_sweep_3d.csv")
CURRENTS = [0.074, 0.106, 0.180, 0.310, 0.580]
GAPS = [0.5, 1.0, 2.0, 3.0, 5.0]


def key(s, n, g, st, i):
    return (str(s), int(n), round(g, 3), round(st, 3), round(i, 3))


def done_jobs():
    d = {}
    old = os.path.join(HERE, "results", "fea3d", "force_first_runs_3d.csv")
    if os.path.exists(old):
        for r in csv.DictReader(open(old)):
            if r["kind"] == "across":
                d[key("best", r["n_washers"], float(r["gap_mm"]), 0, float(r["current_A"]))] = float(r["force_g"])
    if os.path.exists(OUT):
        for r in csv.DictReader(open(OUT)):
            d[key(r["set"], r["n_washers"], float(r["gap_mm"]), float(r["stroke_mm"]), float(r["current_A"]))] = float(r["force_g"])
    return d


def accepted_sets():
    from calibrate import accepted, spread_subset
    return [r for r in spread_subset(accepted(), 16) if str(r["eval"]) != "212"]


def jobs_for(group):
    J = []
    if group == "grid":
        J += [("best", 10, g, 0, i) for g in GAPS for i in CURRENTS]
    if group == "far":
        J += [("best", 10, g, 0, i) for g in (6.0, 8.0, 10.0) for i in CURRENTS]
    if group == "stacks":
        J += [("best", n, g, 0, i) for n in (1, 5, 10, 20, 40) for g in (1.0, 2.0, 3.0, 5.0) for i in (0.31, 0.58)]
    if group == "stroke":
        J += [("best", 10, 2.0, st, i) for st in (0, 1.5, 3.2, 6.4, 9.5) for i in (0.074, 0.180, 0.310, 0.580)]
    if group == "band":
        J += [(r["eval"], 10, g, 0, i) for r in accepted_sets() for g in (1.0, 2.0, 3.0) for i in (0.074, 0.310, 0.580)]
        J += [("best", 10, g, 0, i) for g in (1.0, 2.0, 3.0) for i in (0.074, 0.310, 0.580)]
    return J


def params_for(s):
    if s == "best":
        return fea3d.fitted()
    from calibrate import accepted
    r = [r for r in accepted() if str(r["eval"]) == str(s)][0]
    p = dict(fea3d.fitted())
    for n in ("SEAT", "CLR", "BSCALE", "TPL", "WALL", "CONEA"):
        p[n] = r[n]
    return p


def solve(p, n, g, st, i):
    """Netgen occasionally fails on some calibration sets; a slightly different plunger mesh size
    meshes them (the force moves by under 1 % with mesh size)."""
    for kw in ({}, {"maxh_pl": 0.6}, {"maxh_pl": 0.8}, {"maxh_pl": 0.5}, {"maxh_pl": 0.9},
               {"maxh_tip": 0.4}, {"maxh_tip": 0.5}, {"maxh_pl": 0.6, "maxh_tip": 0.5}):
        try:
            m = fea3d.Model(p, "across", n, g, i, stroke=st, **kw)
        except Exception:
            continue
        return m.solve(verbose=False)
    return None


def run_group(group, budget_s):
    t0 = time.time()
    d = done_jobs()
    todo = [j for j in jobs_for(group) if key(*j) not in d]
    print(group, len(todo), "jobs to do", flush=True)
    if not os.path.exists(OUT):
        open(OUT, "w").write("set,n_washers,gap_mm,stroke_mm,current_A,force_g\n")
    for s, n, g, st, i in todo:
        if time.time() - t0 > budget_s:
            print("time budget reached; rerun to continue", flush=True)
            return False
        f = solve(params_for(s), n, g, st, i)
        if f is None:
            print("MESHING FAILED, skipped:", s, n, g, st, i, flush=True)
            continue
        open(OUT, "a").write("%s,%d,%g,%g,%g,%.5f\n" % (s, n, g, st, i, f))
        print(s, n, g, st, i, "%.4f g" % f, "(%.0f s)" % (time.time() - t0), flush=True)
    return True


OFFSET_OUT = os.path.join(HERE, "results", "fea3d", "force_offset_3d.csv")
OFFSET_GAPS = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
OFFSETS = [0.0, 2.0, 4.0, 6.0, 8.0, 11.0]


def run_offset(part=(0, 1), budget_s=1e9):
    """Pull on the 10-washer tower with its centre yoff above (or below: symmetric) the solenoid axis."""
    t0 = time.time()
    done = set()
    if os.path.exists(OFFSET_OUT):
        for r in csv.DictReader(open(OFFSET_OUT)):
            done.add((round(float(r["gap_mm"]), 3), round(float(r["yoff_mm"]), 3)))
    else:
        open(OFFSET_OUT, "w").write("set,n_washers,gap_mm,yoff_mm,current_A,force_g\n")
    jobs = [(g, y) for y in OFFSETS for g in OFFSET_GAPS]
    jobs = [j for k, j in enumerate(jobs) if k % part[1] == part[0] and (round(j[0], 3), round(j[1], 3)) not in done]
    print("offset", len(jobs), "jobs to do", flush=True)
    p = fea3d.fitted()
    for g, y in jobs:
        if time.time() - t0 > budget_s:
            return False
        f = None
        for kw in ({}, {"maxh_tip": 0.4}, {"maxh_tip": 0.5}, {"maxh_pl": 0.6}):
            try:
                m = fea3d.Model(p, "across", 10, g, 0.31, yoff=y, half=True, **kw)
            except Exception:
                continue
            f = m.solve(verbose=False)
            break
        if f is None:
            print("MESHING FAILED, skipped:", g, y, flush=True)
            continue
        with open(OFFSET_OUT, "a") as fh:
            fh.write("best,10,%g,%g,0.31,%.5f\n" % (g, y, f))
        print("offset gap", g, "yoff", y, "%.4f g" % f, "(%.0f s)" % (time.time() - t0), flush=True)
    return True


def axial():
    """|B| along the plunger outer edge (r = RP, plane x = 0) in front of the tip, no target."""
    p = fea3d.fitted()
    out = os.path.join(HERE, "results", "fea3d", "field_along_plunger_edge_no_target_3d.csv")
    zs = np.arange(0.0, 40.01, 0.25)
    rows = []
    for i in CURRENTS:
        m = fea3d.Model(p, "across", 0, 2.0, i)
        m.solve(verbose=False)
        B = fea3d.curl(m.gfu)
        for d in zs:
            try:
                v = B(m.mesh(0.0, fea3d.RP, -fea3d.PROTRUDE - d))
                rows.append((i, d, float(np.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2))))
            except Exception:
                pass
        print("axial", i, flush=True)
    with open(out, "w") as f:
        f.write("current_A,dist_mm,B_T\n")
        for r in rows:
            f.write("%g,%g,%.6f\n" % r)


if __name__ == "__main__":
    part = next((a[5:] for a in sys.argv[1:] if a.startswith("part=")), "0/1")
    part = tuple(int(v) for v in part.split("/"))
    args = [a for a in sys.argv[1:] if not a.startswith("part=")]
    groups = [a for a in args if not a.replace(".", "").isdigit()] or ["grid", "stacks", "stroke", "band", "axial"]
    budget = float(next((a for a in args if a.replace(".", "").isdigit()), 1300))
    for g in groups:
        if g == "offset":
            if not run_offset(part, budget):
                break
        elif g == "axial":
            if not os.path.exists(os.path.join(HERE, "results", "fea3d", "field_along_plunger_edge_no_target_3d.csv")):
                axial()
        elif not run_group(g, budget):
            break
