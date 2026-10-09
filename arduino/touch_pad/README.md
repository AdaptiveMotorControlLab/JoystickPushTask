# Capacitive rest-pad sensor (Arduino Nano)

Replaces the FSR 402 on the rest pad. A 10×10 mm copper-tape pad is read by an Arduino Nano;
a knob (10 kΩ pot) sets the sensitivity. The Nano outputs a clean 0 V / 5 V signal into
`Dev1/ai2`: **5 V while the paw touches the pad**, 0 V otherwise. The output is low-impedance,
so joystick X no longer ghosts onto `ai2`. The LabVIEW rest-pad logic (`voltage > threshold`)
does not change; set the `rest pad threshold (V)` control to about **2.5 V**.

## Parts

| Part | Notes |
|------|-------|
| Arduino Nano A000005 (ATmega328P) | Classic Nano, Mini-USB. Not the Nano Every. |
| Arduino Nano Screw Terminal Adapter ASX00037 | Nano plugs in; all wiring goes to screw terminals. |
| Copper foil tape (Velleman 5 mm) | Two strips side by side make the 10×10 mm pad. |
| Bourns 10 kΩ linear pot (51AAD-B28-A15L) | Sensitivity knob; 6.35 mm shaft, needs a knob. |
| 1 MΩ resistor | Reuse the 1 MΩ from the FSR divider. |
| Thin shielded wire | Pad lead, as short as practical (< 30 cm). |
| Mini-USB cable | Programming and serial calibration only. |

## Wiring

| From | To | Notes |
|------|----|-------|
| D4 | 1 MΩ resistor | Send pin |
| 1 MΩ resistor | D6 | Receive pin |
| D6 | Pad lead (inner conductor) | Solder to the copper tab before sticking the tape down |
| Pad lead shield | GND (Nano end only) | Leave the shield unconnected at the pad end |
| Pot wiper (middle leg) | A0 | |
| Pot outer leg | 5V | Leg that the wiper reaches when turned fully clockwise |
| Pot other outer leg | GND | Swap the outer legs if clockwise makes it *less* sensitive |
| D2 | `ai2`, SCB-68A terminal 65 | Touch output |
| 5V | Rig +5 V, SCB-68A terminal 8 | Power from the DAQ |
| GND | AI GND, SCB-68A terminal 64 | Common ground |

Before connecting D2 to terminal 65, **remove the FSR 402 and its 1 MΩ divider** so nothing else
drives or loads `ai2`. Do not leave the USB cable connected while the Nano runs from the rig
+5 V; program and calibrate on USB first, or calibrate on USB with the 5V lead disconnected.

Cover the pad with a thin layer of ordinary tape so the paw never touches bare copper and water
cannot short it.

## Install and upload

1. Install the Arduino IDE.
2. Library Manager: install **CapacitiveSensor** (Paul Badger / Paul Stoffregen).
3. Board: **Arduino Nano**. Processor: **ATmega328P** (try "ATmega328P (Old Bootloader)" if upload fails).
4. Open `touch_pad/touch_pad.ino` and upload over Mini-USB.

## Calibration

1. Power up with the pad **untouched** (the Nano tares at power-up; the onboard LED is lit during
   tare). Re-tare any time with the reset button, a power cycle, or by sending `t` in the Serial
   Monitor.
2. Open the Serial Plotter at **115200 baud**. It shows `raw`, `baseline`, `delta`, `on_thr`,
   `off_thr` and `state` (drawn at the `on_thr` level while touched). Send `p` to pause/resume
   printing.
3. Turn the knob until a mouse-sized contact (e.g. a fingertip edge or a small damp swab) pushes
   `delta` clearly above `on_thr`, while the untouched `delta` stays well below `off_thr`. The
   onboard LED follows the output.
4. If the knob runs out of range, edit `THR_MIN` / `THR_MAX` at the top of the sketch
   (raw counts depend on pad size, lead length and `N_SAMPLES`).
5. Then check `ai2` in NI-MAX: about 0 V untouched, about 5 V touched.

Fast LED blinking with D2 held LOW means a pad fault (lead shorted to ground or disconnected).

## Bench checklist (no animal)

- [ ] Finger and mouse-sized contacts switch cleanly; release goes back to 0 V.
- [ ] Resting contact for more than 60 s stays HIGH.
- [ ] Wet pad and water drops: note whether they trigger; adjust the knob or cover tape.
- [ ] Spout extended and licking nearby do not trigger.
- [ ] Joystick sweep across its range does not move `ai2`.
- [ ] Metal tools and hands near (not on) the pad do not trigger.
- [ ] Moving the pad cable does not trigger.
- [ ] Push VI Case 0: `paw on rest pad` follows the pad with the 2.5 V threshold.

## Ephys

The sensor drives small pulses on the pad lead. During recordings: use shielded wire with the
shield grounded at the Nano end, keep the pad lead short and routed away from the headstage,
and check recordings with the sensor powered and unpowered. Unplug the Nano's 5 V if
interference remains.

## Tunables (top of `touch_pad.ino`)

| Constant | Default | Effect |
|----------|---------|--------|
| `N_SAMPLES` | 20 | Samples per reading; higher = less noise, slower |
| `THR_MIN`, `THR_MAX` | 20, 5000 | Knob range of the ON threshold (raw counts) |
| `OFF_FRACTION` | 0.7 | Release threshold as a fraction of ON (hysteresis) |
| `DEBOUNCE_ON`, `DEBOUNCE_OFF` | 3, 3 | Consecutive readings needed to switch |
| `DRIFT_ALPHA` | 0.0005 | Baseline tracking speed while released |
| `PRINT_INTERVAL_MS` | 20 | Serial output interval |
