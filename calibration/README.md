# Calibration

Hardware calibrations for the training-rig push task. Each page is one measurement,
dated, with the raw numbers and the value to use in LabVIEW.

| Calibration | Status | Date |
| --- | --- | --- |
| [Water volume vs valve pulse](water-volume.md) | Done — use 130 / 185 / 240 ms for 4 / 6 / 8 µl | 8 Sep 2026 |
| [Joystick home + volts → mm](joystick-volts-mm.md) | Push = Y / `ai1` / white; lateral = X / `ai0` / red. Rest 2.50 / 2.525 V; ~0.030 V/mm eyeball | 8 Sep 2026 |
| FSR threshold / hysteresis | Not yet (taped replacement working) | — |
| Spout extend voltage vs mouse | Not yet | — |
| Magnet coil current vs AO0 | Done (PVA 1.6, Imin and Imax at minimum, plunger seated): 0 V ≤ 0.006 A, 0.5 V 0.053, 1 V 0.074, 2 V 0.106, 3 V 0.121, 4 V 0.147, 5 V 0.180, 6 V 0.201, 8 V 0.273, 10 V 0.310 A | 11 Oct 2026 |
| Magnet force on the steel target vs AO0 | Not yet measured (needs the printed holder and a gap jig). FEMM model estimate in [`simulations/ledex_femm`](../simulations/ledex_femm/README.md): ~1.4 g at 2 mm and 10 V for five M3 washers | — |
