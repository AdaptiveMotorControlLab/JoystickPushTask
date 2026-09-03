# Mechanical designs

CAD and fabrication files for the forelimb push-task rig: laser-cut flat parts,
3D-printed brackets and mounts, and related build notes.

## Layout

| Folder | Use for |
| ------ | ------- |
| [Laser-cut push object](laser-cut/push-object/README.md) | 2D vector cut files (SVG, DXF) for laser or CNC flat stock |
| [3D-printed parts](3d-print/README.md) | 3D-printable meshes and project files (STL, 3MF, STEP, Fusion, etc.) |

Add new parts in a named subfolder (e.g. `laser-cut/push-object/`, `3d-print/fsr-mount/`) so
revisions stay grouped. Prefer descriptive filenames with dimensions or revision when useful.

## Push object — contact plate (prototype, 03 Sep 2026)

First prototype contact surface for the modified joystick handle:

- **Process:** laser cut
- **Material:** 3 mm transparent sheet (plexiglass / acrylic)
- **Footprint:** 36 × 36 mm square
- **Profile:** rounded corners on the paw-contact (top) edge; square corners on the handle
  (base) edge that is glued to the existing manipulandum handle
- **Source file:** [`laser_cut_36mm_square_left_rounded.svg`](laser-cut/push-object/laser_cut_36mm_square_left_rounded.svg)

## 3D models

- [Joystick 1D-axis constrainer](3d-print/joystick-1d-axis-constrainer/README.md) — 38 × 38 × 41 mm STEP model
- [Ledex holder](3d-print/ledex-holder/README.md) — holder for the Ledex `195224-230`, 30 mm axis STEP model

Still to integrate on the rig: spring return to home, steel-ring / washer target for the axial
solenoid, and final glue-up + volts→mm calibration after geometry is frozen.
