# Live Rig Inventory

> Work in progress. Recorded from NI Measurement & Automation Explorer (NI-MAX) on the animal-facility rig PC.

## DAQ hardware

- Device name: `Dev1`
- Model: **National Instruments PCIe-6321**
- Serial number: `01C8BE45`
- NI-MAX status during inventory: Present
- Device temperature during inventory: approximately 32.8 °C
- Earlier project notes incorrectly assumed PCIe-6251; use the live PCIe-6321 configuration as authoritative.
- `SimDev1` is an NI simulated DAQ device, not the physical rig card; do not assign live tasks to it.

Calibration information shown by NI-MAX:

- External calibration: 13 September 2017
- Recommended next external calibration: 13 September 2019 (overdue)
- Last self-calibration: 13 August 2022

Do not initiate calibration during wiring/inventory. Flag the overdue external calibration to the lab
and decide separately whether traceable analog accuracy is required before experiments.

NI-MAX device configuration:

- Connector 0 accessory setting: None
- `port0` power-up state: all eight lines tristated (high-impedance)

Configuration backup:

- Full NI-DAQmx 17.0 configuration exported from `My System` on 20/08/26 after the X/Y-order fix
  and successful GitHub-copy bench test.
- Repository file:
  [`ni-max/JoystickPushTask_NIMAX_2026-08-20.nce`](ni-max/JoystickPushTask_NIMAX_2026-08-20.nce)
- This is a disaster-recovery snapshot, not a substitute for reviewing physical channels before
  import. Inline DAQmx channels created directly by LabVIEW may not appear as saved tasks.

Official PCIe-6321 capacity:

- 16 single-ended or 8 differential analog inputs
- 2 analog outputs
- 24 bidirectional digital I/O lines
- 4 general-purpose counters (`ctr0`–`ctr3`)

Other devices visible in NI-MAX:

- PS3Eye Camera → `cam2`
- DMK 37BUX287 camera → `cam3`
- Serial port → `COM1`
- USB3 Vision Device (unused) → `USB-0`



## Existing NI-DAQmx tasks

- `joysticklickframe`
- `joysticklickframe_push`
- `Magnets_Dev1`
- `MagnetPush_Dev1`
- `Water_Dev1`
- `SuccessCue_Dev1`
- `LickSpout_Dev1`
- `rest_pad_test_Dev1`
- `success_cue_test_Dev1`
- `lick_spout_motor_test_Dev1`
- `frame counter_Dev1`
- `MyPulseOutputTask`
- `testing1blox_2labviews`



## Live LabVIEW program audit — 12/08/26

- The edited behavioural-rig hierarchy was imported into the repository as
  `Push Behaviour_MCHALABI.vi`; untouched `Pull_Behaviour_march2020` remains the fallback.
- Screenshots confirm the expected parameter loader, five-case trial state machine, occurrence-driven
water loop, and lower occurrence-driven perturbation/laser loop.
- The working push VI now performs:
  `cue HIGH → cue wait → cue LOW → reward delay → spout extend → settle → water HIGH →
  explicit watertime wait → water LOW → consumption wait → spout retract`.
- The lower occurrence loop contains both `Magnets_Dev1` analog writes and `Dev1/ctr1` laser-pulse
generation. Magnet support was preserved but converted to `MagnetPush_Dev1` on AO0 only; the laser
branch was not removed.
- `avg joystick and frame trig lick3.vi` uses `joysticklickframe` with DAQmx Analog 2D
`NChan NSamp`, averages indexed channels 0–3, builds a four-value array, and enqueues it as
`joystick pos`. A push-specific copy of the NI-MAX task can add `Dev1/ai2` as the third channel,
making rest-pad voltage queue element index 2 without restructuring the acquisition loop.
- Keep the original global `joysticklickframe` task unchanged; point the working-copy subVI to a new
task named `joysticklickframe_push`.
- The attempted LabVIEW **Duplicate hierarchy to new location** copy was deleted because the expected
VI was not present in the selected folder. The entire containing folder was then copied manually
and marked with the suffix `- PushVersion - working`. This is the push-task working hierarchy; the
original `LabView files` folder remains the untouched operational baseline.
- Git cannot automatically merge independently changed `.vi` binaries.
- Core working-VI bench validation passed 18/08/26: first-trial rest-pad gating, cue, spout
extension, primed water delivery, consumption wait and retraction all worked across three spaced
successful trials. Fail/timeout behavior was also reported working. Abort-path output cleanup has
not been specifically validated.
- Fresh GitHub-copy validation passed on the rig PC 20/08/26 after correcting the NI-MAX X/Y channel
  order and replacing the repository's unusable `frame counter.vi` with the compatible copy from the
  working hierarchy. The main VI opened with a healthy Run arrow and completed the full bench sequence.



