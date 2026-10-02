#!/usr/bin/env python3
"""Build the LABVIEW timing file that the DataJoint pipeline needs for video sync.

The lab pipeline (MMathisLab/DataJoint_mathis, ``traj.SyncCameras`` ->
``schema/utils/align_camera_timings.align_joystick``) loads this file with
``np.load`` and expects a 1-D float64 array of reward times on the camera clock.
It matches the intervals between these times to the intervals between the
REWARD-file samples (assumed 1 kHz) within a 100 ms window. It then anchors each
video frame to its nearest reward.

The push VI's EVENTS file stores the joystick sample index and the PC Unix time
for every event, and the camera software runs on the same PC. A linear fit of
Unix time against sample index therefore turns every REWARD sample into a camera-clock
time. The output has exactly one entry per REWARD row, in REWARD order.

Usage:
    python make_labview_timing.py EVENTS_<name>
    python make_labview_timing.py EVENTS_<name> --camera TIMESTAMPS_VIDEO1_<...>.npy

REWARD_/TRIAL_/joystick_ files are found next to the EVENTS file by name.
The output is TIMESTAMPS_LABVIEW_<name>.npy in the same folder. Attach it with
the transfer GUI's "timing files" button; the GUI needs "LABVIEW" in the name.
Nothing is written if any check fails.
"""

import argparse
import os
import sys

import numpy as np

EVENT_RECORD = 4
CODE_SESSION_START = 1
CODE_TRIAL_START = 3
CODE_SETTLE_END = 14
CODE_WATER_ON = 15
CODE_HEARTBEAT = 90
CODE_SESSION_STOP = 99
# Session start/stop are logged around acquisition start/stop, so their sample
# index is not tied to their timestamp.
CODES_EXCLUDED_FROM_FIT = (CODE_SESSION_START, CODE_SESSION_STOP)

PIPELINE_RATE_HZ = 1000.0
PIPELINE_MATCH_WINDOW_S = 0.10
FIT_OUTLIER_S = 0.005
REWARD_TO_WATER_TOLERANCE_SAMPLES = 10


class CheckFailed(Exception):
    pass


def read_binary(path, dtype, stride, name):
    size = os.path.getsize(path)
    itemsize = np.dtype(dtype).itemsize
    if size % (itemsize * stride):
        raise CheckFailed(f"{name} file size {size} B is not a multiple of "
                          f"{itemsize * stride} B: {path}")
    return np.fromfile(path, dtype=dtype).reshape(-1, stride)


def sibling(events_path, prefix):
    folder, fname = os.path.split(events_path)
    if not fname.startswith("EVENTS_"):
        raise CheckFailed(f"EVENTS file name must start with 'EVENTS_': {fname}")
    return os.path.join(folder, prefix + fname[len("EVENTS_"):])


def fit_sample_clock(events):
    """Return (slope, intercept, max_residual_s, n_used, n_dropped) for unix_time ~ sample."""
    keep = ~np.isin(events[:, 0], CODES_EXCLUDED_FROM_FIT)
    samples, times = events[keep, 1], events[keep, 2]
    if len(samples) < 2:
        raise CheckFailed("EVENTS file has fewer than 2 usable records for the clock fit.")
    slope, intercept = np.polyfit(samples, times, 1)
    inliers = np.abs(times - (slope * samples + intercept)) < FIT_OUTLIER_S
    if inliers.sum() < 2:
        raise CheckFailed("Clock fit failed: almost every event is more than 5 ms off the fit.")
    slope, intercept = np.polyfit(samples[inliers], times[inliers], 1)
    residual = np.abs(times[inliers] - (slope * samples[inliers] + intercept)).max()
    return slope, intercept, residual, int(inliers.sum()), int((~inliers).sum())


def simulate_pipeline_match(reward_samples, labview_ts):
    """Largest mismatch between the pipeline's 1 kHz reward intervals and ours."""
    pipeline_rel = (reward_samples - reward_samples[0]) / PIPELINE_RATE_HZ
    labview_rel = labview_ts - labview_ts[0]
    return np.abs(pipeline_rel - labview_rel).max()


