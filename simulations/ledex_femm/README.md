# Ledex 195224-230 field and target-force models (FEMM calibration, 3D target forces)

Two magnetostatic models of the Ledex STA 20 × 40 mm pull solenoid (60° plunger) and a steel washer
target in front of the protruding pull end, built on 11-12 Oct 2026 to estimate the resistance force
before the printed holder and a force jig exist.

- **FEMM (2D, axisymmetric)** reproduces the plunger force and was calibrated against the datasheet
  force-stroke curves. It cannot represent washers standing across the axis.
- **3D (NGSolve, `fea3d.py`)** rebuilds the same calibrated device and computes the pull on the
  washer tower standing across the axis with its rim facing the tip (the real layout).

All target forces, field maps and plots in `figures/plots/` and `figures/magnetic_fields/` come from the
3D model, except `calibration_fit.png` and `sensitivity.png` (FEMM). **These are model estimates, not
measurements.** Check them with one scale measurement once the printed holder and a gap jig are available.

![field maps](figures/magnetic_fields/overview_magnetic_fields.png)

## Main findings (3D model, ten M3 washers standing across the axis, plunger seated)

- The pull is very small at the currents the rig uses: about **1.2 g-force (12 mN) at 2 mm** and
  **2.5 g at 1 mm** at 10 V (0.31 A), 0.7 g at 3 mm.
- Below 10 V the force scales roughly with current squared: 1 V (0.074 A) gives only ~6 % of the
  10 V force (0.08 g at 2 mm). Raising `Imax` to the rated 0.58 A (the most the 12 V supply can push
  through the 20.7 Ω coil) gives about 1.8× the 10 V force (2.2 g at 2 mm, 4.7 g at 1 mm).
- It falls steeply with gap (roughly 2× per extra millimetre near the tip), so the resistance fades
  within a few millimetres of the object moving away from the Ledex.
- Taller towers help with diminishing returns (2 mm; 0.58 A in brackets, 10 V first): 1 washer
  0.39 g (0.75), 5 washers 0.79 (1.5), 10 washers 1.2 (2.2), 20 washers 1.6 (2.9), 40 washers 2.3 (4.4).
  Each washer is 0.8 mm thick (10 washers = 8 mm, about 3.5 g of mass on the joystick), the far
  washers sit in a weaker field, and the tower is modelled as solid, so real towers pull somewhat less.
- The seated plunger gives the strongest pull; holding it out from its seat lowers it (10 V, 2 mm:
  1.2 g seated, 0.63 g at 1.5 mm out, 0.13 g at 9.5 mm out).

| Gap | 1 V (0.074 A) | 2 V (0.106 A) | 5 V (0.180 A) | 10 V (0.310 A) | 0.58 A (Imax raised) |
| --- | --- | --- | --- | --- | --- |
| 0.5 mm | 0.33 g | 0.68 g | 1.9 g | 5.2 g | 9.7 g |
| 1 mm | 0.16 g | 0.32 g | 0.93 g | 2.5 g | 4.7 g |
| 2 mm | 0.075 g | 0.15 g | 0.44 g | 1.2 g | 2.2 g |
| 3 mm | 0.043 g | 0.089 g | 0.26 g | 0.68 g | 1.3 g |
| 5 mm | 0.018 g | 0.036 g | 0.10 g | 0.28 g | 0.52 g |

Pull on ten stacked M3 washers (3.2 × 9 × 0.8 mm, mild steel) standing across the axis, plunger
seated; 1 g = 9.81 mN. Best-fit calibration; the spread over the accepted calibration sets is in
`figures/plots/target_force_band.png`. (The earlier FEMM five-washer ring gave about 0.96 g at 2 mm
and 10 V, in `results/sweeps.csv`; it is not the real layout.)

![target force band](figures/plots/target_force_band.png)

## Calibration against the datasheet