## Confirmed task configuration



### `joysticklickframe`

- Purpose: reads the existing joystick position.
- `X_POS` → `Dev1/ai0`
- `Y_POS` → `Dev1/ai1`
- Input range: −10 V to +10 V
- Terminal configuration: Differential
- Acquisition: Continuous Samples
- Sample rate: 10 kHz

Do not assign `ai0` or `ai1` to the new FSR rest-pad sensor.

### `joysticklickframe_push` — created 12/08/26

- New independent AI task created for the working push-task hierarchy; original
`joysticklickframe` remains unchanged.
- Corrected channel order confirmed 20/08/26 as `Dev1/ai1`, `Dev1/ai0`, `Dev1/ai2`
  (`Y_POS`, `X_POS`, FSR). The first push-task configuration used `ai0`, `ai1`, `ai2`, which
  swapped X/Y relative to the unchanged LabVIEW array-index convention inherited from the old task.
- Final channel configuration: `ai0` and `ai1` differential ±10 V; `ai2` RSE, 0–5 V.
- Final timing: Continuous Samples, 10 samples/read, 10 kHz.
- Saved NI-MAX test passed 12/08/26: joystick X, joystick Y, and FSR signals were all visible
simultaneously; FSR responded as expected.
- Working-copy `avg joystick and frame trig lick3.vi` was updated and saved to select
`joysticklickframe_push`; original hierarchy remains pointed at `joysticklickframe`.
- Working-copy main VI Case 0 now reads queue element index 2 into a `rest pad voltage` indicator;
`rest pad voltage > rest pad threshold (V)` now drives a `paw on rest pad` Boolean indicator.
Starting threshold is 0.10 V pending animal-mounted calibration.
- A new AND combines the original X/Y home-ROI result with `paw on rest pad` before the existing
`home TO` hold logic. The separate inter-trial timeout gate is unchanged.
- Runtime test passed: index-2 FSR voltage and `paw on rest pad` changed correctly when Case 0 became
active after a completed/rewarded trial. The apparent initial failure was expected Case Structure
behavior—the indicator does not update while another case executes.
- Working-VI state shift-register initializer changed from 1 to 0 so sessions start in Case 0.
Fresh-run validation passed 12/08/26: the first trial remained gated until paw contact.



### `Magnets_Dev1`

- Purpose: controls the existing two-axis magnetic perturbation hardware.
- `VoltageOut` → `Dev1/ao0`
- `VoltageOut_0` → `Dev1/ao1`
- Output range: −10 V to +10 V
- Generation mode: 1 Sample (On Demand)
- Both available PCIe-6321 analog outputs are currently included in this task.
- The NI-MAX screen showed 1.1 V as the configured test value for both channels; the task was not run.

`Magnets_Dev1` is retained only as an original/legacy task. The working push VI no longer references
it. Its replacement is `MagnetPush_Dev1` on AO0 only, leaving AO1 exclusively available to
`LickSpout_Dev1`.

### `Water_Dev1`

- Purpose: controls the existing water-solenoid output.
- `DigitalOut` → `Dev1/port0/line0`
- Output type: Digital Line Output
- Generation mode: 1 Sample (On Demand)
- `Invert Line`: unchecked

Physical active-high behavior is verified: NI-MAX False→True→False and the LabVIEW sequence both
produce valve clicks and water. The line must be primed and bubble-free before short pulses are
reliable. Bench duration is currently 200 ms, pending delivered-volume calibration.

### `frame counter_Dev1`

- Purpose: counts incoming frame/synchronization pulses.
- Counter resource: `Dev1/ctr0`
- Input terminal: `PFI8`
- Active edge: Rising
- Initial count: 0
- Direction: Count Up
- Acquisition: 1 Sample (On Demand)

Each LOW→HIGH transition arriving on `PFI8` increments counter 0. Keep both `ctr0` and `PFI8`
reserved for the existing frame synchronization.

### `MyPulseOutputTask`

- Purpose: not yet traced physically; likely an existing synchronization/trigger pulse output.
- Counter resource: `Dev1/ctr1`
- Output terminal: `PFI13`
- Generation: Continuous Pulses
- Idle state: Low
- Initial delay: 0 s
- HIGH time: 10 ms
- LOW time: 10 ms
- Resulting pulse frequency: 50 Hz

