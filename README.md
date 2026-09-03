# Forelimb Object-Push Task

> ⚠️ **Work in progress.** This repository adapts the 2-axis joystick rig from
> [Mathis et al., 2017](https://doi.org/10.1016/j.neuron.2017.02.049) into a **1D forelimb object-push task**.
> The working rig VIs have been imported, and the rest-pad-to-reward success path is bench-tested.
> The first push-object contact plate and supporting mechanical CAD have been added. Final assembly,
> animal-specific calibration, training presets and safety/edge-case validation remain in progress.

Forked and adapted from the original [JoystickControlSystem](https://github.com/AdaptiveMotorControlLab/JoystickControlSystem)
(Mathis lab). The original rig trained head-fixed mice to *pull* a 2-axis joystick against a lateral
magnetic perturbation. This fork keeps the same LabVIEW architecture and NI-DAQ backbone but reworks the
task into a goal-directed forward *push*.

## Task overview

Each trial:

```
forepaw on rest pad  →  trial starts  →  reach to object  →  push forward
  →  (optional axial resistance; hardware not yet active)  →  object held in target band
  →  auditory success cue  →  short delay  →  lick spout extends  →  water reward  →  spout retracts
```

Key differences from the original task:

- **1D push** instead of 2D pull — the task-relevant axis remains in the existing coordinate structure;
  the lateral axis is physically limited by the existing **1D-axis constrainer**.
- **Bounded target zone** — reward requires the object to *end and remain* within a target distance band (overshoot fails).
- **Rest-pad initiation** — a trial can only start when the object is home (spring-loaded) **and** the
  forepaw is on the rest pad, giving a clean pre-contact trial-start state.
- **Axial-resistance perturbation** (opposing the push) instead of a lateral kick. The mesoscope
  rig uses the original Mathis solenoid (McMaster `69905K25`). The training-rig copy is Ledex
  `195224-230`, received 02/09/26 but not yet installed; `Dev1/ao0` / `MagnetPush_Dev1` is reserved for it.
- **Delayed, retractable reward** with an immediate auditory success cue, separating push execution from
  licking/reward for cleaner neural alignment.
- **Planned session blocks** (via parameter files): Baseline → Random perturbation → Fixed perturbation → Washout.

## Current status

- Canonical VIs imported from the behavioural rig and pushed on 18 August 2026.
- Bench-validated path: object home + FSR paw gate → trial → success cue → adjustable delay → spout
  extension → water → consumption wait → spout retraction.
- The acquisition helper reads joystick X/Y, lick/frame signals and the new rest-pad channel.
- A fresh GitHub copy now opens and completes the full bench sequence on the rig PC using the
  compatible repository helper VIs.
- Safe startup now commands water/cue LOW, spout retract and magnet 0 V. One canonical Stop cleanly
  ends every parallel loop; idle, reward-delay and spout-extended Stop tests passed.
- Remaining validation includes repeated-cycle testing and explicit fail/timeout checks. LabVIEW's
  toolbar Abort remains emergency-only because it bypasses normal cleanup.
- A 36 × 36 mm laser-cut contact-plate prototype and STEP models for the joystick 1D-axis
  constrainer and Ledex holder are documented in [`mechanical/README.md`](mechanical/README.md).
- Remaining build work includes gluing and rig-fitting the contact plate, adding spring return and
  a steel-ring target, completing the animal-safe rest-pad cover, installing/calibrating the Ledex magnet,
  mouse-specific calibration and training-stage controls/presets.



## Hardware

Existing rig hardware:

- NI-DAQ card, **PCIe-6321** (`Dev1` on the live rig)
- Joystick base/readout (Digi-Key 679-2501-ND)
- 3D-printed **1D-axis constrainer** ([STEP model](mechanical/3d-print/joystick-1d-axis-constrainer/README.md))

Mechanical adaptation in progress:

- The first larger contact surface has been laser-cut from a 3 mm transparent sheet using the
  repository SVG. It is 36 × 36 mm with rounded paw-contact corners and a square glue edge.
- Final glue-up and rig fit, spring return to home, and the steel-ring / washer target for the axial
  solenoid remain.

New components for the push task:


| Role                   | Component                                                                      | DAQ channel          |
| ---------------------- | ------------------------------------------------------------------------------ | -------------------- |
| Rest-pad paw sensor    | Interlink **FSR 402** (solder tabs, 30-81794) + 10 kΩ divider                  | `Dev1/ai2`           |
| Retractable lick spout | **Actuonix L12-30-50-12-I** linear actuator (0–5 V position mode, 12 V supply) | `Dev1/ao1`           |
| Auditory success cue   | **Adafruit 5 V active buzzer** (#1536)                                         | `Dev1/port0/line1`   |
| Axial resistance       | Ledex **`195224-230`** tubular solenoid (received 02/09/26; not installed) | reserved `Dev1/ao0`  |
| Water valve            | existing solenoid                                                              | `Dev1/port0/line0`   |


> The validated live NI-MAX configuration, SCB-68A wiring and bench-test history are documented in
> [`RIG_INVENTORY.md`](RIG_INVENTORY.md).

> The PCIe-6321 has two AO channels. The working design reserves AO0 for axial resistance and uses
> AO1 for the lick-spout actuator; the auditory cue therefore uses a digital line.



## Software

The main VI is `Push Behaviour_MCHALABI.vi`. Its required local dependencies are
`avg joystick and frame trig lick3.vi`, `frame counter.vi` and `PushTask Globals.vi`.

The program retains the original occurrence-driven five-state architecture and trajectory logging while
adding the FSR gate, digital success cue, retractable-spout reward sequence and shared normal-stop
signal for all asynchronous loops. It requires LabVIEW and NI-DAQmx. Saved NI-MAX tasks are
machine-local and must be imported or configured on each rig. The validated task/channel map is
documented in [`RIG_INVENTORY.md`](RIG_INVENTORY.md), with the 20 August 2026 NI-DAQmx backup stored at
[`ni-max/JoystickPushTask_NIMAX_2026-08-20.nce`](ni-max/JoystickPushTask_NIMAX_2026-08-20.nce).

## Experimental settings file

The original experimental parameters are loaded from a text file, one line per trial. They define the
home/start/end regions, hold times, water-valve open time and perturbation command/timing.

The imported VI currently exposes bench controls for the FSR threshold, cue duration, reward delay,
spout extend/retract voltages, spout settling and consumption time. These new settings have **not yet**
been added to the per-trial parameter-file loader or logged session metadata. Training-stage presets and
Baseline → Random → Fixed → Washout files also remain to be created.

## Calibration

Each rig must be calibrated for volts→mm on the push axis (the original demo assumes a 2.55 V rest with
0.05 V ≈ 1 mm — remeasure for your build). Test all channels in NI-MAX before running.

## Citation

Please cite the original work this task is built on:

- [Mathis et al., 2017](https://doi.org/10.1016/j.neuron.2017.02.049) — *Somatosensory Cortex Plays an
  Essential Role in Forelimb Motor Adaptation in Mice.*

We greatly thank Dr. Ed Soucy at the Harvard CBS Center for Neuroengineering for the original LabVIEW code
and expert advice throughout the development of this joystick system.