- Data: Ledex STA pull 20 × 40 catalog (`datasheet/ledex_195224_sta_pull_20x40.pdf`). The 60°
  plunger force-stroke chart (page F19, `datasheet/chart_60deg_force_stroke.png`) was digitized
  with `datasheet/digitize.py` into `datasheet/ledex_195224_60deg_force_stroke.csv`: four curves
  (100/50/25/10 % duty = 7/14/28/70 W = 855/1200/1700/2700 ampere-turns = 0.57/0.80/1.14/1.81 A
  at 1491 turns, 20 °C coil), 0.75–15 mm stroke, plus the 12.8 N holding force.
  `datasheet/digitize_check.png` overlays the digitized points on the chart.
- Geometry from the drawing (page F34, `datasheet/drawing_pull_F34.png`, energised = seated):
  the pull end sits 19.05 + 4.76 = **23.81 mm** beyond the body face (the 9.5 mm used before is
  the depth of the 2.5 mm tip slot), the M14 × 1.5 boss is 9.52 mm long on the plunger side, and
  the plunger length follows from its 20.1 g mass.
- Fitted (not published): seat gap (air-gap spacer), radial clearance (nylon bearing), steel
  saturation scale on the 1010 B-H curve, end-plate thickness, case wall, cone half-angle. The
  plan fixed the cone at 30° and did not fit the clearance; with those fixed the holding force
  stayed 1.5× high, so both were added.
- Method (`calibrate.py`): error = RMS of ln(model / datasheet) over the 100/25/10 % curves and the
  holding force; the 50 % curve is held out as a check. 60-set Latin-hypercube screen, two
  Nelder-Mead runs from the best distinct starts (both converged to the same region), then 48
  random sets around the optimum: 249 parameter sets, 60 FEMM solves each.
- Result: fitted error 0.18 (before: 0.44), **held-out 50 % curve 0.19** (before: 0.51), i.e.
  typically within ±15–20 %. Up to 7 mm stroke the model is within about ±15 % at all four
  currents; beyond 8 mm stroke it still reads 1.4–2× high at 0.57–1.14 A. Seated holding force
  13.0 N vs 12.8 N. See `figures/plots/calibration_fit.png`.
- Best fit (`results/calibration/best_params.json`): seat gap 1.0 mm, clearance 0.8 mm, steel
  scale 0.98, plates 1.58 mm, wall 0.8 mm, cone half-angle 37.5°. Seat gap, clearance and wall
  sit on their bounds, so treat them as effective values that make the magnetic circuit right,
  not as real dimensions.
- Uncertainty band: 134 sets fit within 1.2× the best error (`accepted_sets.csv`; seat gap
  0.52–1.0 mm, clearance 0.68–0.8 mm, steel scale 0.82–1.05, plates 1.5–2.8 mm, wall 0.8–1.6 mm,
  cone 30–42°). The 3D target force of the ten-washer tower was recomputed for 16 well-spread ones
  (`sweep3d.py band`, rows with a numeric `set` in `results/fea3d_sweep.csv`) and gives the bars and
  shading in `force_vs_gap.png`, `force_vs_current.png` and `target_force_band.png`.

![calibration fit](figures/plots/calibration_fit.png)

Caveats:

- The datasheet only gives the plunger force, and only at 0.57–1.81 A. The target force (the
  fringe field outside the body) and the rig currents (0.05–0.31 A) are both outside the fitted
  data. The model is linear (force ∝ current²) at those currents, as the datasheet curves are
  between 0.57 and 0.80 A, so the extrapolation is plausible but untested.
- The remaining long-stroke error (model high when the plunger is mostly out, where fringe
  field matters most) suggests the target force is, if anything, still overestimated.
- Sensitivity of the calibrated model at 2 mm (`figures/plots/sensitivity.png`): protrusion
  ±0.3 mm (drawing tolerance) ±3 %, no tip slot +9 %, other steel grades −12 to +9 %, mesh < 1 %.
- Treat absolute numbers as uncertain by about ±40 %; trends (gap, current², target size) are
  reliable. One measurement at 2 mm will settle the scale.

## 3D model: washers standing across the axis