Keep both `ctr1` and `PFI13` reserved until the task's physical destination and LabVIEW use are
identified. The PCIe-6321 has four counters: saved tasks account for `ctr0` and `ctr1`; `ctr2` and
`ctr3` are not represented in the saved-task list. The active success buzzer still only needs a
spare ordinary digital-output line.

### `testing1blox_2labviews`

- Likely purpose: legacy/diagnostic analog-input test; confirm before deleting or ignoring.
- `Voltage_0` → `Dev1/ai0`
- `Voltage_1` → `Dev1/ai1`
- Input range: −10 V to +10 V
- Terminal configuration: Differential
- Acquisition: N Samples
- Samples to read: 100
- Sample rate: 1 kHz

This task duplicates the same physical AI channels used by `joysticklickframe`. Saved tasks may
overlap resources; they conflict only if software attempts to reserve/run them simultaneously.
Its finite 100-sample configuration and name suggest a test task, but check LabVIEW references
before removing it.

## Breakout box

- Model: **NI SCB-68A** shielded connector block, 68 screw terminals
- Box label: `rig1`
- Connects to `Dev1` via the 68-pin cable; NI-MAX itself still lists the accessory as "None"
- Contains a custom breadboard/component area already populated with user-added circuitry
- The lid label shows S1/S2 switch diagrams for the onboard temperature sensor. Because the joystick
uses AI0/AI8 in differential mode, the temp sensor must be in the disabled (factory default)
position; confirm the physical switches before touching AI0.



### Red regulator module (joystick power supply)

Traced 04/08/26. This is an adjustable DC-DC converter mounted in the breadboard area:

- `IN+` ← red wire from **terminal 14 (+5 V)**
- `IN−` ← black wire from **terminal 50 (D GND)**
- `OUT+` → yellow wire into the rig enclosure, entering the joystick base
- `OUT−` → grey wire into the rig enclosure, entering the joystick base

This supplies the joystick's excitation voltage, and its trim pot is almost certainly what sets the
documented ~2.55 V resting output. **Do not remove, repower or re-trim this module** — doing so would
silently recalibrate every position reading. Note that this consumes **terminal 14**, so the second
+5 V terminal (**8**) must be used for the FSR excitation.

### Laser interlock — SAFETY CRITICAL

**Terminal 42 (PFI 3 / P1.3)**, with **terminal 7 (D GND)** as its return, is wired to a unit labelled
`MDL-III-635L-200mW` (`DC30041`). That is a **200 mW, 635 nm laser — Class 3B**, driven from the
black key-switched supply beside the breakout box.

- No saved NI-MAX task references PFI 3, so this line is commanded directly from LabVIEW code.
- Never toggle PFI 3 / P1.3, and never run an unknown digital task, while the laser key is enabled.
- Keep the laser supply keyed off during all bench testing of the new hardware.



### Saved NI-MAX tasks are not the full picture

PFI 3 is physically wired to the laser but appears in **no** saved NI-MAX task. LabVIEW therefore
creates at least some DAQmx channels inline. Treat the saved-task list as incomplete and confirm
channel usage against the VI before claiming any line is free.

### SCB-68A terminal map (X Series / 63xx label, verified against NI documentation)

Analog input (differential pairs `AI x+` with `AI x+8`):


| Signal       | Terminal | Signal        | Terminal |
| ------------ | -------- | ------------- | -------- |
| AI 0 (AI 0+) | 68       | AI 8 (AI 0−)  | 34       |
| AI 1 (AI 1+) | 33       | AI 9 (AI 1−)  | 66       |
| AI 2 (AI 2+) | 65       | AI 10 (AI 2−) | 31       |
| AI 3 (AI 3+) | 30       | AI 11 (AI 3−) | 63       |
| AI 4 (AI 4+) | 28       | AI 12 (AI 4−) | 61       |
| AI 5 (AI 5+) | 60       | AI 13 (AI 5−) | 26       |
| AI 6 (AI 6+) | 25       | AI 14 (AI 6−) | 58       |
| AI 7 (AI 7+) | 57       | AI 15 (AI 7−) | 23       |


- AI GND: 67, 32, 64, 29, 27, 24, 56, 59
- AI SENSE: 62

Analog output:

- AO 0 → 22, AO GND → 55
- AO 1 → 21, AO GND → 54

Digital port 0:


