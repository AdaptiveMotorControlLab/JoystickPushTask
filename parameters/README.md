# Parameter files

Tab-separated doubles, one line = one trial. The base format has **27 columns**;
columns 22–27 are reward delay, cue duration, spout extend, spout settle,
consumption, and spout retract (order confirmed 29 Sep 2026). Three optional
columns follow: 28 `vel threshold`, 29 `reward on touch`, 30 `joystick only`,
31 `repeat trials`. The loader in `Push Behaviour_MCHALABI.vi` reads up to 31
columns (since 5 Nov 2026) and loads any missing optional column as 0, so
27-, 28-, 29- and 30-column files behave as before. Every row of a file must have the same number of columns, and
every file keeps `mag` = 0.

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
| 27 | 28 | `vel threshold` | **Optional, velocity mode (VI built 22 Oct, in mouse sessions since 22 Oct).** `abs(d push) + abs(d lateral)` over a 200-sample look-back, computed on push and lateral smoothed by a 10-sample moving average (since the 22 Oct edit; it was a raw 50-sample lag before); Case 3 pays when above it. 0 = off. 27-column files load it as 0. Current files use 0.006; the 0.012 / 0.015 files were sized for the old raw rule. |
| 28 | 29 | `reward on touch` | **Optional (VI built 4 Nov; user-reported animal-free bench test passed 4 Nov; no mouse session yet).** 0 = pay on pad release (as before); 1 = pay when the `home TO` hold completes, paw still on the pad (EVENTS code 8 instead of 6), and the paw must lift before the next trial can start. 27- and 28-column files load it as 0; a touch-mode file needs all 29 columns. Ignored when `joystick only` = 1. |
| 29 | 30 | `joystick only` | **Optional (VI built 5 Nov; bench test pending, nothing verified at runtime).** 0 = rest-pad sequence (pad hold, go cue, release or touch per column 29, then joystick). 1 = joystick-only: the rest pad is ignored (no pad hold, no release, no re-arm) and no go cue; a trial arms when the joystick is held in the home box for `home TO` and the ITI has elapsed (EVENTS code 9), then the usual start box, end box / `end TO`, `vel threshold`, `move time` and reward columns apply. 27- to 29-column files load it as 0; a joystick-only file needs all 30 columns. |
| 30 | 31 | `repeat trials` | **Optional (5 Nov; loader step 1 done, Case 3 timeout logic built, bench test pending).** 0 = the next trial uses the next row (as now). 1 = if this row's trial times out (`move time`, EVENTS code 5), the next trial uses the same row again; a success still moves on to the next row. Read from the row that just ran, so a file can mix repeating and non-repeating rows. 27- to 30-column files load it as 0; a repeat file needs all 31 columns. With repeats, trial n is no longer row n: the EVENTS code 3 value is the 1-based row number. |

Velocity-mode files (28 columns): `training/02_micro_touch_velocity_200ms_thr0p012.txt` and `_thr0p015.txt`
(500 rows; home push 2.43-2.53, `home TO` 200, end box 0-1 V so only velocity pays, `move time` 5000).
`training/02_micro_touch_velocity_200ms_thr0p006_smooth_1hr_3ul.txt` is the same as `..._smooth_1hr.txt` (28 columns, 500 rows, `move time` 3600000) except `watertime` = 100 ms (~3 µl; 0.035 µl/ms fit, measured 3.2 µl at 100 ms) instead of 130 ms (~4 µl). Not yet run with a mouse.
`..._smooth_1hr_2ul.txt` is the `_1hr_3ul` file with `watertime` = 70 ms (~2 µl). `..._smooth_3s_2ul.txt` is the same with `move time` = 3000 ms (3 s) instead of 3600000. 70 ms is interpolated between the 50 ms (1.2 µl) and 100 ms (3.2 µl) calibration points (the linear fit gives 71 ms); the fit is only stated valid above ~100 ms, so weigh a 70 ms pulse before using it. Not yet run with a mouse.

`..._smooth_2s_1p5ul.txt` is the `_1hr_2ul` file with `watertime` = 58 ms (~1.5 µl, interpolated between the 50 ms / 1.2 µl and 100 ms / 3.2 µl calibration points; below the range the fit is stated valid for, so measure it before use) and `move time` = 2000 ms (2 s). Not yet run with a mouse.

`training/01_pad_touch_{50,100,200}ms_release_3ul.txt` are the touch-and-release (hold & release) files with `watertime` = 100 ms (~3 µl, measured 3.2 µl) instead of 130 ms (~4 µl); nothing else changed (250 rows, 27 columns). Not yet run with a mouse.

