# Forelimb Object-Push Task

> ⚠️ **Work in progress.** This repository adapts the 2-axis joystick rig from
> [Mathis et al., 2017](https://doi.org/10.1016/j.neuron.2017.02.049) into a **1D forelimb object-push task**.
> The rig runs mouse training sessions (since 16 October 2026) with the axial-resistance magnet mounted but
> kept at 0 V. Push-stage training, magnet force calibration and the perturbation sessions remain in progress.
> The living project record (status, decisions, open bugs, validation) is
> [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md).

Forked and adapted from the original [JoystickControlSystem](https://github.com/AdaptiveMotorControlLab/JoystickControlSystem)
(Mathis lab). The original rig trained head-fixed mice to *pull* a 2-axis joystick against a lateral
magnetic perturbation. This fork keeps the same LabVIEW architecture and NI-DAQ backbone but reworks the
task into a goal-directed forward *push*.

## Task overview

Each trial:

```
forepaw on rest pad (held `home TO`)  →  go cue  →  paw release starts the trial  →  reach to object
  →  push forward  →  (optional axial resistance; magnet kept at 0 V for now)  →  object in target band
  →  auditory success cue  →  short delay  →  lick spout extends  →  water reward  →  spout retracts
```

Key differences from the original task:

- **1D push** instead of 2D pull — the task-relevant axis remains in the existing coordinate structure;
  the lateral axis is physically limited by the **1D-axis constrainer**.
- **Target band** — reward requires the object to stay inside a target band for `end TO`. Overshoot is
  not an abort, but leaving the band resets the dwell. An optional velocity rule pays any cube movement
  above a threshold instead (shaping).
- **Rest-pad initiation** — a trial can only arm when the object is home (spring-loaded) **and** the
  forepaw is on the capacitive rest pad; the movement window starts when the paw is released.
  Optional session modes pay on the pad hold itself (`reward on touch`) or ignore the pad entirely
  (`joystick only`).
- **Axial-resistance perturbation** (opposing the push) instead of a lateral kick. The mesoscope
  rig uses the original Mathis solenoid (McMaster `69905K25`). The training rig uses a Ledex
  `195224-230` driven by a Hydraulik-Kompetenz PVA 1.6 (0–10 V command on `Dev1/ao0` /
  `MagnetPush_Dev1`), with the plunger linked to the joystick shaft. It is electrically commissioned
  and mounted; force calibration and the LabVIEW magnet safety work are still to do, so every
  parameter file keeps `mag = 0`.
- **Delayed, retractable reward** with an immediate auditory success cue, separating push execution from
  licking/reward for cleaner neural alignment.
- **Planned session blocks** (via parameter files): Baseline → Random perturbation → Fixed perturbation → Washout.

## Current status

Validated on the bench or in sessions (details and dates in the project plan):

- Rest-pad gate → trial → success cue → adjustable delay → spout extension → water → consumption wait →
  spout retraction. Safe startup (water/cue LOW, spout retract, magnet 0 V) and one canonical Stop that
  ends every parallel loop. LabVIEW's toolbar Abort remains emergency-only because it skips cleanup.
- Capacitive rest pad (Arduino Nano, mains-filtered sketch) on `ai2`, confirmed in mouse sessions.
- EVENTS logger (`EVENTS_<name>`: trial, state, reward, water-loop, magnet and heartbeat events with
  sample index and Unix time) and the automatic `TIMESTAMPS_LABVIEW_<name>.npy` file for video sync,
  written at Stop.
- Trial start at paw release (Case 5), go cue at the end of the pad hold (second buzzer on P0.2),
  velocity reward mode (column 28) and reward-on-touch mode (column 29).
- `deliverWater_RIG1_cue.vi` for manual habituation rewards (50 ms cue, then water; no joystick
  requirement, does not move the spout).

Built but not yet bench-tested: the joystick-only session mode (column 30). Open bugs (unpaid
successes, occasional acquisition stalls, a missed magnet-loop occurrence) are tracked in the project plan.

Mechanics: printed 89 mm joystick shaft with a narrow rounded-cube handle, 1D-axis constrainer, adjustable
Ledex holder and plunger link, all on the rig. CAD and print status in
[`mechanical/README.md`](mechanical/README.md); superseded parts in [`archive/`](archive/).

## Hardware

Existing rig hardware:

- NI-DAQ card, **PCIe-6321** (`Dev1` on the live rig), SCB-68A breakout
- Joystick base/readout: APEM TS-1D1S00A-1294 Hall thumbstick (Digi-Key 679-2501-ND)
- 3D-printed joystick shaft, cube handle and **1D-axis constrainer** ([mechanical](mechanical/README.md))

New components for the push task:

| Role                   | Component                                                                      | DAQ channel          |
| ---------------------- | ------------------------------------------------------------------------------ | -------------------- |
| Rest-pad paw sensor    | **Capacitive touch pad** (Arduino Nano, 10×10 mm copper tape, 0 V / 5 V output)| `Dev1/ai2`           |
| Retractable lick spout | **Actuonix L12-30-50-12-I** linear actuator (0–5 V position mode, 12 V supply) | `Dev1/ao1`           |
| Auditory success cue   | **Adafruit 5 V active buzzer** (#1536)                                         | `Dev1/port0/line1`   |
| Go cue                 | second Adafruit #1536 buzzer, 1 kΩ in series, burst-modulated from LabVIEW     | `Dev1/port0/line2`   |
| Axial resistance       | Ledex **`195224-230`** via Hydraulik-Kompetenz **PVA 1.6** (0–10 V), plunger linked to the shaft | `Dev1/ao0` (command only) |
| Water valve            | existing solenoid                                                              | `Dev1/port0/line0`   |

> The live NI-MAX configuration, SCB-68A wiring and bench-test history are documented in
> [`RIG_INVENTORY.md`](RIG_INVENTORY.md); the magnet wiring and commissioning steps in
> [`MAGNET_COMMISSIONING.md`](MAGNET_COMMISSIONING.md).

> The PCIe-6321 has two AO channels. AO0 is the magnet command (never coil power) and AO1 drives the
> lick-spout actuator, so both cues use digital lines.

## Software

The main VI is `Push Behaviour_MCHALABI.vi`. Its required local dependencies are
`avg joystick and frame trig lick3.vi` (acquisition), `frame counter.vi`, `PushTask Globals.vi` (shared
`stop all` and `sample count`) and `Log Event.vi` (EVENTS logger). `deliverWater_RIG1_cue.vi` is the
stand-alone habituation reward VI.

The program keeps the original occurrence-driven state machine and trajectory logging, and adds the
rest-pad gate, the paw-release state (Case 5), the go-cue loop, the EVENTS writer loop, the digital
success cue, the retractable-spout reward sequence and a shared normal-stop signal for all asynchronous
loops. It requires LabVIEW and NI-DAQmx. Saved NI-MAX tasks are machine-local and must be imported or
configured on each rig; the 20 August 2026 NI-DAQmx backup is
[`ni-max/JoystickPushTask_NIMAX_2026-08-20.nce`](ni-max/JoystickPushTask_NIMAX_2026-08-20.nce)
(it predates the go-cue task `GoCue_Dev1`).

At Stop the VI runs [`scripts/run_timing.bat`](scripts/run_timing.bat), which calls
[`scripts/make_labview_timing.py`](scripts/make_labview_timing.py) (numpy only; the rig PC's Python 3.6.4
must not be upgraded). The EVENTS format is specified in [`EVENTS_LOGGER_PLAN.md`](EVENTS_LOGGER_PLAN.md).
The rest-pad Arduino sketch is in [`arduino/touch_pad/`](arduino/touch_pad/README.md).

## Experimental settings file

The experimental parameters are loaded from a tab-separated text file, one line per trial. The base
format has **27 columns** (boxes, timings, water, cue and spout settings). Three optional columns
switch on newer modes: 28 `vel threshold` (velocity reward), 29 `reward on touch`, 30 `joystick only`.
Shorter files load the missing columns as 0, so older files behave as before. Column map, the
X/Y naming trap and every file's purpose: [`parameters/README.md`](parameters/README.md).
Push = Y / `ai1`; lateral = X / `ai0`, but push values go in the loader's **X** columns.

Training files live in [`parameters/training/`](parameters/training/); bench presets
(`push_bench_*.txt`) sit in [`parameters/`](parameters/). Habituation and perturbation blocks are not
yet file-only stages.

## Calibration

Water-valve pulse length was measured on the training rig on 8 September 2026.
Use **130 / 185 / 240 ms** for **4 / 6 / 8 µl** (100 ms measured 3.2 µl). Full table, fit and figures:
[`calibration/water-volume.md`](calibration/water-volume.md).

Joystick map: **push = Y = `Dev1/ai1`** (white), **lateral = X = `Dev1/ai0`** (red); forward push
lowers the voltage. Measured 3 November 2026 on the current mount: **0.0295 V/mm** over 0–8 mm
(10 mV ≈ 0.34 mm), home ~2.47 V. Rest drifts between sessions (2.44–2.48 V seen), so re-centre home
boxes on the measured rest before each session. See
[`calibration/joystick-volts-mm.md`](calibration/joystick-volts-mm.md) and
[`calibration/README.md`](calibration/README.md) (also magnet coil current vs AO0).

## Repository layout

| Path | Contents |
| --- | --- |
| `*.vi` (root) | Canonical LabVIEW hierarchy (edit only in LabVIEW on the rig PC; never Git-merge `.vi` files) |
| `parameters/` | Parameter files and their README |
| `scripts/` | Timing-file script run at Stop |
| `calibration/` | Water, joystick and magnet calibrations |
| `arduino/touch_pad/` | Capacitive rest-pad sketch and wiring |
| `mechanical/` | Current CAD (STEP + STL) and generator scripts |
| `simulations/ledex_femm/` | Ledex force models, rig geometry and the rig explorer |
| `archive/` | Superseded CAD, the FSR rest-pad history and retired scripts |
| `ni-max/` | NI-DAQmx configuration backup |
| `docs/PROJECT_PLAN.md` | Project state, decisions, known bugs and validation status |

## Citation

Please cite the original work this task is built on:

- [Mathis et al., 2017](https://doi.org/10.1016/j.neuron.2017.02.049) — *Somatosensory Cortex Plays an
  Essential Role in Forelimb Motor Adaptation in Mice.*

We greatly thank Dr. Ed Soucy at the Harvard CBS Center for Neuroengineering for the original LabVIEW code
and expert advice throughout the development of this joystick system.