| Line | Terminal | Line | Terminal |
| ---- | -------- | ---- | -------- |
| P0.0 | 52       | P0.4 | 19       |
| P0.1 | 17       | P0.5 | 51       |
| P0.2 | 49       | P0.6 | 16       |
| P0.3 | 47       | P0.7 | 48       |


- +5 V: 14 and 8
- D GND: 53, 18, 50, 15, 13, 12, 44, 9, 7, 4, 36, 35
- PFI 8 / P2.0 → 37 (frame counter input); PFI 13 / P2.5 → 40 (pulse output)



### Physically occupied terminals (surveyed 04/08/26)


| Terminal | Signal       | Connected to                             |
| -------- | ------------ | ---------------------------------------- |
| 68       | AI 0 (AI 0+) | joystick X position                      |
| 34       | AI 8 (AI 0−) | joystick X position, differential return |
| 33       | AI 1 (AI 1+) | joystick Y position                      |
| 66       | AI 9 (AI 1−) | joystick Y position, differential return |
| 67       | AI GND       | analog ground                            |
| 27       | AI GND       | analog ground                            |
| 8        | +5 V         | FSR divider excitation                   |
| 65       | AI 2         | FSR rest-pad signal                      |
| 64       | AI GND       | FSR divider return                       |
| 21       | AO 1         | Actuonix 0–5 V position command          |
| 54       | AO GND       | Actuonix command/external-PSU common     |
| 52       | P0.0         | water solenoid                           |
| 18       | D GND        | water solenoid return                    |
| 17       | P0.1         | Adafruit success buzzer positive         |
| 15       | D GND        | Adafruit success buzzer return           |
| 14       | +5 V         | red regulator module `IN+`               |
| 50       | D GND        | red regulator module `IN−`               |
| 42       | PFI 3 / P1.3 | 635 nm 200 mW laser control              |
| 7        | D GND        | laser return                             |




### Terminals confirmed physically empty

- **22 (AO 0)** — reserved for a future axial-resistance magnet; currently no wire landed
- 37 (PFI 8) and 40 (PFI 13) — not in the occupied list
- AI10 terminal 31 remains unused because FSR AI2 uses RSE, not differential
- Remaining unused P0 lines: P0.2–P0.7



### Analog-output split and current physical state

AO1 terminal 21 is now physically wired to the Actuonix command input. AO0 terminal 22 remains
physically empty because this training rig has no magnet. The old `Magnets_Dev1` task still contains
both channels but is not used by the working push VI; `MagnetPush_Dev1` owns AO0 and
`LickSpout_Dev1` owns AO1.

Consequences:

- An AO channel **is** available for the Actuonix, so the lick spout is no longer blocked.
- Confirmed 12/08/26: this behavioural training rig has **no perturbation magnet hardware**.
- Perturbation magnet hardware exists only on the separate rig under the mesoscope.
- Preserve training-rig magnet support for possible later installation, but `Magnets_Dev1` must no
  longer reserve AO1. Target split: one-channel on-demand magnet task on AO0 and one-channel
  on-demand Actuonix task on AO1.
- NI documentation permits one software-timed/on-demand AO task per physical AO channel. Both current
  outputs use on-demand writes, so magnet AO0 and spout AO1 can coexist; hardware-timed AO would
  require a combined task because the PCIe-6321 has one AO timing engine.
- Live LabVIEW magnet-loop audit 18/08/26 shows two `Analog 1D DBL NChan 1Samp` writes using
  `Magnets_Dev1`: one command write and one later reset write. Both can be converted to a new
  one-channel AO0 task without altering the separate counter/laser logic.
- `MagnetPush_Dev1` created 18/08/26: `Dev1/ao0` only, ±10 V, 1 Sample (On Demand). Saved but not
  physically exercised because no magnet is connected on this rig.
- Working-copy LabVIEW magnet task constant changed to `MagnetPush_Dev1`; its two DAQmx Write nodes
  were converted to `Analog DBL 1Chan 1Samp`. Activation writes scalar `mag`; reset writes scalar
  zero; both retain auto-start=True. Magnet code now addresses AO0 only and cannot command AO1.
  Working VI retained a solid Run arrow after the refactor.
- Live water-loop audit 18/08/26 confirms its existing Flat Sequence performs
  `Water_Dev1 HIGH → wait watertime → Water_Dev1 LOW`; new cue/spout frames should wrap these without
  replacing them.
- Final output tasks created 18/08/26:
  - `SuccessCue_Dev1` → `Dev1/port0/line1`, digital one-sample/on-demand
  - `LickSpout_Dev1` → `Dev1/ao1`, 0–5 V, one-sample/on-demand
  Existing test tasks remain saved but must not run concurrently on the same lines.
