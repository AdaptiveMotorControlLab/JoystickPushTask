#!/usr/bin/env python3
"""Check from EVENTS that every trial used the parameter row it should have.

Trial n is the n-th arming (EVENTS code 6, 8 or 9; 1-based). Trial 1 uses row 1;
each later trial uses the next row, except after a timeout on a row whose
column 30 `repeat trials` is nonzero (31-column files), which repeats that row.
Without repeats, trial n uses row n. For every trial the script compares what
the VI did with its expected row r:

- code 3 value: the row number r (only once the VI logs it; all-zero values
  are reported as "not logged").
- code 15 value (water pulse, ms): column 17 `watertime`.
- timeout length (arming to code 5): column 19 `move time`, within --tol ms.
- trials armed beyond the last row of the file.

On a mismatch it lists which nearby rows (r-3 .. r+3) the value matches, so an
offset such as "row n+1" (one after the expected row) is visible. Rows that repeat (e.g. alternating files)
match several offsets; use a file with distinct per-row values to pin them down.

Usage:
    python check_row_mapping.py EVENTS_<name> <parameter file> [--tol 25] [--quiet]

Numpy only (runs on the rig PC's Python 3.6). Exit code 1 if any check fails.
"""

import argparse
import sys

import numpy as np

ARM_CODES = (6, 8, 9)
CODE_TRIAL_START, CODE_SUCCESS, CODE_TIMEOUT, CODE_WATER_ON, CODE_MAGNET_ON = 3, 4, 5, 15, 20
COL_WATERTIME, COL_MOVE_TIME, COL_REPEAT = 17, 19, 30
OFFSETS = (-3, -2, -1, 1, 2, 3)


def read_parameters(path):
    rows = []
    with open(path) as f:
        for line in f:
            if line.strip():
                rows.append([float(v) for v in line.rstrip("\r\n").split("\t")])
    widths = sorted(set(len(r) for r in rows))
    if len(widths) != 1 or widths[0] < 27:
        sys.exit(f"Parameter file has inconsistent or short rows (widths {widths}): {path}")
    return np.array(rows)


def offsets_matching(values, r, target, tol):
    hits = []
    for d in OFFSETS:
        if 0 <= r + d < len(values) and abs(values[r + d] - target) <= tol:
            hits.append(f"n{d:+d}")
    return ",".join(hits) if hits else "none nearby"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("events")
    ap.add_argument("parameters")
    ap.add_argument("--tol", type=float, default=25.0, help="timeout tolerance in ms (default 25)")
    ap.add_argument("--quiet", action="store_true", help="print only failing trials and the summary")
    args = ap.parse_args()

    params = read_parameters(args.parameters)
    water, move = params[:, COL_WATERTIME], params[:, COL_MOVE_TIME]
    repeat = params[:, COL_REPEAT] if params.shape[1] > COL_REPEAT else np.zeros(len(params))
    ev = np.fromfile(args.events, ">f8").reshape(-1, 4)
    ev = ev[np.argsort(ev[:, 2], kind="mergesort")]
    codes = ev[:, 0]
    arms = np.flatnonzero(np.isin(codes, ARM_CODES))
    code3_logged = bool(np.any(ev[codes == CODE_TRIAL_START, 3] != 0))

    print(f"{len(arms)} armed trials, {len(params)} parameter rows, "
          f"{int(np.count_nonzero(repeat))} with repeat trials on; code 3 row number "
          f"{'logged' if code3_logged else 'not logged (all 0)'}")
    print("   n  row  outcome  code3  water(ms) exp   timeout(ms) exp    magnet  problems")
    n_fail = 0
    tally = {"code3": 0, "water": 0, "timeout": 0, "beyond": 0, "unpaid": 0, "magnet": 0}
    r = 0
    for n, i in enumerate(arms, 1):
        j = arms[n] if n < len(arms) else len(ev)
        seg = ev[i:j]
        problems = []

        def first(code):
            hit = seg[seg[:, 0] == code]
            return hit[0] if len(hit) else None

        e3, e4, e5, e15, e20 = (first(c) for c in
                                (CODE_TRIAL_START, CODE_SUCCESS, CODE_TIMEOUT, CODE_WATER_ON, CODE_MAGNET_ON))
        outcome = "success" if e4 is not None else ("timeout" if e5 is not None else "none")
        if r >= len(params):
            problems.append("armed beyond the last row")
            tally["beyond"] += 1
        if e20 is None:
            problems.append("no code 20 (magnet loop missed)")
            tally["magnet"] += 1

        c3 = "-" if e3 is None else f"{e3[3]:.0f}"
        if code3_logged and (e3 is None or e3[3] != r + 1):
            problems.append(f"code 3 value {c3} != {r + 1}")
            tally["code3"] += 1

        w_txt, wexp_txt = "-", "-"
        if r < len(params):
            wexp_txt = f"{water[r]:.0f}"
        if e4 is not None and e15 is None:
            problems.append("success without code 15 (unpaid)")
            tally["unpaid"] += 1
        if e15 is not None:
            w_txt = f"{e15[3]:.0f}"
            if r < len(params) and abs(e15[3] - water[r]) > 0.5:
                problems.append(f"water from row {offsets_matching(water, r, e15[3], 0.5)}")
                tally["water"] += 1

        t_txt, texp_txt = "-", "-"
        if r < len(params):
            texp_txt = f"{move[r]:.0f}"
        if e5 is not None:
            dt = (e5[2] - ev[i, 2]) * 1000.0
            t_txt = f"{dt:.0f}"
            if r < len(params) and abs(dt - move[r]) > args.tol:
                problems.append(f"timeout from row {offsets_matching(move, r, dt, args.tol)}")
                tally["timeout"] += 1

        n_fail += bool(problems)
        if problems or not args.quiet:
            print(f"{n:4d} {r + 1:4d}  {outcome:7s}  {c3:>5s}  {w_txt:>5s} {wexp_txt:>5s}   {t_txt:>6s} {texp_txt:>6s}"
                  f"    {'ok' if e20 is not None else 'MISS':>4s}    {'; '.join(problems)}")
        if not (outcome == "timeout" and r < len(params) and repeat[r] != 0):
            r += 1

    print(f"\n{n_fail} of {len(arms)} trials with problems: " +
          ", ".join(f"{k} {v}" for k, v in tally.items()))
    print("Note: a success can only be checked through its water value; criteria offsets show up as "
          "timeouts with the wrong length or as successes that the row should not allow.")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