`02_micro_touch_velocity_50ms_thr0p006_smooth_1hr_3ul.txt` is the `_200ms_..._1hr_3ul` file with `home TO` = 50 ms instead of 200 ms (28 columns, 500 rows, `move time` 3600000, `watertime` 100 ms). Not yet run with a mouse.

`02_micro_touch_velocity_100ms_thr0p006_smooth_1hr_2ul.txt` (29 Oct) is the `_50ms_..._1hr_3ul` file with `home TO` = 100 ms and `watertime` = 70 ms (~2 µl, interpolated as in `_1hr_2ul`; weigh it). 28 columns, 500 rows, `move time` 3600000. `..._100ms_thr0p006_smooth_3s_2ul.txt` is the same with `move time` = 3000 ms (3 s). Not yet run with a mouse.

`02_mixed_touch1_cube1_100ms_thr0p006_smooth_5s_1p5ul_3ul.txt` (29 Oct, for zuchon; 28 columns, 500 rows) alternates two row types, starting with a touch row.
Odd rows (1, 3, ...) are the `01_pad_touch_100ms_release_3ul` row with `vel threshold` 0 and `watertime` 58 ms (~1.5 µl, interpolated like `_2s_1p5ul`; weigh it): joystick ignored, paid at pad release.
Even rows are the `02_micro_touch_velocity_50ms_..._1hr_3ul` row with `home TO` 100 and `move time` 5000 (`watertime` stays 100 ms, ~3 µl, measured 3.2 µl): home push 2.43-2.53, paid only for a cube movement (velocity > 0.006) within 5 s of release.
Both rows use ITI 2000 ms. Untested: that the VI applies each row's boxes, `vel threshold` and `watertime` to its own trial, and that a timed-out cube trial moves on to the next row. Bench-test this before a mouse.

`03_push_distance_200ms_20mV_1s_1p5ul.txt` (30 Oct, for anaconda; 28 columns, 500 identical rows) is the first distance-based file (velocity rule off, `vel threshold` 0): pad hold 200 ms with home push 2.438-2.482 V (measured rest band), paid when push < 2.41 V (end box 0-2.41 V, `end TO` 0; well below home so home and end do not overlap), `move time` 1000 ms, ITI 1500 ms, 58 ms water (~1.5 µl, interpolated as in `_2s_1p5ul`; weigh it), cue 50 ms, delay 0, consumption 1000 ms (was 1500), spout columns 0. Consumption is only the water-loop wait before the spout-retract command, so with a fixed spout it does not limit drinking; cutting it makes the water loop (cue + water + consumption ≈ 1.1 s) finish inside the 1.5 s ITI, avoiding the unpaid-success bug without raising the ITI. Choice from the 29 Oct anaconda notebook: 20 mV keeps 71 % of the velocity-paid rewards (30 mV: 52 %, 40 mV: 45 %). Re-centre the home box on the measured rest voltage r before a session (home r ± 0.010, push bound r - 0.020; the 10 mV gap keeps the minimum required push at 10 mV). Not bench-tested, not run with a mouse.

`02_micro_touch_velocity_100ms_thr0p006_smooth_3s_home2p46-2p51_1p5ul.txt` (2 Nov, for blackmamba; 28 columns, 500 identical rows) is the `02_micro_touch_velocity_200ms_thr0p006_smooth_3s_1p5ul.txt` file with `home TO` 100 ms (was 200) and home push 2.46-2.51 V (was 2.43-2.53). Everything else unchanged (`move time` 3000 ms, ITI 1500 ms, 58 ms water ~1.5 µl, velocity threshold 0.006). Not bench-tested, not run with a mouse.

`02_mixed_touch1_cube1_100ms_thr0p006_smooth_10s_home2p46-2p51_2ul.txt` (2 Nov, for zuchon; 28 columns, 500 rows) is the `..._smooth_5s_1p5ul_3ul` file with cube-row `move time` 10000 ms, cube-row home push 2.46-2.51 V (was 2.43-2.53), and `watertime` 45 ms (~1 µl) on touch rows, 70 ms (~2 µl) on cube rows. 70 ms is interpolated; 45 ms is extrapolated below the lowest calibration point (50 ms / 1.2 µl, line through 50 and 100 ms), so measure both before use. Touch rows keep the joystick ignored (home 0-5 V). Not bench-tested, not run with a mouse.

`03_push_distance_200ms_home2p46-2p51_end2p43_1s_1p5ul.txt` (2 Nov) is identical to `03_push_distance_200ms_20mV_1s_1p5ul.txt` except home push 2.46-2.51 V and success when push ≤ 2.43 V (end box 0-2.43 V; 30 mV gap below home). 28 columns, 500 rows. Not bench-tested, not run with a mouse.

