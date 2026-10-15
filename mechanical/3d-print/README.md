# 3D-printed parts

Current models are provided as editable STEP sources and slicer-ready STL exports:

- [Joystick shaft](joystick/README.md) — 89 mm shaft that the interchangeable handles mount onto
- [Joystick bar handle](joystick-handle-bar/README.md) — 38 mm bar that attaches at the shaft tip
- [Joystick rounded-cube handle](joystick-handle-cube/README.md) — rounded box with three offset holes
- [Joystick 1D-axis constrainer](joystick-1d-axis-constrainer/README.md) — constrains the joystick to one movement axis
- [Joystick component](joystick-component/README.md) — measured model of the APEM TS Hall base
- [Joystick component holder](joystick-holder/README.md) — breadboard holder for the component; the constrainer sits on it
- [Adjustable Ledex holder](ledex-holder-adjustable/README.md) — slotted base, upright and carriage (distance, lateral, height), gauges and plunger-link parts
- [Ledex holder (fixed 30 mm axis)](ledex-holder/README.md) — superseded

Keep one subfolder per part (or per design iteration), for example:

```
3d-print/
  lateral-delimiter/
  fsr-rest-pad-mount/
  lick-spout-carriage/
```

Supported formats: STL, 3MF, STEP, or native CAD project files. Include a one-line note in the
part README or filename if print orientation, infill, or material matters for the rig.