- Working water loop now begins with `SuccessCue_Dev1 HIGH → 50 ms wait → SuccessCue_Dev1 LOW`
  before the preserved water sequence. Runtime test passed 18/08/26: one brief cue occurred per
  successful trial and stopped cleanly.
- Spout/reward frames added with initial bench defaults: reward delay 0 ms; extend command 1.0 V;
  settle 3000 ms; consumption 2000 ms; retract command 0 V. Both `LickSpout_Dev1` analog writes use
  scalar `Analog DBL 1Chan 1Samp` with auto-start=True.
- First LabVIEW sequence test 18/08/26: actuator made the expected coarse 1.0 V extension, followed
  by slight continued fine extension coincident with its familiar audible settling sound. The
  L12-I requires a continuously held setpoint and uses a fixed internal digital position controller;
  time repeated trials to confirm all fine motion/noise stops within the 3000 ms settle window.
- Bench controls later set to extend=3.0 V, settle=2000 ms, consumption=2000 ms, retract=0 V,
  reward delay=0 ms and cue=50 ms; settling sound/fine movement accepted provisionally.
- Automated reward sequence currently produces cue and spout motion but no visible water delivery;
  `watertime` is 200 ms but no solenoid click occurs. NI-MAX `Water_Dev1` False→True→False produces
  clicks and water, and LabVIEW visibly writes True then False. Inspect Water HIGH DAQmx error; if
  clear, verify the middle frame contains a real 200 ms Wait rather than only a sequence local.
- Water HIGH returned no DAQmx error. A 200 ms Wait added inside the same frame as HIGH produced a
  click but no water. User reports it was already placed in a dedicated frame, while the untouched
  original VI delivers water without the added Wait. Exact timing-node/frame placement is unresolved;
  compare readable close-ups before further modification.
- A dedicated 1000 ms HIGH test then produced automated water successfully. This rules out the
  task/channel/valve and shows either 200 ms is currently below the reliable delivery threshold or
  the line needed priming. Retest short pulses after priming and calibrate delivered volume before
  animal use; 1000 ms is diagnostic only.
- Immediate post-prime retest at 200 ms worked. Multiple air bubbles were observed in the tubing;
  failed short-pulse delivery was therefore caused by an unprimed/air-filled water path, not DAQ or
  LabVIEW. Inspect and prime until bubble-free before each session; calibrate 200 ms output in µL.
- Three spaced complete trials then passed with cue, extension, water and retraction on every trial.
  The explicit 200 ms Wait is nominally the same intended duration as original `watertime=200`, but
  exact pulse equivalence has not been electrically measured; functional calibration should use
  delivered water mass/volume.
- Random/Fixed perturbation blocks cannot be physically bench-tested on this training rig; their
hardware mapping and sign must be validated separately on the mesoscope rig.



### Channel availability implications

- The joystick task runs in **differential** mode, so it physically consumes AI 0, AI 8, AI 1 and
AI 9 (terminals 68, 34, 33, 66). `ai2` and above are the genuinely free analog inputs.
- `P0.0` (terminal 52) is the water valve. `P0.1`–`P0.7` are candidate buzzer lines.
- Port 0 lines can source up to 24 mA; PFI lines only 16 mA. The Adafruit #1536 buzzer draws roughly
24 mA at 5 V, so it must use a **port 0** line, and even then it sits at the specification limit —
add a small transistor/MOSFET driver if the tone is weak or the line is loaded.
- Terminal 14 (+5 V) is taken by the regulator module; use **terminal 8** for FSR excitation.



## Still to inspect

- [x] `Magnets_Dev1`: `Dev1/ao0` + `Dev1/ao1`, −10 V to +10 V, on-demand
- [x] AO terminals 21 and 22 confirmed physically empty; magnet drive not currently wired
- [x] Confirmed: no perturbation magnet on training rig; magnet exists on mesoscope rig only
- [x] `Water_Dev1`: `Dev1/port0/line0`, digital line output, on-demand, not inverted in NI-MAX
- [x] `frame counter_Dev1`: `Dev1/ctr0`, rising edges from `PFI8`
- [x] `MyPulseOutputTask`: `Dev1/ctr1` output on `PFI13`, continuous 50 Hz pulse train
- [ ] Confirm whether PFI 8 / PFI 13 are only connected when the imaging system is attached
- [x] `testing1blox_2labviews`: duplicate AI test on `Dev1/ai0` + `Dev1/ai1`, 100 samples at 1 kHz
- [ ] Search LabVIEW/project references before classifying `testing1blox_2labviews` as unused
- [x] Device capacity checked against PCIe-6321 specification: 16 SE/8 differential AI, 2 AO, 24 DIO, 4 counters
- [x] Physical connector/breakout-box model: NI SCB-68A, labelled `rig1`
- [x] Recorded which SCB-68A screw terminals physically have wires landed in them
- [x] Red breadboard module identified as the joystick supply regulator
- [x] PFI 3 traced to a Class 3B 635 nm laser
- [ ] Audit the VI for inline DAQmx channels not represented in saved NI-MAX tasks
- [ ] Confirm S1/S2 temperature-sensor switch positions



