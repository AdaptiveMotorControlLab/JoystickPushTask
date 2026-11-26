# 3D-printed parts and CAD models

Every model is an editable STEP source plus a slicer-ready STL, one subfolder per part. Frames and the
rig layout are in `simulations/ledex_femm/rig_geometry.py` (README "Rig geometry"); the Ledex holder and
plunger-link parts have their own [README](ledex-holder-adjustable/README.md). Superseded designs are in
[`archive/`](../archive/).

The push object is a compact rounded cube that sits below the mouse in the natural forelimb workspace and
presents a push-biased surface that discourages grasping like the original pull handles. Add new parts as a
named subfolder (STEP + STL, descriptive filenames) and a row in the table below; no README per folder.

On the rig: the adjustable Ledex holder, link collar and link bar (since 1 Nov 2026), and now the wide-window
constrainer and the 15.1 mm cube (fitted after 5 Nov, date not recorded; they replaced the 16 mm window
constrainer, now archived). The Ledex-off hand check (full return to home, no binding) passed on the current
parts (15 Nov), and 17 hand releases from 2-37 mm all settled within ±3.6 mV of home. Still to do: measure the
return spring statically with weights; re-measure the push axis volts → mm after the stereo calibration (the
0-8 mm calibration in `calibration/joystick-volts-mm.md`, 3 Nov, predates the current cube and constrainer).
**Metal joystick (designed 26 Nov 2026, not printed or fitted):** the printed PLA shaft bends at low force when
the Ledex link holds it at the collar, so it is being replaced by an 80 mm metal joystick (1.6 g, non-magnetic,
Ø2.74 mm arm; reference model in `joystick/`). The 27 mm cube, the 3.45 mm-bore link collar and the new
`fit_test` go with it; `rig_geometry.py` and all force figures already use it (rerun 26 Nov). Next: print
`fit_test`, pick the cube hole and collar bore, print the cube and collar, fit them, then re-centre home,
redo the Ledex-off hand check and the volts → mm calibration.

Print notes: PETG or PLA, orientation and fit allowances for the holder parts are in the Ledex holder
README (printed holes come out ~0.3-0.4 mm small; print `fit_test` first).

| Folder | Files | Status | What it is |
| --- | --- | --- | --- |
| `joystick/` | `joystick_metal_80mm`, `make_joystick_metal.py` | reference, not printed; to replace the printed shaft on the rig | 80 mm metal joystick (base Ø6.35 × 8 mm, 2.5 mm transition, Ø2.74 mm arm, rounded tip) that screws onto the thumbstick stub; the cube slides onto its tip. The printed 89 mm PLA shaft still on the rig is archived in `archive/joystick/`. |
| `TS-1D1S00A-1294_stripped/` | `TS-1D1S00A-1294_stripped` | reference, not printed | Measured APEM TS-1D1S00A-1294 Hall base (castle cap removed). |
| `joystick-holder/` | `joystick_holder` | printed, on the rig | Breadboard holder for the component. |
| `joystick-handle-cube/` | `joystick_handle_cube_11p5_h27_d3p1_dp8`, `make_handle_cube.py` | newest revision (26 Nov), for the metal joystick, not printed; the 15.1 mm one on the rig and older revisions archived | Narrow rounded-cube push object, 11.5 × 11.5 × 27 mm; the script regenerates it. |
| `joystick-1d-axis-constrainer/` | `..._38x38x56_ledex_wide_window`, `make_wide_window.py` | wide-window revision, printed, on the rig | Stepped hollow box that limits the joystick to one axis; home wall open over almost its whole width for the plunger link. |
| `ledex-holder-adjustable/` | base, upright, carriage, `link_collar`, `link_bar`, `fit_test`, `make_ledex_holder.py` | holder, collar and link printed and mounted 1 Nov | Adjustable Ledex holder and plunger link (see its README). |
| `ledex-195224-model/` | `ledex_body`, `ledex_plunger` | reference, not printed | Ledex body and plunger from the datasheet drawing. |

## Joystick component and holder

- **Component:** round body 25.3 mm diameter, 11.53 mm tall; flange 29.75 mm diameter (z 11.53-13.09); stepped
  dome up to z 18.28; stem to z 23.45; a 9.6 × 2.1 mm cross-bar at z 23.87-26.27; 4.3 mm stub to z 29.3. The
  metal joystick screws onto the stub and its base bottom stands 1 mm above the stub top (z 30.3, world Z
  44.18; measured by the user). The printed shaft's 5 mm × 2.7 mm bottom bore held a glued screw and its cone
  sat on the stub top (shaft base z 29.3, world Z 43.18). The pivot is inside the body and not modelled (the
  models assume mid-body, z 5.8, and test z 2-10).
- **Holder:** base 86 × 31.8 × 5 mm with four 10 × 24 mm slots, four 5 × 5 mm corner posts (z 5-20.4, open
  sides for the cable), top frame z 20.41-25.41 (31.82 mm square, 25.3 mm hole). The component's flange rests
  on the frame, so the body bottom is 13.88 mm and the shaft base 40.5 mm above the breadboard. The push runs
  along the 31.8 mm width; the Ledex stands on the breadboard on the mouse (home) side.

## Handles

