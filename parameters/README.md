# Parameter files

Tab-separated doubles, **27 columns**, one line = one trial. The loader in
`Push Behaviour_MCHALABI.vi` reads all 27. Columns 22–27 are reward delay, cue
duration, spout extend, spout settle, consumption, and spout retract. User
confirmed on 29 Sep 2026 that this 27-column order is the correct one.

## Column map (confirmed)

| Index | File column | Field | Notes |
| ---: | ---: | --- | --- |
| 0 | 1 | `home X1` | **ROI slot X — follows the white / push line** (09/09/26 hand test). Pair with col 3. Loader name “X” is not NI-MAX `ai0`. |
| 1 | 2 | `home Y1` | **ROI slot Y — follows the red / lateral line.** Pair with col 4. |
| 2 | 3 | `home X2` | No ×2 on the live loader (checked 09/09/26). |
| 3 | 4 | `home Y2` | |
| 4 | 5 | `home TO` | ms. Object-in-home **and** rest pad touched. |
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
| 27 | 28 | `vel threshold` | **Optional, velocity mode (VI built 22 Oct, bench-tested by hand; mouse test pending).** V per 50 ms of `abs(d push) + abs(d lateral)` (50-sample lag); Case 3 pays when above it. 0 = off. 27-column files load it as 0. |

Velocity-mode files (28 columns): `training/02_micro_touch_velocity_200ms_thr0p012.txt` and `_thr0p015.txt`
(500 rows; home push 2.43-2.53, `home TO` 200, end box 0-1 V so only velocity pays, `move time` 5000).
Noise on 20-21 Oct (paw on pad, cube untouched): 99.99th percentile 7.8-8.0 mV, max 9-11.6 mV (same at lag 10-50 ms). VI uses a 50 ms lag; 0.012 gave 0 noise onsets in 224 min.
Bench-tested without a mouse on 22 Oct (touch pays, slow micro-push pays at lag 50); not yet run with a mouse.

Restored historical day-one files (exact copies from git, kept so every recorded session has its file;
session map in `docs/PROJECT_PLAN.md`): `training/02_micro_push_day1_restpad_home2p475.txt` (16 Oct: home 2.475-2.51,
success < 2.47, `home TO` 50, ITI 1500), `training/02_micro_push_day1_restpad_home2p44-2p49_hold100_end2p35.txt` and
`_hold100_end2p40.txt` (19 Oct: home 2.44-2.49, `home TO` 100, success < 2.35 / < 2.40, ITI 1500). The current
`_home2p44-2p49.txt` (from 20 Oct) has `home TO` 50 and success < 2.40.

Boxes are two corners `(X1, Y1, X2, Y2)`. Write the smaller voltage first in
each pair. **Do not trust the words X and Y.** The names in the loader are not
the NI-MAX channel names. White / push goes in the **X** columns (1, 3, 11, 13).
Red / lateral goes in the **Y** columns (2, 4, 12, 14). A 09/09/26 file with
the forward band in the Y slots paid out only when red moved. The 27-column
files already use this order; user confirmed that on 29 Sep 2026. Likely
cause: after `joysticklickframe_push` was reordered to `[Y, X, rest pad]`, Case 3
still compares index 0 to the X box and index 1 to the Y box.

## Shared settings

Scale is the 08/09/26 eyeball **0.030 V/mm** (lower V = forward). Remeasure
with a ruler before treating millimetres as final.

Home voltage is not a fixed rig constant. It changes when the joystick shaft
or the object is fitted or removed. Remeasure before loading a file from
another mechanical setup.

The table below is the **08–09 Sep** calibration (rest **2.50 V**). It still
describes `02_micro_push.txt` and stages 03–08. It is not the current
object-on setup. For that setup use
`training/02_micro_push_day1_5s_8ul.txt` (rest about **2.25 V**, home
2.225–2.350, `home TO` 1 ms, reward 0.00–2.22) or the two pad-contact shaping files.
User confirmed those later files on 29 Sep 2026.

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
| [push_bench_full-system.txt](push_bench_full-system.txt) | No-joystick/base-movement full-system hand test | 0.00–2.22 | manually move base from expert-file home | 0 | 20 | expert home/start and 250 ms rest-pad gate; 500 ms reward delay; cue, spout 0→3→0 V, 6 µl water; `mag=0` |
| [push_bench_full-system_nocue.txt](push_bench_full-system_nocue.txt) | Same as full-system bench test, silent | 0.00–2.22 | same as above | 0 | 20 | identical except `cue duration` = 0 ms (column 23), so the buzzer is not held HIGH |
| [training/01_pad_contact_shaping_50ms.txt](training/01_pad_contact_shaping_50ms.txt) | 1b supervised pad-contact shaping | 0.00–5.00 | Joystick ignored within 0–5 V | **0** | 125 | 50 ms pad gate (`home TO`); 2 s ITI; 8 µl; fixed 3 V spout |
| [training/01_pad_contact_shaping_250ms.txt](training/01_pad_contact_shaping_250ms.txt) | 1b supervised pad-contact shaping, longer hold | 0.00–5.00 | Joystick ignored within 0–5 V | **0** | 125 | 250 ms pad gate (`home TO`); otherwise identical to the 50 ms file |
| [training/02_micro_push.txt](training/02_micro_push.txt) | 2 Discovery | 2.15–2.45 | past ~1.7 mm, no far wall | **0** | 200 | delay 0 |
| [training/02_micro_push_day1_5s_8ul.txt](training/02_micro_push_day1_5s_8ul.txt) | 2 Day-1 pilot | 0.00–2.22 | permissive threshold from 28/09 live rest 2.25 V and 2.225–2.350 home | **0** | 250 | 1 ms home/rest-pad contact gate; 5 s move; 8 µl; fixed 3 V spout |
| [training/02_micro_push_day1_restpad.txt](training/02_micro_push_day1_restpad.txt) | 2 Day-1 rest pad + micro push (16 Oct) | 0.00-2.47 | home 2.47-2.56 (measured 2.48-2.525 at baseline, object on) | **0** | 250 | 100 ms home + capacitive pad gate; 3 s move; 4 ul (130 ms); 2 s ITI; spout columns 0 V (no spout motion) |
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