## New channels — installed and bench-tested


| Component             | Channel            | SCB-68A terminals                                                                           | Status                                                                                                  |
| --------------------- | ------------------ | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| FSR 402 rest pad      | `Dev1/ai2`         | signal → 65, ground → AI GND (64), excitation → +5 V (**8**, not 14)                        | installed; NI-MAX and first-trial LabVIEW gating passed; animal-safe cap/calibration remain             |
| Adafruit #1536 buzzer | `Dev1/port0/line1` | `+` → 17 (P0.1), `−` → 15 (D GND)                                                           | installed; NI-MAX and 50 ms LabVIEW success-cue tests passed                                            |
| Actuonix lick spout   | `Dev1/ao1`         | signal → 21, reference → AO GND (54), motor power from separate 12 V PSU with shared ground | installed; `LickSpout_Dev1` and full extend/water/retract sequence passed across three spaced trials    |


Leave `ao0` (terminal 22) reserved for the axial-resistance perturbation.

### Buzzer installation — 06/08/26

- Adafruit #1536 manufacturing wash seal removed; buzzer was not washed.
- Positive/long lead wired to terminal 17 (`P0.1`).
- Negative/short lead wired to terminal 15 (`D GND`).
- Direct-drive test chosen for initial prototype. Official nominal current is 15 mA, but independent
measurements report up to approximately 24 mA at 5 V, equal to the PCIe-6321 P0 per-line limit.
Treat direct drive as provisional; stop on DAQ error, weak/unstable output or excessive voltage drop.
- Saved NI-MAX task: `success_cue_test_Dev1`
  - Physical channel: `Dev1/port0/line1`
  - Digital line output, not inverted
  - Generation: 1 Sample (On Demand)
- Final task: `SuccessCue_Dev1` on the same line, one-sample/on-demand.
- Direct LOW→HIGH→LOW test passed on 06/08/26: HIGH produced a loud, clear high-pitched tone and
LOW silenced it; no NI-MAX error reported.
- Buzzer leads subsequently soldered and insulated, connected permanently to terminals 17/15, and
the LOW→HIGH→LOW NI-MAX test passed again.
- Working VI writes HIGH, waits a configurable 50 ms bench duration, then writes LOW immediately on
success. End-to-end runtime test passed.



### Actuonix L12-I — identified 06/08/26

- Exact model: `L12-30-50-12-I` (30 mm stroke, 50:1, 12 V, integrated controller)
- Six manufacturer leads split across two three-pin female connectors:


| Wire   | Function                         | Planned use                                           |
| ------ | -------------------------------- | ----------------------------------------------------- |
| Green  | 4–20 mA current-command input    | Unused; insulate                                      |
| Blue   | 0–5 V voltage/PWM command input  | `Dev1/ao1`, terminal 21                               |
| Purple | 0–3.3 V position-feedback output | Optional future AI logging                            |
| White  | RC-servo command input           | Unused; insulate                                      |
| Red    | 12 V motor/controller power      | External regulated +12 V                              |
| Black  | Ground                           | External PSU negative + shared DAQ AO GND terminal 54 |


The L12-I scans green, blue and white at power-up and locks to the first valid interface. For 0–5 V
mode, connect blue and shared ground before applying 12 V; leave the current and RC inputs isolated.
The blue command must remain driven after reaching position. Never power the actuator before its
command wiring is defined and the rod has unobstructed travel.

AO command verification 06/08/26:

- Saved NI-MAX task: `lick_spout_motor_test_Dev1`
- Physical channel: `Dev1/ao1`
- Range: 0–5 V
- Generation: 1 Sample (On Demand)
- Terminal 21 (`ao1`) measured relative to terminal 54 (`AO GND`)
- Commands 0, 1, 2.5 and 5 V all matched the multimeter as expected
- AO1 returned to 0 V after testing