- **Narrow cube (11.5 mm wide, chosen 17 Oct):** 11.5 × 11.5 mm footprint, 3 mm corner radius, 2.5 mm top
  fillets, three blind holes along the push axis (push face 2.05 / 5.75 / 9.45 mm from the shaft axis).
  The 27 mm revision (26 Nov) is for the 80 mm metal joystick, whose tip ends 5.45 mm below the old cube's
  bottom: same footprint and top height (world Z 144.73), the body runs down to Z 117.73 and the Ø3.1 × 8 mm
  holes grip 6.45 mm of the 2.74 mm arm (tip at the centre of the ball end). Ø3.1 is a snug-fit guess
  (printed holes come out ~0.3-0.4 mm small); check it on `fit_test` (holes 2.8-3.6) before printing the cube.
  The cube bottom is 11.9 mm lower than before: check it clears the rest platform at home. The
  shaft goes in the front hole (nearest the mouse) so the paw cannot touch cube and rest pad together. At home
  the cube is 2 mm from the rest platform (3 Nov). `make_handle_cube.py` (CadQuery, ball-ended holes) writes
  the newest revision and can rebuild the 14.1 mm one for comparison; only the newest is kept here:

  | Revision | Height | Holes (diameter × depth) | Volume | Where |
  | --- | --- | --- | --- | --- |
  | `joystick_handle_cube_11p5` (17 Oct) | 10.0 mm | 3.2 × 3.2 mm | 1130 mm³ | archive; used by the force models until 15 Nov |
  | `joystick_handle_cube_11p5_h14p1` (28 Oct) | 14.1 mm | 3.2 × 3.2 mm | 1641 mm³ | archive |
  | `joystick_handle_cube_11p5_h15p1_d3p3_dp4p2` (5 Nov) | 15.1 mm | 3.3 × 4.2 mm | 1736 mm³ | archive; on the rig with the printed shaft |
  | `joystick_handle_cube_11p5_h27_d3p1_dp8` (26 Nov) | 27.0 mm | 3.1 × 8.0 mm | 3143 mm³ | here; for the metal joystick, not printed |

  `simulations/ledex_femm/rig_geometry.py` uses the 27 mm cube on the metal joystick (`CUBE_STL`, cube at shaft z
  73.55-100.55). The push is still taken at world Z 137.18 (the 15.1 mm cube's mid-height on the printed shaft),
  so the lever ratios are unchanged; force figures and tables rerun 26 Nov (within 1.5 % of the old ones).
  `make_handle_cube.py --check-h15p1` / `--check-old` rebuild the archived 15.1 / 14.1 mm revisions exactly.
- **Original 20 mm cube** (used from the first mouse session, 16 Oct) and the older narrow-cube revisions are
  archived in [`archive/joystick-handle-cube/`](../archive/joystick-handle-cube/).
- **38 × 3 × 3.1 mm bar handle** (never fitted) is archived in [`archive/joystick-handle-bar/`](../archive/joystick-handle-bar/).

## 1D-axis constrainer (wide-window revision)

38 × 38 × 56 mm stepped hollow box. The home (mouse-side) wall is open over the full 26 mm cavity width (the
6 mm side walls stay as posts) from the top of the socket (part z 10, world Z 25.41, the frame top) up to the
cavity ceiling (part z 53, world Z 68.41); the 3 mm socket ring below z 10 is closed again, and the top plate
with its 1D slot is unchanged. Generated by `joystick-1d-axis-constrainer/make_wide_window.py` from the
original part in `archive/`. On the rig it spans world Z 15.41-71.41 on the holder frame. This revision is
on the rig. The earlier 16 mm window revision (installed 1 Nov, since replaced) and the original arched version
are in [`archive/joystick-1d-axis-constrainer/`](../archive/joystick-1d-axis-constrainer/). The socket opening
in the home wall is closed in this revision, so the holder's cable must exit elsewhere.

## Ledex 195224-230 reference model

Body and plunger of the STA 20 × 40 mm pull solenoid (60° plunger, no anti-rotation flat) from the datasheet
drawing (page F34, `simulations/ledex_femm/datasheet/`), for clearance checks, figures and the rig explorer.
Generated by `ledex-holder-adjustable/make_ledex_holder.py` from `simulations/ledex_femm/ledex_geometry.py`
(`LEDEX`, `plunger_dims`). Frame: X along the axis from the body face (boss side, + toward the joystick); the
plunger is drawn seated (energised).

| | dimension (mm) | source |
| --- | --- | --- |
| case | Ø19.56 × 39.37 | drawing |
| M14 × 1.5 boss | 9.52 long | drawing |
| plunger | Ø7.82, 20.1 g | drawing |
| tip beyond body face, seated | 23.81 | drawing |
| tip slot | 2.5 ± 0.3 wide, 9.5 ± 0.3 deep | drawing |
| cross hole | Ø2.5/2.6, 4.76 ± 0.30 from the tip | drawing |
| plunger length | 59.7 (55.9 cylinder + 3.8 cone) | from the mass |
| 60° cone | half-angle 37.5°, 1 mm flat at the apex | FEMM calibration |
| mounting nut | M14 × 1.5, size not given | assumed 22 mm AF × 3.5 mm |

Mesh masses match the datasheet (plunger 20.0 g vs 20.1 g). Internals (bobbin, coil, back stop) are not
modelled; FEMM adds fitted internals and uses axisymmetric stand-ins for the slot and cross hole. Still to
confirm with calipers: slot width, cross-hole diameter and distance from the tip, seated protrusion, plunger
length and the nut size.
