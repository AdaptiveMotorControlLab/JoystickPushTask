# Capacitive rest-pad sensor (Arduino Nano)

The rest-pad touch sensor. A 10×10 mm copper-tape pad is read by an Arduino Nano;
a knob (10 kΩ pot) sets the sensitivity. The Nano outputs a clean 0 V / 5 V signal into
`Dev1/ai2`: **5 V while the paw touches the pad**, 0 V otherwise. The output is low-impedance,
so joystick X does not ghost onto `ai2`. The LabVIEW rest-pad logic is `voltage > threshold`;
set the `rest pad threshold (V)` control to about **2.5 V**.

## Parts

| Part | Notes |
|------|-------|
| Arduino Nano A000005 (ATmega328P) | Classic Nano, Mini-USB. Not the Nano Every. |
| Arduino Nano Screw Terminal Adapter ASX00037 | Nano plugs in; all wiring goes to screw terminals. |
| Copper foil tape (Velleman 5 mm) | Two strips side by side make the 10×10 mm pad. |
| Bourns 10 kΩ linear pot (51AAD-B28-A15L) | Sensitivity knob; 6.35 mm shaft, needs a knob. |
| 1 MΩ resistor | Send resistor between D4 and D6. |
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

Nothing else may drive or load `ai2` (terminal 65). Do not leave the USB cable connected while the Nano runs from the rig
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
2. Open the Serial Plotter at **115200 baud**. It shows `raw` (mean over the last 20 ms),
   `baseline`, `delta`, `ripple` (max − min of the readings in that 20 ms), `on_thr`, `off_thr`
   and `state` (drawn at the `on_thr` level while touched). Send `p` to pause/resume printing.
3. Turn the knob until a mouse-sized contact (e.g. a fingertip edge or a small damp swab) pushes
   `delta` clearly above `on_thr`, while the untouched `delta` stays well below `off_thr`. The
   onboard LED follows the output. Set `on_thr` near the middle between the untouched and the
   touched `delta`, not just under the touched level.

### Mains hum (50 Hz)

A mouse on the pad is an antenna for mains hum: the readings swing at 50 Hz, and `ripple` can be
as large as the touch signal itself. The first mouse session (16 Oct 2026) with the old sketch
showed `ai2` toggling every ~20 ms (high ~13 ms, low ~8 ms) whenever the threshold sat near the
paw signal, so a 100 ms `home TO` hold almost never completed. The sketch now averages over
exactly one mains period (cancels the hum), uses wider hysteresis (`OFF_FRACTION` 0.5) and needs
`delta` below `off_thr` for 40 ms before releasing. Output timing: touch-on ~30–50 ms after
contact, release ~50–60 ms after lift-off.

Grounding the mouse removes most of the hum at its source: with the Fluke on Ω check whether the
metal head-fixation clamp is connected to AI GND (SCB-68A terminal 64). If not, run one wire from
the clamp to terminal 64 (single point, no other ground paths) and compare `ripple` during a
light touch with and without it. Re-check the knob afterwards (the touch signal gets larger).
4. If the knob runs out of range, edit `THR_MIN` / `THR_MAX` at the top of the sketch
   (raw counts depend on pad size, lead length and `N_SAMPLES`).
5. Then check `ai2` in NI-MAX: about 0 V untouched, about 5 V touched.

Fast LED blinking with D2 held LOW means a pad fault (lead shorted to ground or disconnected).

## Bench checklist (no animal)

- [ ] Finger and mouse-sized contacts switch cleanly; release goes back to 0 V.
- [ ] Very light contact near threshold: `state` stays steady (no 50 Hz flicker) even while `raw` shows ripple.
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
| `DECISION_US` | 10000 | Half a mains period; readings are averaged over two of these (20 ms). Use 8333 on 60 Hz mains |
| `OFF_FRACTION` | 0.5 | Release threshold as a fraction of ON (hysteresis) |
| `TOUCH_HOLD_MS`, `RELEASE_HOLD_MS` | 20, 40 | Time above ON / below OFF needed to switch |
| `DRIFT_ALPHA`, `DROP_ALPHA` | 0.0025, 0.22 | Baseline tracking per 10 ms step while released (~4 s drift, ~40 ms drop) |
| `PRINT_INTERVAL_MS` | 20 | Serial output interval |
