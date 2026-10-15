# Joystick 1D-axis constrainer

STEP model for the 38 × 38 × 56 mm stepped hollow box that mechanically constrains the joystick
to one movement axis.

- STEP source: [`joystick_1d_axis_constrainer_38x38x56.step`](joystick_1d_axis_constrainer_38x38x56.step)
- STL export: [`joystick_1d_axis_constrainer_38x38x56.stl`](joystick_1d_axis_constrainer_38x38x56.stl)
- Fabrication and fit on the current rig have not yet been documented here.

## Window revision for the Ledex plunger link (print this one)

`joystick_1d_axis_constrainer_38x38x56_ledex_window.step/.stl`, made from the original by
[`make_ledex_window.py`](make_ledex_window.py). The round-topped arch in the home (mouse-side) wall,
16 mm wide with its top at 48 mm above the part's bottom, is cut square up to the cavity ceiling
(53 mm); the width, the top plate and its 1D slot are unchanged (646 mm³ removed).

On the rig this is world Z 55.4-68.4. With the plunger link at its recommended height (Ledex axis
Z 58.5) the plunger now passes 4.1 mm from the window instead of 1 mm under the arch, and the 10 mm
link pin's ends stay 3 mm from the sides. The link height can now go up to 23 mm above the shaft base
(was 18).

Rerun with the NGSolve venv (`/tmp/ngenv/bin/python make_ledex_window.py`) after changing the
original or the window size in `simulations/ledex_femm/rig_geometry.py`.
