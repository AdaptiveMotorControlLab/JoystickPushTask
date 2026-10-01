# EVENTS logger plan (push VI)

Written 1 Oct 2026 for the agent working on the rig PC. It adds one new output file to
`Push Behaviour_MCHALABI.vi`. The three existing files (`joystick_*`, `TRIAL_*`, `REWARD_*`) and their
formats must stay exactly as they are.

## Why

The lab DataJoint pipeline (`MMathisLab/DataJoint_mathis`) currently gets only three things from this
rig: the joystick/FSR trace, one row per trial start (`TRIAL`) and one row per reward (`REWARD`). Many
things the task does are never written anywhere:

- every state-machine transition (Case 0 -> 1 -> 2 -> 3 -> 4, and the Case 3 -> 0 timeout/fail)
- trial outcome (success vs movement-window timeout), and so the ITI and the time spent in each case
- the water-loop sequence: cue on/off, reward delay end, spout extend, settle end, water on/off,
  consumption end, spout retract
- magnet on/off (and with what command voltage)
- absolute (wall-clock) time. The existing files only use sample indices, so they cannot be aligned to the
  video.

Two goals:

1. **A complete trial-event record** that can be analysed offline without re-deriving anything from
   voltages. Licks and movement events (paw-off, push onset) are deliberately excluded because they are
   computed offline.
2. **Accurate video alignment.** The camera software runs on this same PC and writes Unix-time frame
   timestamps (`TIMESTAMPS_VIDEO_*.npy`). Each event therefore stores both the joystick sample index
   **and** the PC's Unix time. Together with a 1 s heartbeat this maps every joystick sample onto the
   camera clock. A small Python script will later turn the reward events into the
   `TIMESTAMPS_LABVIEW_*.npy` file that the pipeline's `traj.SyncCameras` step needs. Without that file
   the pipeline cannot sync video for this task.

## File format (this is a contract with DataJoint; do not change it without updating the pipeline)

- Name: `EVENTS_<same base name as the other three files>`, same folder. Example: if the session writes
  `joystick_benchtest_for_datajoint`, this file is `EVENTS_benchtest_for_datajoint`. Build the path with the
  same mechanism that builds the `TRIAL_` / `REWARD_` paths, just with the `EVENTS_` prefix.
- Binary, **big-endian float64** (LabVIEW Write to Binary File default byte order), no header.
- Each record is **4 doubles**: `[event_code, sample_index, unix_time_s, value]`.
  - `event_code`: from the table below.
  - `sample_index`: the joystick-file record index at the moment of the event. It must use **the same
    units and counter as `TRIAL` column 2 and `REWARD` column 0**, so that the trial-start event's
    sample index equals the `TRIAL` row exactly.
  - `unix_time_s`: `Get Date/Time In Seconds` -> `To Double Precision Float` -> subtract `2082844800`
    (LabVIEW counts from 1904-01-01 UTC; Unix from 1970-01-01 UTC).
  - `value`: event-specific (see table), otherwise 0.
- **Write to Binary File must have `prepend array or string size?` = FALSE.** Otherwise LabVIEW inserts a
  4-byte length before every record and the file can't be parsed. The existing files have no headers
  (the bench joystick file is exactly records x 5 x 8 bytes); this one must match.
- File size must always be a multiple of 32 bytes.

## Event codes

Codes are permanent: never renumber or reuse a code; only add new ones.