`03_push_distance_200ms_home2p46-2p51_end2p40_1s_1p5ul.txt` (3 Nov) is identical to the `_end2p43_` file except success when push ≤ 2.40 V (end box 0-2.40 V; 60 mV gap below home). 28 columns, 500 rows. Not bench-tested, not run with a mouse.

`training/01_pad_touch_200ms_release_2ul.txt` (3 Nov) is `01_pad_touch_200ms_release_3ul.txt` with `watertime` = 70 ms (~2 µl, interpolated between the 50 ms / 1.2 µl and 100 ms / 3.2 µl calibration points; weigh it, measure before use). 250 rows, 27 columns, nothing else changed. Not bench-tested, not run with a mouse.

`training/01_pad_touch_100ms_touch_2ul.txt` (4 Nov) is the first reward-on-touch file: the `01_pad_touch_100ms_release_2ul` row with ITI 2000 ms (was 1500, avoids the unpaid-success bug), `vel threshold` 0 and `reward on touch` 1. 500 rows, 29 columns. Used for the 4 Nov animal-free bench test of the touch mode (user-reported OK); not run with a mouse.

`training/01_pad_touch_200ms_touch_1p5ul.txt` (5 Nov) is `01_pad_touch_100ms_touch_2ul.txt` with `home TO` = 200 ms (was 100) and `watertime` = 58 ms (~1.5 µl, interpolated as in `_2s_1p5ul`; below the range the fit is stated valid for, so measure before use). 500 rows, 29 columns, nothing else changed. Not bench-tested, not run with a mouse.

`training/02_micro_touch_velocity_200ms_thr0p006_smooth_2s_home2p46-2p51_1p5ul.txt` (5 Nov) is `02_micro_touch_velocity_100ms_thr0p006_smooth_2s_home2p46-2p51_1p5ul.txt` with `home TO` (rest-pad hold) = 200 ms (was 100). Nothing else changed. Not bench-tested, not run with a mouse.

`push_bench_joystick-only.txt` (5 Nov) is the first joystick-only file: the `03_push_distance_200ms_home2p46-2p51_end2p40_1s_1p5ul` row with `reward on touch` 0 and `joystick only` 1 appended. 500 rows, 30 columns. Joystick home 2.46-2.51 V held 200 ms, paid when push ≤ 2.40 V within 1 s; the pad is not used. For the pending joystick-only bench test (checklist in `docs/PROJECT_PLAN.md`); not run with a mouse.

`training/02_pad_velocity_100ms_thr0p006_smooth_5s_1p5ul_iti1p5.txt` (30 Oct, for zuchon; 28 columns, 500 identical rows) uses only the cube row of the 29 Oct mixed file (no touch-only trials) with water 58 ms (~1.5 µl, interpolated; weigh it; was 100), ITI 1500 (was 2000) and consumption 1000 ms (was 1500): `home TO` 100, home push 2.43-2.53, end box 0-1 V (only velocity pays), `vel threshold` 0.006, `move time` 5000. Not bench-tested, not run with a mouse.

`training/02_micro_touch_velocity_100ms_thr0p006_smooth_2s_home2p46-2p51_1p5ul.txt` (4 Nov; 28 columns, 500 rows) is the `_3s_home2p46-2p51_1p5ul` file with `move time` 2000 ms (was 3000). Not bench-tested, not run with a mouse.

`training/04_broad_zone_4-8mm_hold50ms_home2p46-2p51_1s_1p5ul.txt` (4 Nov; 28 columns, 500 rows) is `03_push_distance_200ms_home2p46-2p51_end2p40_1s_1p5ul.txt` with the end push box 2.235-2.365 V (8 / 4 mm from home on the 3 Nov calibration) and `end TO` 50 ms ("hold50ms" in the name; the pad hold `home TO` stays 200 ms). Pushing past 8 mm leaves the zone. Re-centre on the measured rest voltage if it is not ~2.47 V. Not bench-tested, not run with a mouse.

`push_bench_row-mapping.txt` (5 Nov) is the bench file for the parameter-row mapping fix (`docs/PROJECT_PLAN.md`, "Parameter-row mapping"). 40 rows, 28 columns. Odd rows are touch-and-release (all boxes 0-5 V, pay at pad release); even rows need a push (home push 2.43-2.53 V, end push 0-2.40 V). Every row has its own `watertime` (50 + row number, 51-90 ms) and `move time` (2000 + 50 × row number, 2050-4000 ms), so `scripts/check_row_mapping.py` can tell which row each code 15 value and timeout came from. All rows `home TO` 100, ITI 2000, cue 50 ms, delay 0, consumption 1500, spout columns 0, `mag` 0, `vel threshold` 0. No animal. Not bench-tested.

