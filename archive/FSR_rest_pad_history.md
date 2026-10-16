# FSR 402 rest-pad history (archived)

The Interlink FSR 402 rest pad was used from August to October 2026 and replaced by the capacitive
Arduino pad (`arduino/touch_pad/README.md`) on 14 Oct 2026. Kept here for reference only; moved
unchanged from `RIG_INVENTORY.md`.

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
movement. Electrical installation was complete at this checkpoint; the FSR was subsequently placed
in the temporary rail mount documented below. Its animal-safe cap and final cleanable mounting
remain pending.



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
- Mount status reconfirmed 04/09/26: user reports the FSR is securely fixed in place with tape.
  Recheck the unloaded baseline after taping to ensure the active circle is not mechanically preloaded.
- Current status later on 04/09/26: the FSR tail/tongue ripped during testing. Do not splice a
  damaged printed tail.
- Replacement completed 08/09/26: new FSR 402 installed on the existing harness, fixed on the
  rail, protective tape over the contact face, and reported working with no issues. Do not treat
  the ripped 04/09 sensor as current. Recalibrate threshold/hysteresis on the taped surface;
  confirm the unloaded baseline is not preloaded by the tape. A dedicated cleanable puck remains
  optional if the taped cover stays stable.