| code | name | logged where | value |
|---|---|---|---|
| 1 | session start | once, right after the file is opened, before the trial loop starts | 0 |
| 2 | case entered | main loop, whenever the state changes (see step 3) | new case number (0-4) |
| 3 | trial start | Case 2, next to the `TRIAL` file write | trial number if available, else 0 |
| 4 | trial success | Case 4, next to the `REWARD` file write | 0 |
| 5 | trial timeout / fail | Case 3, in the movement-window-timeout branch (before returning to Case 0) | 0 |
| 10 | cue on | water loop, after `SuccessCue_Dev1` HIGH | 0 |
| 11 | cue off | water loop, after `SuccessCue_Dev1` LOW | 0 |
| 12 | reward delay end | water loop, after the reward-delay wait | 0 |
| 13 | spout extend | water loop, after the extend write to `LickSpout_Dev1` | commanded V |
| 14 | settle end | water loop, after the settle wait | 0 |
| 15 | water on | water loop, after `Water_Dev1` HIGH | water time (ms) |
| 16 | water off | water loop, after `Water_Dev1` LOW | 0 |
| 17 | consumption end | water loop, after the consumption wait | 0 |
| 18 | spout retract | water loop, after the retract write | commanded V |
| 20 | magnet on | magnet loop, after the AO write of `mag` | commanded V (`mag`) |
| 21 | magnet off | magnet loop, after the AO write of 0 | 0 |
| 90 | heartbeat | writer loop, every 1 s | 0 |
| 99 | session stop | writer loop, when `stop all` goes TRUE, before closing the file | 0 |

Notes:
- Code 2 alone already gives every transition, including a rest-pad-initiated trial that times out
  (2 -> 3 -> 0). Codes 3/4/5 are kept as explicit markers so the analysis doesn't depend on case numbering.
- Code 4 is logged at the same moment as the `REWARD` row, so its `unix_time_s` values are exactly
  the reward times the pipeline's camera sync expects.
- With `mag = 0` (magnet not commissioned) codes 20/21 still appear with value 0. "Magnet came on" means
  code 20 with value > 0.

## Implementation steps

Make a backup copy of both VIs before starting. Do not touch the acquisition loop in
`avg joystick and frame trig lick3.vi` except for step 0, if that turns out to be needed. That loop runs
1000 times/s and has already caused -200279 overruns.

### Step 0. Find the sample counter (inspect first, change nothing)

Find where the value written to `TRIAL` column 2 (trial-start sample) and `REWARD` column 0 comes from.
It is some counter of joystick samples or records (for example, a count of dequeued `joystick pos`
elements in the main VI, or a counter in the acquisition subVI).

- If it is already available as a global in `PushTask Globals.vi`, use that global.
- If it lives only on a wire in one loop, add a global `sample count` (DBL) to `PushTask Globals.vi`
  and write it **once per iteration at the place where that counter is updated**. The water loop, the
  magnet loop and the writer loop can then read it. One global write per iteration is fine; do not add
  anything else to the 1 kHz loop.

Report back which counter it is and where it lives before continuing.

### Step 1. `Log Event.vi` (new subVI)

