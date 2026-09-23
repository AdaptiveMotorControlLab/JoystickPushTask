# Mechanical designs

CAD and fabrication files for the forelimb push-task rig: 3D-printed parts and
related build notes.

## Layout

| Folder | Use for |
| ------ | ------- |
| [3D-printed parts](3d-print/README.md) | 3D-printable meshes and project files (STL, 3MF, STEP, Fusion, etc.) |

Add new parts in a named subfolder (e.g. `3d-print/fsr-mount/`) so
revisions stay grouped. Prefer descriptive filenames with dimensions or revision when useful.

## Push object

CAD added 05 Sep 2026: an 89 mm joystick shaft plus two interchangeable tip-mounted handles.

- [Joystick shaft](3d-print/joystick/README.md)
- [Bar handle](3d-print/joystick-handle-bar/README.md) — 38 mm bar
- [Rounded-cube handle](3d-print/joystick-handle-cube/README.md) — current push-object candidate.
  Three holes set how close the front face sits to the mouse and rest pad, and they also shift
  weight relative to the joystick beneath the object.

The cube is meant to sit below the mouse in the natural forelimb workspace and present a
push-biased surface that discourages grasping like the original pull handles.

## 3D models

- [Joystick shaft](3d-print/joystick/README.md) — 89 mm STEP source and STL export
- [Joystick bar handle](3d-print/joystick-handle-bar/README.md) — 38 mm STEP source and STL export
- [Joystick rounded-cube handle](3d-print/joystick-handle-cube/README.md) — rounded-box STEP source and STL export
- [Joystick 1D-axis constrainer](3d-print/joystick-1d-axis-constrainer/README.md) — 38 × 38 × 41 mm STEP source and STL export
- [Ledex holder](3d-print/ledex-holder/README.md) — holder for the Ledex `195224-230`, 30 mm axis STEP source and STL export

One printed joystick, handle and 1D-axis constrainer are fitted for bench testing. Further
prints wait until 21 September 2026. Still to integrate: spring return to home, the
steel-ring / washer target, and final volts→mm calibration after the below-mouse geometry
is frozen.
