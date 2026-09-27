# Ledex / PVA 1.6 commissioning handoff

**Status 27/09/2026:** The Hydraulik-Kompetenz **PVA 1.6 0–10 V** driver is now physically
available at the training rig. The Ledex `195224-230`, reserved 12 V / 1 A Goobay supply,
`MagnetPush_Dev1` NI-MAX task and LabVIEW AO0 path already exist, but the driver and coil have
not yet been wired or powered together.

This page is the handoff for the rig-PC AI agent. Guide the user through one checkpoint at a
time, record actual measurements, and update `.cursorrules` after every completed step. Do not
skip ahead after a failed measurement.

## Safety and Sunday scope

- Keep the Class 3B laser keyed **off** throughout.
- No animal and no experimental parameter file during commissioning.
- Secure the driver and Ledex before power. Keep fingers, loose steel tools and the washer target
  away during first energisation.
- Never open or alter the mains side of the power adapter.
- The PVA can source up to 3 A even though the Ledex is nominally only about 0.58 A. Install a
  **1 A inline fuse** in the 12 V positive lead before powered testing. If no fuse is available,
  stop after unpowered inspection and wiring preparation.
- The printed Ledex holder is not proven to provide the heatsinking assumed by the continuous-duty
  coil rating. Use only short pulses with long cool-downs today.
- Stop for a blown fuse, unstable current, failure to release at 0 V, rapid heating, smoke/odour,
  unexpected LED state, binding or incorrect force direction.

Primary driver datasheet:
<https://www.hydraulikshop.ch/ftp/PVA_1.6_0919.pdf>

The shop description contains a `0–10 mA` typo. The ordered product and datasheet variant are
**0–10 V differential input**. Confirm the physical unit says 0–10 V; stop if it is the 4–20 mA
variant.

## Known hardware limits

- Ledex `195224-230`: 12 VDC, 7 W, approximately 20.7 ohm, nominal current approximately
  `12 / 20.7 = 0.58 A`.
- NI PCIe-6321 AO0: ±10 V range but only ±5 mA drive. Power-on/off can glitch as high as 2 V for
  500 ms, so keep the PVA Enable open until AO0 is initialised and measured at 0 V.
- AO0 command: `Dev1/ao0`, SCB-68A terminal **22**.
- AO0 reference: AO GND, SCB-68A terminal **55**.
- The coil must be powered by the reserved 12 V supply through the PVA, never by AO0.

## PVA terminal map

- `D`: +12–36 V supply (`+Ub`)
- `F`: power ground
- `E`: earth / chassis function
- `J`: Enable; below 1 V is disabled, above 4 V is enabled
- `K`: internal +10 V reference; unused here
- `M`: signal ground for the local-reference circuit; unused here
- `H`: positive 0–10 V command input
- `G`: negative command input
- `C`: positive coil output
- `A`: negative coil output

The LED should be red while disabled and green while enabled. Do not guess or jumper `F`, `G`
and `M` together. Do not improvise a mains-earth connection to `E`.

## Checkpoint 1 — unpowered preflight

With all power disconnected:

1. Confirm the driver is the 0–10 V model.
2. Measure and record the Ledex resistance. Expected cold value is approximately 20.7 ohm;
   roughly 18–22 ohm is a reasonable initial acceptance band.
3. Check that neither coil lead is shorted to the Ledex case.
4. Identify the adapter's positive and negative **low-voltage** conductors with the DMM.
5. Measure PVA `H–G` resistance as an initial AO-input screen. Stop if below 2 kohm, because
   10 V / 2 kohm already reaches the NI AO0 5 mA limit. A high or unstable semiconductor reading
   is only a preliminary screen.
6. Secure the PVA and Ledex mechanically.

Record the values before proceeding.

## Checkpoint 2 — wiring, still unpowered

Wire:

```text
12 V PSU +  ── 1 A inline fuse ──> PVA D
12 V PSU −                       ──> PVA F

SCB-68A terminal 22 / AO0        ──> PVA H
SCB-68A terminal 55 / AO GND     ──> PVA G

PVA C                            ──> Ledex lead 1
PVA A                            ──> Ledex lead 2

PVA D ── removable switch/jumper ──> PVA J Enable
                                      (leave open)
```

