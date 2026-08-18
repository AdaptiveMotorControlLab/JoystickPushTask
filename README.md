# Forelimb Object-Push Task

> ⚠️ **Work in progress.** This repository adapts the 2-axis joystick rig from
> [Mathis et al., 2017](https://doi.org/10.1016/j.neuron.2017.02.049) into a **1D forelimb object-push task**.
> New hardware is installed and the core LabVIEW success path is bench-tested. The working rig VI
> still needs to be imported into this repository — expect breaking changes.

Forked and adapted from the original [JoystickControlSystem](https://github.com/AdaptiveMotorControlLab/JoystickControlSystem)
(Mathis lab). The original rig trained head-fixed mice to *pull* a 2-axis joystick against a lateral
magnetic perturbation. This fork keeps the same LabVIEW architecture and NI-DAQ backbone but reworks the
task into a goal-directed forward *push*.

## Task overview

Each trial:

```
forepaw on rest pad  →  trial starts  →  reach to object  →  push forward
  →  (axial resistance perturbation)  →  object held in target band
  →  auditory success cue  →  short delay  →  lick spout extends  →  water reward  →  spout retracts
```

Key differences from the original task:

- **1D push** instead of 2D pull — the task-relevant axis is set in the parameter file; the lateral axis
  is physically constrained by a 3D-printed delimiter.
- **Bounded target zone** — reward requires the object to *end and remain* within a target distance band (overshoot fails).
- **Rest-pad initiation** — a trial can only start when the object is home (spring-loaded) **and** the
  forepaw is on the rest pad, giving a clean pre-contact trial-start state.
- **Axial resistance** perturbation (opposing the push) instead of a lateral kick.
- **Delayed, retractable reward** with an immediate auditory success cue, separating push execution from
  licking/reward for cleaner neural alignment.
- **Session blocks** (via parameter files): Baseline → Random perturbation → Fixed perturbation → Washout.



## Hardware

Inherited from the original rig:

- NI-DAQ card, **PCIe-6321** (`Dev1` on the live rig)
- LabVIEW 2013 or newer
- Joystick base (Digi-Key 679-2501-ND), modified into a spring-loaded **push object** with a larger
  contact surface, placed close to the rest pad
- 3D-printed lateral delimiter (constrains the task to 1D)

New components for the push task:


| Role                   | Component                                                                      | DAQ channel          |
| ---------------------- | ------------------------------------------------------------------------------ | -------------------- |
| Rest-pad paw sensor    | Interlink **FSR 402** (solder tabs, 30-81794) + 10 kΩ divider                  | `Dev1/ai2`           |
| Retractable lick spout | **Actuonix L12-30-50-12-I** linear actuator (0–5 V position mode, 12 V supply) | `Dev1/ao1`           |
| Auditory success cue   | **Adafruit 5 V active buzzer** (#1536)                                         | `Dev1/port0/line1`   |
| Axial resistance       | future axial magnet/coil; not installed on the training rig                    | reserved `Dev1/ao0`  |
| Water valve            | existing solenoid                                                              | `Dev1/port0/line0`   |


> The validated live NI-MAX configuration, SCB-68A wiring and bench-test history are documented in
> [`RIG_INVENTORY.md`](RIG_INVENTORY.md).

> The PCIe-6321 has two AO channels. The working design reserves AO0 for axial resistance and uses
> AO1 for the lick-spout actuator; the auditory cue therefore uses a digital line.



## Software

The main VI is `Push Behaviour_MCHALABI.vi`. The helper VIs (`avg joystick and frame trig lick3.vi`,
`frame counter.vi`) grab frames from an external source (e.g. 2-photon) and must be present for the code
to run. Outputs include reward TTLs, a trial-start TTL, and the full trajectory (push axis + lick signal +
frame count). NI-DAQ tasks must be configured in NI-MAX (see the `media/` folder for the original task setup).

## Experimental settings file

Experimental parameters are loaded from a text file, one line per trial. It defines the home/start/end
positions (target band), hold and delay times, water valve open time, reward delay, spout timing, and
perturbation magnitude/timing. New push-task fields (reward delay, spout position/settle, cue duration)
are being added as the code is adapted.

## Calibration

Each rig must be calibrated for volts→mm on the push axis (the original demo assumes a 2.55 V rest with
0.05 V ≈ 1 mm — remeasure for your build). Test all channels in NI-MAX before running.

## Citation

Please cite the original work this task is built on:

- [Mathis et al., 2017](https://doi.org/10.1016/j.neuron.2017.02.049) — *Somatosensory Cortex Plays an
  Essential Role in Forelimb Motor Adaptation in Mice.*

We greatly thank Dr. Ed Soucy at the Harvard CBS Center for Neuroengineering for the original LabVIEW code
and expert advice throughout the development of this joystick system.