Actuator wiring paused at end of 06/08/26:

- Both double-ended 3-pin headers inserted into the actuator's female connectors
- Female jumper attached to the exposed header pin aligned with the actuator black/ground lead
- Jumper's free end remains a female socket; it has not yet been cut/stripped
- Red power and blue command leads remain disconnected
- Actuator has never been powered
- Resume by converting the black jumper's loose end to bare wire, then building the shared ground
connection with barrel-adapter `−` and SCB terminal 54

Actuator bench wiring assembled 12/08/26:

- Actuator black lead and SCB terminal 54 (`AO GND`) share barrel-adapter `−`
- Actuator red lead connects to barrel-adapter `+`
- Actuator blue 0–5 V command lead connects temporarily via insulated alligator connection to the
wire from SCB terminal 21 (`ao1`)
- Green current input, purple feedback and white RC input remain disconnected/isolated
- Wiring visually checked by user; actuator still unpowered at this checkpoint
- Alligator connection is bench-test-only and must be replaced by a soldered/connectorized harness
before mounting or animal use

First controlled actuator power-up 12/08/26:

- AO1 explicitly written to 0 V before applying 12 V power
- No unexpected motion, noise or fault at 0 V power-up
- Command changed to 1.0 V; actuator extended a small amount as expected (~20% command)
- Confirms correct power polarity, shared ground, blue voltage-command wiring and successful
automatic selection of the 0–5 V interface mode
- Command returned to 0 V; actuator retracted fully and smoothly without abnormal noise.
- 2.5 V commanded approximately half stroke and returned correctly to 0 V.
- 5.0 V commanded the full measured 30 mm stroke and returned correctly to 0 V.
- For command changes of roughly 2 V or greater, actuator emits a tone/whine for approximately
1–2 seconds after reaching the commanded position, then stops. No failure reported.
- Likely internal position-loop settling, but re-evaluate after replacing the temporary blue
alligator connection. Treat as abnormal if accompanied by visible hunting, persistent noise,
repeated clicking, heating or failure to stop.
- Datasheet maximum duty cycle is 20%; avoid rapid repeated full-stroke cycling and allow cooling.
- Temporary blue alligator command connection replaced on 12/08/26 by a soldered, heat-shrunk splice
between the blue-header female jumper and the wire from SCB terminal 21.
- Unused green, purple and white interface pins insulated; connector wiring strain-relieved.
- Post-solder 0 → 2.5 → 0 V motion test passed smoothly.
- Actuator electrical bench installation was complete at this checkpoint; mechanical mounting was
completed later the same day. Remaining work is animal-specific calibration and final cable cleanup.

Mechanical lick-spout installation — 12/08/26:

- Actuator mounted on the rig and attached to the lick spout.
- User confirmed unobstructed motion with no mechanical interference across the tested movement.
- Mounted system responds correctly when powered/commanded.
- Still to record/validate:
  - Final retracted and extended command voltages
  - Spout position relative to the mouse
  - Tubing and cable strain relief across the full movement
  - Repeated-cycle reliability within the actuator's 20% duty-cycle limit
- Tubing/wire routing checked through motion: no obstruction or impedance; final cable cleanup remains.
- Existing water-valve delivery through the mounted moving spout tested successfully with no reported
leak/snag.
- Final NI-MAX task `LickSpout_Dev1`: AO1, 0–5 V, one-sample/on-demand.
- Working-VI bench controls on 18/08/26: retract 0 V, extend 3.0 V, settle 2000 ms, consumption
2000 ms, reward delay 0 ms. These are bench values, not final mouse-specific settings.
- Full cue → delay → extend → settle → 200 ms water → consumption → retract sequence passed across
three spaced trials after tubing was primed bubble-free.

Power status:

- No dedicated 12 V supply was included with the actuator.
- A Goobay 3–12 V universal supply was found on 06/08/26:
  - Model `MW MB10EU`
  - Selectable 12 V output rated 1 A / 12 W
  - Capacity is sufficient for the L12-I
  - Voltage selector and connector polarity must be independently verified before connection
- The actuator cannot be powered from a DAQ AO, DAQ +5 V terminal or USB.
- Required supply capacity is at least 0.5 A (1 A recommended); the located Goobay unit meets this.
- Do not repurpose the laser driver, joystick regulator or an unidentified rig supply.
- One three-pin male-to-male adapter and mechanical screws/attachments were supplied; photograph and
inventory connector hardware before wiring.
- Supply verification 06/08/26:
  - Selector set to 12 V
  - Initial reversible-tip orientation measured −11.97 V with red probe at centre
  - Tip rotated 180°
  - Final output measured **+11.97 V centre-positive** (red probe centre, black probe outer sleeve)
  - Supply unplugged again after verification