Leave `K` and `M` unused. Handle `E` only as part of an established lab chassis/functional-earth
scheme. Do not add a random external flyback diode across `C/A`: the PVA is itself a PWM
inductive-load driver, and an external diode may alter current regulation and release time.

## Checkpoint 3 — disabled power and AO command

1. Disconnect the coil for this checkpoint and leave Enable `J` open.
2. Set `Imin` and gain / `Imax` to their minimum positions without forcing the trimmer end stops.
   Leave dither at the factory position initially.
3. Power the 12 V supply. Measure about 12 V across `D–F`; the PVA LED should be red. Stop if it
   is green with `J` open, or if there is heating or smell.
4. In NI-MAX, initialise `MagnetPush_Dev1` to **0.0 V**. Before connecting `H`, measure terminal
   22 relative to 55 and confirm 0 V.
5. Connect `H/G`, then verify that commands of 0 V and small positive steps are reproduced across
   `H–G`. Never command a negative voltage.

If the DMM can safely measure the command-input current, measure it at 10 V while the output remains
disabled; it must be below 5 mA. Recheck the DMM lead sockets before returning to voltage mode.

## Checkpoint 4 — establish coil current with short pulses

1. Power off and insert the DMM in series with the coil on its suitable high-current range.
2. Keep the steel target away. Reconnect the coil, initialise AO0 to 0 V, power the PVA, then close
   the removable Enable jumper.
3. At a 0 V command, coil current must be effectively zero. Adjust `Imin` toward zero if needed.
   Stop if it energises strongly at 0 V.
4. Apply approximately 0.5-second pulses at `0.5, 1, 2, 3, 4, 5 V`, with at least 10 seconds off
   between pulses. Record command voltage, current, supply voltage, sound, release and temperature
   trend.
5. Continue toward 9–10 V only if current is stable, the coil remains cool and current stays below
   **0.58 A**. Measured current is authoritative. At the published minimum gain, rough expectations
   are 0.30 A at 5 V and 0.54 A at 9 V, but the 12 V supply leaves little driver headroom.
6. Establish and record the maximum allowed AO command that does not exceed 0.58 A cold.
7. Confirm that returning AO0 to 0 V removes current promptly. Open Enable before changing wiring.

## Checkpoint 5 — mechanical direction

Mount the Ledex on the **home side** of the object so attraction toward the steel washer opposes
the forward push. Start with a generous air gap and the lowest proven command. Verify:

- resistance is backward, not assistive;
- the object and target cannot collide with the Ledex;
- the spring returns the object;
- the 1D mechanism does not bind;
- current returns to zero and force releases at 0 V.

Sunday's successful endpoint is a repeatable, low-duty pull at known current with clean release.
Do not claim force calibration without a force gauge or load cell. A later calibration must map
AO command to force at the actual operating gap and characterize heating across repeated trials.

## Existing LabVIEW behavior and later code work

No LabVIEW edit is required for initial electrical commissioning:

- NI-MAX task `MagnetPush_Dev1` owns only `Dev1/ao0`.
- The main VI currently wakes the magnet loop at trial Case 2, writes scalar parameter `mag`,
  waits `magtime`, then writes 0 V.
- Safe startup already writes `MagnetPush_Dev1 = 0 V`.
- Normal Stop has been validated to end all loops without DAQ errors.
- Every current training/bench parameter file keeps `mag = 0`; leave them that way.

Before animal use or any nonzero experiment file, the canonical VI still needs:

1. a clamp from 0 V to the measured safe maximum;
2. guaranteed 0 V on success, timeout, Stop and DAQ/error paths;
3. logged command, calibration version, onset and offset;
4. verification of magnet-loop trial indexing;
5. later replacement of the Case-2 timed pulse with movement-onset activation held until trial
   end, matching the axial-resistance design.

Record actual wiring, measurements and outcomes in `RIG_INVENTORY.md` and
`calibration/README.md`, and update `.cursorrules` after each completed checkpoint.
