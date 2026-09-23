# 3D-printed parts

Current models are provided as editable STEP sources and slicer-ready STL exports:

- [Joystick shaft](joystick/README.md) — 89 mm shaft that the interchangeable handles mount onto
- [Joystick bar handle](joystick-handle-bar/README.md) — 38 mm bar that attaches at the shaft tip
- [Joystick rounded-cube handle](joystick-handle-cube/README.md) — rounded box with three offset holes
- [Joystick 1D-axis constrainer](joystick-1d-axis-constrainer/README.md) — constrains the joystick to one movement axis
- [Ledex holder](ledex-holder/README.md) — holder for the Ledex `195224-230` axial-resistance solenoid

Keep one subfolder per part (or per design iteration), for example:

```
3d-print/
  lateral-delimiter/
  fsr-rest-pad-mount/
  lick-spout-carriage/
```

Supported formats: STL, 3MF, STEP, or native CAD project files. Include a one-line note in the
part README or filename if print orientation, infill, or material matters for the rig.