def build(events_path, camera_path=None, out_path=None):
    events = read_binary(events_path, ">f8", EVENT_RECORD, "EVENTS")
    reward_path = sibling(events_path, "REWARD_")
    trial_path = sibling(events_path, "TRIAL_")
    joystick_path = sibling(events_path, "joystick_")
    for path in (reward_path, trial_path, joystick_path):
        if not os.path.exists(path):
            raise CheckFailed(f"Missing session file next to EVENTS: {path}")

    reward_samples = read_binary(reward_path, ">u4", 2, "REWARD")[:, 0].astype(float)
    trial_samples = read_binary(trial_path, ">f4", 4, "TRIAL")[:, 2].astype(float)
    n_joystick = read_binary(joystick_path, ">f8", 5, "joystick").shape[0]
    codes, samples = events[:, 0], events[:, 1]

    print(f"EVENTS   {len(events)} records, {int((codes == CODE_HEARTBEAT).sum())} heartbeats")
    print(f"TRIAL    {len(trial_samples)} rows   REWARD {len(reward_samples)} rows   "
          f"joystick {n_joystick} samples ({n_joystick / PIPELINE_RATE_HZ:.1f} s)")

    if codes[0] != CODE_SESSION_START:
        print("WARNING: EVENTS does not start with session start (code 1).")
    if codes[-1] != CODE_SESSION_STOP:
        print("WARNING: EVENTS does not end with session stop (code 99); the VI may not "
              "have stopped normally.")

    # These checks catch EVENTS/REWARD/TRIAL files from different runs.
    event_trials = samples[codes == CODE_TRIAL_START]
    if len(event_trials) != len(trial_samples) or np.any(event_trials != trial_samples):
        raise CheckFailed(
            f"Trial starts in EVENTS {event_trials.astype(int).tolist()} do not match "
            f"TRIAL {trial_samples.astype(int).tolist()}. Are these files from the same run?")
    if len(reward_samples) == 0:
        raise CheckFailed("REWARD file is empty. The pipeline cannot sync video for a session "
                          "without rewards, so no LABVIEW file is written.")
    if reward_samples.max() >= n_joystick:
        raise CheckFailed("A REWARD sample lies beyond the end of the joystick file.")
    water_samples = samples[np.isin(codes, (CODE_SETTLE_END, CODE_WATER_ON))]
    for r in reward_samples:
        if len(water_samples) == 0 or np.abs(water_samples - r).min() > REWARD_TO_WATER_TOLERANCE_SAMPLES:
            raise CheckFailed(f"REWARD sample {int(r)} has no settle-end/water-on event within "
                              f"{REWARD_TO_WATER_TOLERANCE_SAMPLES} samples.")

    slope, intercept, residual, n_used, n_dropped = fit_sample_clock(events)
    drift_ppm = (slope * PIPELINE_RATE_HZ - 1) * 1e6
    print(f"Clock fit: {slope * 1e3:.6f} ms/sample ({drift_ppm:+.1f} ppm vs 1 kHz), "
          f"max residual {residual * 1e3:.1f} ms over {n_used} events, {n_dropped} outliers dropped")
    if n_dropped > 0.05 * (n_used + n_dropped):
        raise CheckFailed("More than 5% of events are over 5 ms off the clock fit.")

    labview_ts = slope * reward_samples + intercept

    mismatch = simulate_pipeline_match(reward_samples, labview_ts)
    print(f"Pipeline reward matching: worst mismatch {mismatch * 1e3:.1f} ms "
          f"(limit {PIPELINE_MATCH_WINDOW_S * 1e3:.0f} ms)")
    if mismatch >= PIPELINE_MATCH_WINDOW_S:
        raise CheckFailed("Clock drift is too large for the pipeline's 100 ms reward matching; "
                          "SyncCameras would return NaNs for this session.")
    if mismatch >= PIPELINE_MATCH_WINDOW_S / 2:
        print("WARNING: drift uses over half of the pipeline's 100 ms matching window.")

    if camera_path:
        camera_ts = np.load(camera_path)
        print(f"Camera   {camera_ts.size} frames, "
              f"{camera_ts[0] - labview_ts[0]:+.3f} s from first reward to first frame")
        if labview_ts.min() < camera_ts.min() or labview_ts.max() > camera_ts.max():
            raise CheckFailed("Some reward times fall outside the camera recording. Is this the "
                              "camera file for the same session?")

    if out_path is None:
        out_path = sibling(events_path, "TIMESTAMPS_LABVIEW_") + ".npy"
    if "LABVIEW" not in os.path.basename(out_path):
        raise CheckFailed("Output file name must contain 'LABVIEW' for the transfer GUI.")
    np.save(out_path, labview_ts.astype(np.float64))
    print(f"Wrote {out_path} ({len(labview_ts)} reward times)")
    return out_path


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("events", help="EVENTS_<name> file written by the push VI")
    parser.add_argument("--camera", help="camera TIMESTAMPS_*.npy for an optional range check")
    parser.add_argument("-o", "--output", help="output path (default TIMESTAMPS_LABVIEW_<name>.npy)")
    args = parser.parse_args()
    try:
        build(args.events, args.camera, args.output)
    except CheckFailed as err:
        sys.exit(f"ERROR: {err}\nNo LABVIEW file written.")


if __name__ == "__main__":
    main()
