# Parameter files

Tab-separated doubles, **27 columns**, one line = one trial. Columns 1–21 were
mapped on the live VI on 8 September 2026. Columns 22–27 (reward delay, cue,
spout) are in the files as of 9 September 2026; the loader still has to grow
from 21 to 27 cases or those values are ignored.

## Column map (confirmed)

| Index | File column | Field | Notes |
| ---: | ---: | --- | --- |
| 0 | 1 | `home X1` | **ROI slot X — follows the white / push line** (09/09/26 hand test). Pair with col 3. Loader name “X” is not NI-MAX `ai0`. |
| 1 | 2 | `home Y1` | **ROI slot Y — follows the red / lateral line.** Pair with col 4. |
| 2 | 3 | `home X2` | No ×2 on the live loader (checked 09/09/26). |
| 3 | 4 | `home Y2` | |
| 4 | 5 | `home TO` | ms. Object-in-home **and** FSR paw. |
| 5 | 6 | `start X1` | Unused while `start TO` = 0. |
| 6 | 7 | `start Y1` | |
| 7 | 8 | `start X2` | |
| 8 | 9 | `start Y2` | |
| 9 | 10 | `start TO` | Keep **0**. |
| 10 | 11 | `end X1` | **Push target** (white / `ai1`). Lower V = farther forward. |
| 11 | 12 | `end Y1` | **Lateral** (red / `ai0`). Keep wide around 2.525 V. |
| 12 | 13 | `end X2` | |
| 13 | 14 | `end Y2` | |
| 14 | 15 | `end TO` | ms dwell inside the end box. |
| 15 | 16 | `mag` | Keep **0** until resistance. |
| 16 | 17 | `magtime` | Dummy 25 on zero-force rows. |
| 17 | 18 | `watertime` | ms. 130 / 185 / 240 → 4 / 6 / 8 µl. |
| 18 | 19 | `timeout` | Case 0 inter-trial wait (ms). |
| 19 | 20 | `move time` | Case 3 movement window (ms). **400 is short.** |
| 20 | 21 | `light` | Keep **0**. |
| 21 | 22 | `reward delay` | ms after cue, before spout extend. Stage 6. |
| 22 | 23 | `cue duration` | ms. Bench 50. |
| 23 | 24 | `spout extend` | V. Bench **3.0**. |
| 24 | 25 | `spout settle` | ms. Bench **2000**. |
| 25 | 26 | `consumption` | ms. Bench **2000**. |
| 26 | 27 | `spout retract` | V. Bench **0**. |

Boxes are two corners `(X1, Y1, X2, Y2)`. Write the smaller voltage first in
each pair. **Do not trust the words X and Y.** 09/09/26: a file with the
forward band in the Y slots paid out only when **red** moved. The forward
band now goes in the **X** slots so a white-line push is the target. Likely
cause: after `joysticklickframe_push` was reordered to `[Y, X, FSR]`, Case 3
still compares index 0 to the X box and index 1 to the Y box.

## Shared settings (all written files)

Scale is the 08/09/26 eyeball **0.030 V/mm**, push rest **2.50 V** (lower V =
forward). Remeasure with a ruler before treating millimetres as final.

| Field | Value | Why |
| --- | --- | --- |
| Home X (push) | 2.46–2.54 | Rest 2.50 ± 0.035 |
| Home / end Y (lateral) | 2.40–2.65 | Wide so red noise does not fail the trial |
| `home TO` | 250 ms | User 09/09/26 |
| `start TO` | 0 | Rest pad + home replace the start-box wait |
| `watertime` | 185 ms | ~6 µl |
| `timeout` (ITI) | 1000 ms | |
| `move time` | 30000 ms | Clock still starts at Case 2, not paw lift |
| `mag` / `magtime` / `light` | 0 / 25 / 0 | No resistance yet |
| `reward delay` | 0 ms stages 2–5; stage 6 ramps 0/250/500/1000; 500 ms expert/shadow | Final default can move to 1000 ms after validation |
| `cue duration` | 50 ms | |
| `spout extend` / `retract` | 3.0 V / 0 V | |
| `spout settle` / `consumption` | 2000 / 2000 ms | |

Advance a stage after the criterion on **two consecutive days**. Change only
one important thing at a time.

## Files that exist