FEMM is axisymmetric, so it can only model washers stacked on the axis as a ring. The real layout is a
tower of washers standing across the solenoid axis, with the tip facing the rims. `fea3d.py` is a
quarter-symmetry 3D magnetostatic model (NGSolve, edge elements, nonlinear 1010 B-H with the fitted
BSCALE, Maxwell-stress force) that reuses the calibrated geometry. It can also hold the plunger out
from its seat (`stroke`). It gives the pull on the target only; the force on the plunger is not
computed. Setup: `python3 -m venv /tmp/ngenv && /tmp/ngenv/bin/pip install ngsolve numpy scipy`.

Validation: a coaxial ring of 5 washers, 2 mm, 0.31 A gives 0.90 g in 3D (mesh and box changes move it
by under 2 %) against 0.96 g in FEMM, so the 3D model is about 6 % low.

Pull (g-force) of a washer tower across the axis, tip to nearest rim, 0.58 A (10 V, 0.31 A, in brackets):

| washers | 1 mm | 2 mm | 3 mm |
|---|---|---|---|
| 1 | 1.2 (0.63) | 0.75 (0.39) | 0.50 (0.26) |
| 5 | 2.5 (1.4) | 1.5 (0.79) | 0.93 (0.49) |
| 10 | 4.7 (2.5) | 2.2 (1.2) | 1.3 (0.68) |
| 20 | 6.8 (3.4) | 2.9 (1.6) | 1.7 (0.91) |
| 40 | 8.9 (5.0) | 4.4 (2.3) | 2.4 (1.3) |

Gains from extra washers flatten past 10. Uncertainty: about ±10 % from the nonlinear iteration near
saturation at 0.58 A, plus the calibration extrapolation (±40 %).

## Model

- Published: case 19.56 mm dia × 39.37 mm, M14 boss 9.52 mm, plunger 7.82 mm dia and 20.1 g,
  23.81 mm protrusion, 2.5 × 9.5 mm tip slot (modelled as an equal-area axial hole),
  1491 turns (30 AWG, 20.7 Ω), 60° plunger. Measured: coil current at each AO command
  (Checkpoint 4, `calibration/README.md`).
- Fitted: see above. Assumed: bobbin 0.5 mm, 1 mm flat at the cone apex, "1010 Steel" for the
  target, washer tower modelled as solid steel (real interfaces between washers lower the force
  slightly). The PWM drive is modelled as its average DC current.
- Coordinates: `z = 0` at the front face of the case body, boss at −9.52 < z < 0, plunger tip at
  `z = -23.81`, targets beyond the tip. The field-map figures turn this sideways (position along
  the axis x = −z; 0 mm = body face, tip at 23.8 mm).

## Files

- `ledex_washer.lua`: the FEMM 4.2 model (modes `forces`, `profile`, `stroke`, `sweep`,
  `plunger`, `fieldgrid`, `map`). Every parameter can be overridden by the caller; defaults are
  the calibrated values.
- `femm_run.py`: runs FEMM in parallel on Windows or on a Mac under Wine (Python 3.6+, standard
  library only). `python3 femm_run.py sweeps` (all sweeps and field grids; `--only <regex>`,
  `--no-grids`), `summary` (`results/forces.csv`, `axial_B.csv` (field along the plunger outer edge r = 3.91 mm, not the slotted axis), `stroke.csv`), `maps` (FEMM
  screenshots in `figures/plots/femm/`, needs Pillow for PNG). `FEMM_WORKERS` sets the number of
  parallel FEMM processes.
- `calibrate.py`: the datasheet fit (`screen`, `refine`, `explore`, `best`, `band`, or `all`);
  writes `results/calibration/` (`fit_log.csv` one row per parameter set, `fit_points.csv` model
  vs datasheet per point, `best_params.json`, `accepted_sets.csv`, `target_band.csv`).
- `fea3d.py`: the 3D model (see above); `python fea3d.py check` compares a coaxial stack with FEMM.
- `sweep3d.py`: resumable 3D sweeps (`grid`, `stacks`, `stroke`, `band`, `axial`) written to
  `results/fea3d_sweep.csv` (`set`, `n_washers`, `gap_mm`, `stroke_mm`, `current_A`, `force_g`; `set`
  = `best` or the FEMM eval number of an accepted calibration set) and `results/axial_B3d.csv`.
  Older `results/fea3d.csv` holds the first across-axis runs (best fit only).
