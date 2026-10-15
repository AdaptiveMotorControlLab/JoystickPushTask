# Joystick component (thumbstick base, measured model)

Measured model of the Hall thumbstick base (APEM TS-1D1S00A-1294, castle cap removed) that the
[89 mm shaft](../joystick/README.md) screws onto. It is not printed; it is used to place the shaft, the
[holder](../joystick-holder/README.md) and the Ledex correctly in the models
(`simulations/ledex_femm/rig_geometry.py`).

- STEP source: [`joystick_component.step`](joystick_component.step)
- STL export: [`joystick_component.stl`](joystick_component.stl)
- Round body 25.3 mm diameter, 11.53 mm tall; round flange 29.75 mm diameter (z 11.53-13.09);
  stepped dome (21.2 / 12.9 / 7.1 mm diameter) up to z 18.28; stem 4.84 mm to z 23.45; a 9.6 × 2.1 mm
  cross-bar at z 23.87-26.27; 4.3 mm stub to the top at z 29.3.
- The shaft's 5 mm × 2.7 mm bottom bore holds a small screw with its head glued in; the screw goes into
  the stub and the shaft's cone sits directly on the stub top, so the shaft base is 29.3 mm above the
  bottom of the body.
- The pivot is inside the body and is not modelled; the models take it at mid-body (z 5.8) and test
  z 2-10.
