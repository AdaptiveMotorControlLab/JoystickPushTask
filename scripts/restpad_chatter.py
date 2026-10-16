#!/usr/bin/env python3
"""Summarise rest-pad (ai2) contact quality in a joystick file.

The capacitive rest pad drives ai2 (joystick-file column 4) to ~0 V / ~5 V. Mains hum picked
up through the mouse can make it toggle every ~20 ms while the paw rests on the pad, which
blocks the Case 0 `home TO` hold. This prints how often that happens.

Usage:
    python restpad_chatter.py joystick_<name> [--hold-ms 100] [--threshold 2.5]

Numpy only (runs on the rig-PC Python 3.6).
"""

import argparse

import numpy as np

RATE_HZ = 1000
STRIDE = 5
COL_REST_PAD = 3
CHATTER_TRANSITIONS_PER_S = 40


def runs(state):
    edges = np.flatnonzero(np.diff(state.astype(np.int8))) + 1
    starts = np.r_[0, edges]
    lengths = np.diff(np.r_[starts, len(state)])
    return starts, lengths, state[starts]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("joystick_file")
    ap.add_argument("--hold-ms", type=int, default=100, help="Case 0 home TO (ms)")
    ap.add_argument("--threshold", type=float, default=2.5, help="rest pad threshold (V)")
    args = ap.parse_args()

    data = np.fromfile(args.joystick_file, dtype=">f8").reshape(-1, STRIDE)
    touched = data[:, COL_REST_PAD] > args.threshold
    n = len(touched)
    _, lengths, state = runs(touched)
    high = lengths[state]
    low = lengths[~state]

    print("%s: %.1f min, touched %.1f%% of the time"
          % (args.joystick_file, n / RATE_HZ / 60, 100 * touched.mean()))
    print("touch episodes: %d, of which >= %d ms: %d (%.1f%%)"
          % (len(high), args.hold_ms, (high >= args.hold_ms).sum(),
             100 * (high >= args.hold_ms).mean() if len(high) else 0))
    if len(high):
        print("touch episode length (ms) median %.0f, 90th pct %.0f"
              % tuple(np.percentile(high, [50, 90])))
    if len(low):
        print("release gaps <= 30 ms: %d (%.1f%% of releases)"
              % ((low <= 30).sum(), 100 * (low <= 30).mean()))

    seconds = n // RATE_HZ
    transitions = np.flatnonzero(np.diff(touched.astype(np.int8)))
    per_s = np.bincount(transitions // RATE_HZ, minlength=seconds)[:seconds]
    chatter = per_s > CHATTER_TRANSITIONS_PER_S
    print("seconds with chatter (> %d transitions/s): %d" % (CHATTER_TRANSITIONS_PER_S, chatter.sum()))
    print("chatter seconds per minute:",
          np.bincount(np.flatnonzero(chatter) // 60, minlength=seconds // 60 + 1).tolist())


if __name__ == "__main__":
    main()