`push_bench_repeat-trials.txt` (5 Nov) is the bench file for `repeat trials`: `push_bench_row-mapping.txt` with `reward on touch` 0, `joystick only` 0 and `repeat trials` appended. 40 rows, 31 columns. `repeat trials` is 0 on rows 4, 8, ..., 40 and 1 on every other row, so even rows 2, 6, 10, ... repeat after a timeout and rows 4, 8, 12, ... do not; odd rows pay at release and test that a success still advances with the flag on. `scripts/check_row_mapping.py` follows the repeats (expected row, code 3 value, `watertime`, timeout length). No animal. Not bench-tested.

`training/01_pad_touch_50ms_release_2ul.txt` and `training/01_pad_touch_100ms_release_2ul.txt` (3 Nov) are the matching `_3ul` files with `watertime` = 70 ms (~2 µl, interpolated as above; measure before use). 250 rows, 27 columns, nothing else changed. Not bench-tested, not run with a mouse.

Raw-rule history (before the 22 Oct smoothing edit): noise on 20-21 Oct (paw on pad, cube untouched) had a 99.99th percentile of 7.8-8.0 mV and a max of 9-11.6 mV (same at lag 10-50 ms); with the 50 ms lag, 0.012 gave 0 noise onsets in 224 min. Bench-tested without a mouse on 22 Oct (touch pays, slow micro-push pays at lag 50). The smoothed rule's noise max is ~0.0045, hence the 0.006 files.

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

Scale measured 3 Nov 2026 on the current mount: **0.0295 V/mm** over 0–8 mm
(lower V = forward; 10 mV ≈ 0.34 mm; `calibration/joystick-volts-mm.md`). The
older stage files below were written with the 08/09/26 eyeball 0.030 V/mm.

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

This table covers the original stage files and bench presets; files added from
16 Oct 2026 on (touch-and-release, velocity, mixed, distance, broad-zone,
reward-on-touch and joystick-only) are described above, and the session → file
map is in `docs/PROJECT_PLAN.md`.

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

1. Keep the Class 3B laser keyed off. Leave the PVA/Ledex supply unplugged
   and the Enable clip off. The file commands `mag=0`.
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
actually exercised. It does not test the magnet; magnet tests follow
`MAGNET_COMMISSIONING.md`.

## Stages that are **not** a parameter file

| Stage | Why | What to do instead |
| --- | --- | --- |
| 1 Habituation (cue → water, no push) | Water loop only wakes on Case 4 | Run `deliverWater_RIG1_cue.vi` once per manual reward. It gives a fixed 50 ms cue, then water for the front-panel `Water on time (ms)` value. |
| Pad-contact shaping (supervised fallback) | Rewards pad contact without requiring joystick movement | Use `training/01_pad_contact_shaping_50ms.txt` (or `_250ms`) only after a hand-contact bench test. Its full-range home/end boxes make joystick position irrelevant within 0–5 V. It does not require release-to-rearm, so held contact can earn another reward after each 2 s ITI; supervise reward count and stop if this is not intended. |
| 6 Delay / retractable spout | Files exist (`06_delay_*`) | Load 0 → 250 → 500; use 1000 only if desired and tolerated. Do not change the zone in those sessions. |
| 8 Shadow block labels | No column for block ID; magnet not yet force-calibrated | Run `08_shadow` as one 300-trial zero-force session. Split 50/75/100/75 later if needed. |
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

`Push Behaviour_MCHALABI.vi` on `master` loads up to 31 columns and the
water loop uses columns 22–27. Loader cases 21–26 are `reward delay`,
`cue duration`, `spout extend`, `spout settle`, `consumption`, and
`spout retract`; cases 27–30 are `vel threshold`, `reward on touch`,
`joystick only`, and `repeat trials`, each added as the LAST entry of the
`exp values` and `exp para array` clusters (default 0). A new optional column
needs the same pattern: new last cluster entry, new loader case, Array Subset
length + 1.

On 27/09/26 the loader cluster and the water-loop cluster had `reward delay`
and `spout retract` swapped because the clusters were the same type of
numbers in a different order. That mismatch was fixed on the rig and is in
the repository VI. The front-panel captions were corrected without renaming
the working labels.

Habituation (cue→water with no push) is still a separate LabVIEW mode. These
columns do not create that.