- Inputs: `code` (DBL), `value` (DBL), `error in`. Output: `error out`.
- Inside:
  1. Read the `sample count` global from step 0.
  2. `Get Date/Time In Seconds` -> `To Double Precision Float` -> subtract `2082844800`.
  3. `Build Array` -> `[code, sample, unix_time, value]` (1D DBL, 4 elements).
  4. `Obtain Queue` **by name** `push events`, element type 1D DBL array, then `Enqueue Element`
     (unlimited queue, so it never blocks), then `Release Queue` (force destroy = FALSE; this only drops
     this call's reference).
- VI Properties -> Execution -> **Preallocated clone reentrant execution**, so calls from parallel loops
  never wait on each other.
- Timestamps are taken inside this subVI at call time, not later by the writer. That is why file I/O
  can't distort event times.

A named queue means no queue reference has to be wired into the water loop, the magnet loop or the
cases.

### Step 2. Writer loop (new While loop in the main VI)

- Before the loop: build the `EVENTS_` path, `Open/Create/Replace File` (operation: replace or create),
  then `Obtain Queue` named `push events` (same element type). This reference keeps the queue alive. Then
  call `Log Event` with code 1.
- Loop body:
  - `Dequeue Element` with timeout 200 ms. If not timed out, `Write to Binary File` the 4-element array
    (big-endian, **prepend size = FALSE**).
  - Heartbeat: if 1 s has passed since the last heartbeat (`Elapsed Time` or a Tick Count shift
    register), call `Log Event` with code 90.
  - Stop terminal: the `stop all` global.
- After the loop: `Log Event` code 99, then `Flush Queue` (it returns all remaining elements). Write
  each remaining element in a For loop, then `Close File`, then `Release Queue` (force destroy = TRUE).
- No file writes for this file anywhere else.

### Step 3. Case transitions (main state-machine loop)

- Add a shift register `previous state` (initialised to -1).
- After the case structure, where the next state is known: if `next state != previous state`, call
  `Log Event` (code 2, value = next state). Feed next state into `previous state`.
- This logs only real transitions, not every iteration of Case 0.
- Add the explicit markers inside the cases:
  - Case 2: `Log Event` code 3, wired by error cluster right after the `TRIAL` write.
  - Case 4: `Log Event` code 4, right after the `REWARD` write (before or after `Set Occurrence`
    doesn't matter, but keep it next to the REWARD write).
  - Case 3: `Log Event` code 5 in the branch where the movement window times out.

### Step 4. Water loop

In the occurrence-received sequence, put one `Log Event` in each relevant frame, **after** that frame's
DAQmx write or wait. Chain it with the error wire so dataflow forces the order (codes 10-18 from the
table). Use the actual wired values for the `value` inputs: extend V, water ms, retract V.

### Step 5. Magnet loop

After the AO write of `mag`: code 20 (value = `mag`). After the AO write of 0: code 21.

### Step 6. Save, run, commit

Save both VIs and confirm the run arrow is unbroken. Commit the VIs together with this file's status
notes in `.cursorrules`.

## Bench validation (no animal)

Use `parameters/push_bench_full-system.txt`. Start the camera recording too, so the alignment can be
checked. Run about 5 minutes:

1. Withhold the rest pad for about 20 s, so only heartbeats should appear.
2. Trigger rest-pad initiation, then do NOT push: one timeout trial (expect 2->1->2->3->0 with codes
   3 and 5).
3. Complete 3-4 successful trials (codes 3, 4, then 10-18 each time).
4. Once, press the FSR clearly in view of the camera (a visual sync check).
5. Stop normally, then a second time stop from inside a reward sequence.

Then check (this can be done on the Mac with Python):

- The file size is a multiple of 32 bytes; it starts with code 1 and ends with code 99.
- The sample index and Unix time never decrease (over the writer's records sorted by time, both are
  monotonic; the interleaving order of records in the file may differ slightly).
- Number of code-3 events == `TRIAL` rows, and each code-3 `sample_index` == the `TRIAL` column 2 value.
- Number of code-4 events == `REWARD` rows, and each code-4 `sample_index` == the `REWARD` column 0 value.
- One full 10-18 sequence per success, in order.
- Heartbeats about 1 s apart. A linear fit of `unix_time` vs `sample_index` over heartbeats should have
  a slope of about 0.001 s/sample and residuals of a few ms at most (this measures Windows clock
  resolution and loop jitter).
- No -200279 error on Stop; the joystick file is still exactly records x 5 doubles.

## Send back to the Mac

- The new bench files (`joystick_`, `TRIAL_`, `REWARD_`, `EVENTS_`, the camera `TIMESTAMPS_VIDEO_*.npy`
  and the video), plus the parameter file used.
- Screenshots: `Log Event.vi` block diagram, the writer loop, the transition logic, one water-loop frame
  with its log call, and the magnet loop.
- Which sample counter was used (step 0), and any code placed somewhere other than the table says.

## Not part of this step

- `SETTINGS_<name>.txt` (front-panel values at session start): separate, small follow-up.
- `make_labview_timing.py` (EVENTS -> `TIMESTAMPS_LABVIEW_*.npy` from code 4): written on the Mac after
  the bench files arrive.
- Any DataJoint change. The pipeline side (`push` schema, GUI field for the EVENTS file) is planned in the
  DataJoint repo and only starts once this file format is validated.