- Connector hardware found 06/08/26:
  - Matching female DC barrel-jack to two-screw adapter, labelled `+` and `−`; plug fit confirmed
  - Two double-ended 3-pin male headers, sufficient to break out both actuator female connectors
  - Barrel adapter measured approximately +11.97 V with red probe on `+` screw and black probe on
  `−` screw; adapter polarity verified
  - At this checkpoint the actuator remained unpowered; subsequent AO1, powered-motion and full
    LabVIEW sequence tests passed as documented above



### FSR bench test — 05/08/26

- 10 kΩ divider resistor measured approximately 9.88 kΩ.
- FSR measured open circuit when unloaded.
- Direct multimeter measurement across the two solder tabs produced a resistance value when the
sensing area was pressed, confirming that the sensor responds to force.
- Two flexible leads were soldered to the factory solder tabs. The completed joints passed the same
unloaded/pressed resistance test.
- Breadboard divider assembled using the FSR and 9.88 kΩ resistor.
- Breadboard resistor branch measured correctly across the signal/ground nodes.
- Breadboard FSR branch measured open unloaded and force-responsive when pressed.
- Divider connected to SCB-68A: yellow terminal 8→A10, green terminal 65→A11, blue/black
terminal 64→A15; FSR at E10/E11; resistor D11→D15.
- With the rig PC powered, the divider supply measured **5.06 V** between the +5 V and AI GND nodes.
- Divider signal measured relative to AI GND:
  - Unpressed: 0.000 V
  - Light/intermediate pressure: approximately 0.2–1.5 V
  - Hard pressure: approximately 4.7–4.8 V
- Signal rises monotonically with applied pressure. Electrical bench test passed; NI-MAX `ai2`
acquisition test passed.
- On 05/08/26 the temporary breadboard divider was replaced with an inline soldered harness and the
yellow/green/blue leads were reattached to SCB terminals 8/65/64 respectively.
- On 06/08/26 the permanent harness passed its post-solder `rest_pad_test_Dev1` verification:
released baseline near zero, graded pressure peaks, and no large artifacts during gentle cable
movement. Electrical installation is complete; the FSR remains mechanically loose beside the rig.



### NI-MAX FSR test task — 05/08/26

- Saved task: `rest_pad_test_Dev1`
- Physical channel: `Dev1/ai2`
- Input range: 0–5 V
- Terminal configuration: RSE
- Acquisition: Continuous Samples
- Samples to read: 100
- Rate: 1 kHz
- Result: stable near-zero released baseline and graded upward voltage peaks under increasing force.
- Working push task uses `joysticklickframe_push`; rest-pad voltage is queue element index 2.
- Case 0 requires joystick home X/Y AND `paw on rest pad`, then applies the existing home hold.
- State initializer changed from 1 to 0 so the first trial cannot bypass the gate; fresh-start test
passed. Current bench threshold shown on 18/08/26 was 0.01 V and must be recalibrated with the final
paw-contact cap and animal.

The PCIe-6321 has one analog-input timing engine, so this standalone test task is for bench testing
only. For the experiment, `ai2` must be appended to the existing joystick analog-input acquisition
task; do not attempt to run `rest_pad_test_Dev1` simultaneously with `joysticklickframe`.

### Proposed mechanical rest-pad location — 05/08/26

- Selected location: fixed black horizontal rail immediately in front of the head-fixation tube,
beside the future push-object position.
- FSR circular active area sits flat on the rail; tail routes laterally away from the paw and object.
- This location preserves the intended sequence: paw on fixed pad → leave pad → contact push object.
- Temporary geometry testing may use removable tape on the inactive tail/perimeter only.
- Final animal-ready mounting requires a small protective paw-contact cap/puck, tail strain relief,
and protection from claws/moisture; do not glue or preload the active sensing circle.



### Temporary mechanical mount — 06/08/26

- FSR mounted face-up on the selected fixed rail in front of the head tube.
- Inactive tail and cable secured laterally with removable tape/strain relief.
- Mounted sensor retained a near-zero unloaded baseline and graded pressure response in
`rest_pad_test_Dev1`.
- Temporary mount passed bench testing.
- **Not yet animal-ready:** active sensing face remains exposed and needs a centred protective
paw-contact cap/puck plus final cleanable mounting.