- `plot_results.py`: makes `figures/plots/*.png` (numpy + matplotlib). The force, stroke, target and
  profile figures read the 3D CSVs; `calibration_fit.png` and `sensitivity.png` read the FEMM CSVs.
- `plot_target_across.py`: makes `figures/magnetic_fields/*.png` from the 3D model (needs the
  NGSolve venv; solved fields cached in `results/fieldcache3d_*.npz`).
- `results/sweeps.csv`: one row per FEMM solve (coaxial layouts, used for the calibration and sensitivity figures). Columns: `case`, `target`,
  `target_id_mm`, `target_od_mm`, `target_t_mm` (inner/outer diameter, thickness; id 0 = solid
  disc), `protrude_mm`, `seat_mm`, `stroke_mm` (plunger held out from its seat), `bscale`,
  `tpl_mm`, `wall_mm`, `steel`, `target_mesh_mm`, `gap_mm` (tip to target face), `current_A`,
  `target_force_N`, `target_force_g`, `plunger_force_N` (axial force on the plunger, toward the
  seat), `clr_mm`, `conea_deg`. Cases: `baseline_gap*` (five washers, 11 gaps × 12 currents),
  `target_*` (other targets), `stroke_*`, `sens_*`.
- `results/fieldgrid_<target>_<current>A.csv`: FEMM field grids (`r_mm, z_mm, Br_T, Bz_T, Bmag_T` on a
  0.25 mm grid) for the coaxial layouts; no longer plotted (the field maps now come from the 3D model).
- `results/uncalibrated/`: the first model (9.5 mm protrusion, guessed internals), kept for
  comparison.
- `figures/magnetic_fields/`: 3D field maps with a mT colour scale: `notarget_<I>A.png`,
  `target_gap{1,2,3}mm_<I>A.png` (ten washers across the axis) and `overview_magnetic_fields.png`
  (rows: no target, 1, 2, 3 mm; columns: five currents). `figures/plots/`: force, stroke, field
  profile and calibration figures. `figures/plots/femm/`: raw FEMM screenshots of the coaxial layouts
  (colour scale 0–0.05 T), kept for the record.
- Command voltage to current (minimum `Imax`): 0.5 V 0.053, 1 V 0.074, 2 V 0.106, 3 V 0.121,
  4 V 0.147, 5 V 0.180, 6 V 0.201, 8 V 0.273, 10 V 0.310 A; 0.40–0.58 A need `Imax` raised.

## Running FEMM

Rig PC: FEMM 4.2 is installed in `C:\femm42`; run `python femm_run.py sweeps` from this folder
(4 parallel FEMM processes by default). Full sweeps take about 5 minutes on a Mac with 10 workers;
the calibration took about 2.5 hours.

Mac (Apple Silicon) under Wine, as set up on 11 Oct 2026:

1. `softwareupdate --install-rosetta --agree-to-license`
2. Wine: download `wine-staging-11.18-osx64.tar.xz` from
   [Gcenx/macOS_Wine_builds](https://github.com/Gcenx/macOS_Wine_builds/releases) and unpack it to
   `~/Applications/wine/` (gives `Wine Staging.app`; the Homebrew casks are disabled).
3. `WINEPREFIX=~/.wine-femm wineboot` to create the prefix.
4. FEMM: the installer crashes under Wine, so unpack it instead: download
   `femm42bin_x64_21apr2019.exe` from [femm.info](https://www.femm.info/wiki/Download),
   `brew install innoextract`, `innoextract -s femm42bin_x64_21apr2019.exe`, then copy `app/` to
   `~/.wine-femm/drive_c/femm42`.
5. FEMM needs `mfc90.dll`: run the extracted `tmp/vcredist_x64.exe /q` under Wine with the same
   prefix.
6. `femm_run.py` finds Wine at the default path (override with `FEMM_WINE`, prefix with
   `WINEPREFIX`). A Lua error opens a dialog that blocks FEMM until the job timeout; bitmap export
   needs a visible window.
