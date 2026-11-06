# Calibration

Hardware calibrations for the training-rig push task. Each page is one measurement,
dated, with the raw numbers and the value to use in LabVIEW.

| Calibration | Status | Date |
| --- | --- | --- |
| [Water volume vs valve pulse](water-volume.md) | Done — use 130 / 185 / 240 ms for 4 / 6 / 8 µl | 8 Sep 2026 |
| [Joystick home + volts → mm](joystick-volts-mm.md) | Push = Y / `ai1` / white; lateral = X / `ai0` / red. Push: 0.0295 V/mm (33.9 mm/V, 0–8 mm, R² 0.995), home ~2.47 V | 3 Nov 2026 (eyeball 8 Sep) |
| Rest-pad threshold | Done: 2.5 V on `ai2` (capacitive pad, 0 V / 5 V; sensitivity set by the knob) | 14 Oct 2026 |
| Spout extend voltage vs mouse | Not yet | — |
| Magnet coil current vs AO0 | Done (PVA 1.6, Imin and Imax at minimum, plunger seated): 0 V ≤ 0.006 A, 0.5 V 0.053, 1 V 0.074, 2 V 0.106, 3 V 0.121, 4 V 0.147, 5 V 0.180, 6 V 0.201, 8 V 0.273, 10 V 0.310 A | 11 Oct 2026 |
| Magnet force at the cube vs AO0 (plunger linked to the shaft) | Not yet measured. Holder and link mounted 1 Nov 2026; measure with a gram scale at the cube (0 / 5 / 10 / 15 mm push, Ledex off for the spring curve, then 5 V and 10 V). Model estimate in [`simulations/ledex_femm`](../simulations/ledex_femm/README.md) ("Plunger link"): home → 15 mm push 2.3 → 0.6 gf at 1 V, 13 → 4 gf at 5 V, 40 → 11 gf at 10 V | — |
| Go-cue burst length | Not yet measured (nominal 1 ms on / 1 ms off × 50 = 100 ms; Windows wait overhead may stretch it) | — |