## Full-system bench test

Use `push_bench_full-system.txt` without an animal and without the joystick
fitted; move the base by hand. Its home and start fields are copied exactly
from the older expert-mouse file `training/07_expert.txt`: push/white
2.46–2.54 V, lateral/red 2.40–2.65 V, `home TO=250 ms`, and `start TO=0`.
The success threshold remains the wider bench range 0.00–2.22 V rather than
the expert file's narrow target. Before Run:

1. Keep the Class 3B laser keyed off. Do not power the unfused PVA/Ledex.
   The file commands `mag=0`.
2. Stop the manual-reward and standalone rest-pad test VIs. Prime the water line
   until it is bubble-free.
3. Position the base so both live signals are inside the expert home box:
   push/white 2.46–2.54 V and lateral/red 2.40–2.65 V. Set the
   front-panel rest-pad threshold from the live signal; use about 2.5 V
   (the capacitive pad outputs 0 V / 5 V).
4. Set `Session start spout (V)` to **0.0 V** so this test visibly exercises
   both protraction and retraction.

Suggested sequence:

1. Leave the pad untouched and confirm no trial starts.
2. Activate the pad while the object is home, then do not push for 5 s.
   Confirm the movement timeout returns to Case 0 with no cue, water or spout
   motion.
3. Activate the pad again and push the white/push signal below 2.22 V within
   5 s. Confirm one 50 ms cue, 500 ms delay, spout protraction to 3 V,
   2000 ms settle, one 185 ms water pulse (~6 µl), 1500 ms consumption, and
   retraction to 0 V.
4. Repeat several successes, then press normal Stop during idle and during a
   reward sequence on separate runs. Confirm all loops stop, the spout ends
   retracted, acquisition indicators did not freeze, and no DAQ error appears.

The parameter file can select criteria and output timings, but operator
actions determine whether the rest-pad gate, timeout and success branches are
actually exercised. It cannot safely test the magnet until the required 1 A
inline fuse is installed and magnet commissioning resumes.

## Stages that are **not** a parameter file

| Stage | Why | What to do instead |
| --- | --- | --- |
| 1 Habituation (cue → water, no push) | Water loop only wakes on Case 4 | Run `deliverWater_RIG1_cue.vi` once per manual reward. It gives a fixed 50 ms cue, then water for the front-panel `Water on time (ms)` value. |
| Pad-contact shaping (supervised fallback) | Rewards pad contact without requiring joystick movement | Use `training/01_pad_contact_shaping_50ms.txt` (or `_250ms`) only after a hand-contact bench test. Its full-range home/end boxes make joystick position irrelevant within 0–5 V. It does not require release-to-rearm, so held contact can earn another reward after each 2 s ITI; supervise reward count and stop if this is not intended. |
| 6 Delay / retractable spout | Files exist (`06_delay_*`) | Load 0 → 250 → 500; use 1000 only if desired and tolerated. Do not change the zone in those sessions. |
| 8 Shadow block labels | No column for block ID; magnet still absent | Run `08_shadow` as one 300-trial zero-force session. Split 50/75/100/75 later if needed. |
| 9 Experiment (Baseline / Random / Fixed / Washout) | Random/Fixed need a force-calibrated magnet | Baseline ≈ `07_expert`. Do not write `mag ≠ 0` files yet. |

## Front panel during these files

The loader and water loop in the repository VI read columns 22–27 from the
file. That extension was runtime-tested on the rig on 09/09/26 and imported
on 21/09/26. The 27/09/26 cluster-order fix for `reward delay` and
`spout retract` is in the same VI. Log the selected filename with the session.

For `02_micro_push_day1_5s_8ul.txt`, set the front-panel
`Session start spout (V)` control to **3.0 V** before Run. The file also writes
3.0 V for both extend and retract, so the spout remains extended throughout
the session; normal Stop still retracts it. Bench testing on 27/09/26 corrected
the loader/water-loop cluster-order mismatch for `reward delay` and
`spout retract`. The front-panel captions were corrected separately without
changing the working underlying labels.

## Loader

`Push Behaviour_MCHALABI.vi` on `master` already loads 27 columns and the
water loop already uses those fields. Cases 21–26 are `reward delay`,
`cue duration`, `spout extend`, `spout settle`, `consumption`, and
`spout retract`. Do not expand the cluster or add those cases again.

On 27/09/26 the loader cluster and the water-loop cluster had `reward delay`
and `spout retract` swapped because the clusters were the same type of
numbers in a different order. That mismatch was fixed on the rig and is in
the repository VI. The front-panel captions were corrected without renaming
the working labels.

Habituation (cue→water with no push) is still a separate LabVIEW mode. These
columns do not create that.
