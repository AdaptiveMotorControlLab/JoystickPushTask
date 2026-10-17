# Mechanical designs

CAD and fabrication files for the forelimb push-task rig: 3D-printed parts and
related build notes.

## Layout

| Folder | Use for |
| ------ | ------- |
| [3D-printed parts](3d-print/README.md) | 3D-printable meshes and project files (STL, 3MF, STEP, Fusion, etc.) |

Add new parts in a named subfolder (e.g. `3d-print/rest-pad-mount/`) so
revisions stay grouped. Prefer descriptive filenames with dimensions or revision when useful.

## Push object

CAD added 05 Sep 2026: an 89 mm joystick shaft plus two interchangeable tip-mounted handles.

- [Joystick shaft](3d-print/joystick/README.md)
- [Bar handle](3d-print/joystick-handle-bar/README.md) — 38 mm bar
- [Rounded-cube handle](3d-print/joystick-handle-cube/README.md) — current push object (20 mm wide;
  a narrow 11.5 × 11.5 × 10 mm version is also available). Three holes set how close the front face sits
  to the mouse and rest pad; the shaft goes in the front hole.

The cube is meant to sit below the mouse in the natural forelimb workspace and present a
push-biased surface that discourages grasping like the original pull handles.

## 3D models

- [Joystick shaft](3d-print/joystick/README.md) — 89 mm STEP source and STL export
- [Joystick bar handle](3d-print/joystick-handle-bar/README.md) — 38 mm STEP source and STL export
- [Joystick rounded-cube handle](3d-print/joystick-handle-cube/README.md) — STEP and STL for the 20 mm and the narrow 11.5 mm cube
- [Joystick 1D-axis constrainer](3d-print/joystick-1d-axis-constrainer/README.md) — 38 × 38 × 56 mm STEP source and STL export
- [Adjustable Ledex holder](3d-print/ledex-holder-adjustable/README.md) — slotted base, upright and carriage, gauges and plunger-link parts

One printed joystick, handle and 1D-axis constrainer are fitted for bench testing. Further
prints wait until 21 September 2026. Still to integrate: spring return to home, the
steel-ring / washer target, and final volts→mm calibration after the below-mouse geometry
is frozen.