| File | Stage | Push end box (X) | ~mm from rest | `end TO` | Rows | Extra |
| --- | --- | --- | --- | --- | --- | --- |
| [push_bench_wide-zone.txt](push_bench_wide-zone.txt) | Hand test | 2.20–2.35 | 5–10 mm, wide | 50 | 80 | delay 0 |
| [training/02_micro_push.txt](training/02_micro_push.txt) | 2 Discovery | 2.15–2.45 | past ~1.7 mm, no far wall | **0** | 200 | delay 0 |
| [training/03_proximal_zone.txt](training/03_proximal_zone.txt) | 3 Proximal | 2.35–2.45 | 1.7–5.0 mm | 50 | 400 | delay 0 |
| [training/04_zone_translate_1.txt](training/04_zone_translate_1.txt) | 4 Shift 1 | 2.31–2.41 | 3.0–6.3 mm | 50 | 400 | delay 0 |
| [training/04_zone_translate_2.txt](training/04_zone_translate_2.txt) | 4 Shift 2 | 2.26–2.36 | 4.7–8.0 mm | 50 | 400 | delay 0 |
| [training/04_zone_translate_3.txt](training/04_zone_translate_3.txt) | 4 Final broad | 2.24–2.35 | 5.0–8.7 mm | 50 | 400 | delay 0 |
| [training/05_zone_refine.txt](training/05_zone_refine.txt) | 5 Refine | 2.27–2.34 | 5.3–7.7 mm, ~2.3 mm wide | 50 | 400 | delay 0 |
| [training/06_delay_0.txt](training/06_delay_0.txt) | 6 Delay 0 | same as expert | same | 50 | 400 | reward delay **0** |
| [training/06_delay_250.txt](training/06_delay_250.txt) | 6 Delay 250 | same | same | 50 | 400 | delay **250** |
| [training/06_delay_500.txt](training/06_delay_500.txt) | 6 Delay 500 | same | same | 50 | 400 | delay **500** |
| [training/06_delay_1000.txt](training/06_delay_1000.txt) | 6 Delay 1000 | same | same | 50 | 400 | delay **1000** |
| [training/07_expert.txt](training/07_expert.txt) | 7 Expert | same as refine | same | 50 | 500 | delay **500** |
| [training/08_shadow.txt](training/08_shadow.txt) | 8 Shadow | same as expert | same | 50 | 300 | delay **500** |

`08_shadow` is geometrically identical to expert (`mag = 0`). The 50 / 75 / 100 / 75
block labels are not in the file; they are session notes until the magnet exists.

Do not load `Full_shoterPull_Training_Task_RIG1` for the push task.

## Stages that are **not** a parameter file

| Stage | Why | What to do instead |
| --- | --- | --- |
| 1 Habituation (cue → water, no push) | Water loop only wakes on Case 4 | Run `deliverWater_RIG1_cue.vi` once per manual reward. It gives a fixed 50 ms cue, then water for the front-panel `Water on time (ms)` value. |
| Rest only (fallback) | Would reward pad contact without a push | LabVIEW if a mouse never touches the pad. Not a default. |
| 6 Delay / retractable spout | Files exist (`06_delay_*`) | Load 0 → 250 → 500; use 1000 only if desired and tolerated. Do not change the zone in those sessions. |
| 8 Shadow block labels | No column for block ID; magnet still absent | Run `08_shadow` as one 300-trial zero-force session. Split 50/75/100/75 later if needed. |
| 9 Experiment (Baseline / Random / Fixed / Washout) | Random/Fixed need a force-calibrated magnet | Baseline ≈ `07_expert`. Do not write `mag ≠ 0` files yet. |

## Front panel during these files

The live rig loader and water loop were extended and runtime-tested on
09/09/26. The six values now come from the file. Keep the old FP controls
temporarily as visible references/fallbacks until the edited VI is transferred
back to this repository and re-tested from a clean copy. Log the selected
filename with the session.

## LabVIEW: loader extension completed on rig 09/09/26

The following implementation was completed and reported working on the rig PC.
The repository `.vi` binary still needs to be replaced with that tested copy.

1. Stop the VI. Save a backup.
2. On the front panel, expand the cluster inside **`exp para array`** from
   21 to 27 numeric fields. Copy six existing DBL fields inside the cluster
   and rename their labels exactly: `reward delay`, `cue duration`,
   `spout extend`, `spout settle`, `consumption`, `spout retract`. If the
   cluster is a typedef, open and edit the typedef instead. The loader cases
   cannot Bundle By Name into fields that do not exist in this cluster.
3. Parameter-loader For Loop: change the **21** to **27** (loop count and any
   “init array of 21 zeros”).
4. Add cases **21–26** on that Case Structure (`i`), same pattern as `home X1`:
   Scan From String `%f` → bundle into a new named field.
   - 21 `reward delay`
   - 22 `cue duration`
   - 23 `spout extend`
   - 24 `spout settle`
   - 25 `consumption`
   - 26 `spout retract`
5. Water loop (the Flat Sequence that already uses `watertime`):
   - Wait after cue LOW → **`reward delay`** from this trial (not the FP)
   - Cue wait → **`cue duration`**
   - Extend write → **`spout extend`**
   - Settle wait → **`spout settle`**
   - After water LOW → **`consumption`**
   - Retract write → **`spout retract`**
   Copy how `watertime` is already unbundled for the current trial.
6. Save. Load `06_delay_250.txt`. Success should wait **250 ms** after the cue
   before the spout moves. Then try `06_delay_0.txt` — spout should move
   immediately after the cue.

Habituation (cue→water with no push) is still a separate LabVIEW mode. These
columns do not create that.
