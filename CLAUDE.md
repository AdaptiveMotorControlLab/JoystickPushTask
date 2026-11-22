# JoystickPushTask: agent instructions

Head-fixed mouse 1D forelimb object-push task (LabVIEW + NI-DAQ rig, forked from the Mathis joystick-pull rig). This file holds only standing instructions. Project state, history, rig facts, decisions and test results live in `docs/PROJECT_PLAN.md`.

## Where things are
- `docs/PROJECT_PLAN.md`: living project record (status, known bugs, decisions, validation, session → parameter-file map). Read it first for any substantial task.
- `README.md` overview; `RIG_INVENTORY.md` DAQ channels, SCB-68A terminals, NI-MAX tasks; `MAGNET_COMMISSIONING.md` Ledex/PVA; `EVENTS_LOGGER_PLAN.md` EVENTS file format and event codes (a contract with the lab DataJoint pipeline: never renumber codes).
- `parameters/README.md`: column map and every parameter file. `calibration/`: water, joystick volts → mm, magnet current.
- `scripts/`: `make_labview_timing.py` (run at Stop via `run_timing.bat`), `check_row_mapping.py` (EVENTS vs parameter file). `arduino/touch_pad/`: rest-pad sketch. `mechanical/`, `simulations/ledex_femm/`: CAD and Ledex force models.
- `*.vi` at the root are binary LabVIEW files: they cannot be read or diffed. Work from the docs and the user's screenshots.
- Session data (rig PC only, not in the repo): `C:\Users\Mathis_Lab_1\Desktop\RIG1_DATA` (`joystick_`, `TRIAL_`, `REWARD_`, `EVENTS_`, `TIMESTAMPS_LABVIEW_` per session). EVENTS is the source of truth for trials and rewards.

## Before changing anything
- Read the relevant code and docs first (README, `RIG_INVENTORY.md`, `parameters/README.md`, the README of the folder you touch). Never invent file paths, APIs, channel names or test results.
- Traps that have caused bugs: push = Y = `ai1` (white) but goes in the parameter loader's **X** columns; lateral = X = `ai0` (red) goes in the **Y** columns. Forward push lowers the voltage. Home voltage drifts between sessions (re-centre home boxes on the measured rest).

## Project plan (`docs/PROJECT_PLAN.md`)
- Where it disagrees with older notes or other docs, the plan wins unless the code, git history or session data prove it stale; then fix the plan.
- Update it after each meaningful milestone and at the end of every substantial task. Replace stale items instead of appending logs. Keep it concise, accurate and in sync with the repo.
- Never mark anything verified, tested, bench-validated or fixed unless it was actually tested (by you with real output, or reported by the user; say which). Otherwise record it as built / pending test / unverified, with what is still to check.
- Write entries so a fresh agent can act on them: what, where, status, next step.
- Don't touch the plan for trivial questions, explanations or unrelated edits.
- The repo is public: no private chat, people's names, or purchasing/admin details in the plan, docs or commits.

## Safety rules (always)
- Class 3B 635 nm laser on `PFI3` / terminal 42: keep keyed OFF. Never toggle PFI3 blind. Do not touch the laser pulse nodes in the magnet loop.
- Never power the Ledex coil from AO0 (AO0 is only the 0–10 V command; PCIe-6321 AO limit ±5 mA).
- The 1 A inline fuse stays in the 12 V positive lead of the Bürkert/Ledex supply. The Bürkert has no Enable pin: unplug that supply before starting or stopping AO0. The magnet's reserved 12 V Goobay supply is for nothing else.
- Normal Stop only; toolbar Abort is emergency-only (skips cleanup frames and the auto timing file).
- Never press an animal's paw onto the pad. Keep `mag = 0` in every parameter file until the unperturbed task is stable and the LabVIEW magnet safety work is done.
- Never hand-edit `.vi` binaries or internal names. Never Git-merge independently edited `.vi` files; the repo copy is the canonical hierarchy.

## Working conventions
- Two machines share GitHub `master`: the rig PC (Windows, LabVIEW, hardware, data) and a Mac (docs, parameter files, Python, CAD). Before editing: `git fetch origin` and `git status`; pull if behind. If the branch is both ahead and behind, do not merge: ask.
- Never commit unless asked; never push without explicit permission. When asked, commit after each finished step as the existing git identity (`maxchalabi`), with an imperative one-sentence message ending in a period. **No co-author or tool-attribution trailers of any kind** (no `Co-Authored-By: Claude`, no Cursor trailer): commits show only the author.
- VIs are edited by hand in LabVIEW on the rig PC. Guide changes one small step at a time (which node, which wire, how to check it) and wait for the user's confirmation before the next step. Prefer parameter files, front-panel controls and Python scripts over diagram changes.
- Bench-test everything animal-free first; change one variable at a time; no improvised circuit changes during an animal session.
- Validate parameter files after every edit: exact row count, tab-separated, the same column count on every row (27 base; 28–31 with the optional `vel threshold`, `reward on touch`, `joystick only`, `repeat trials`), consistent row definition, `mag` = 0, CRLF line endings like the existing files.
- Rig constraints: never run two AI tasks at once (one AI timing engine); keep the acquisition `Read` at 10 samples (not 100); do not upgrade the rig PC's Python 3.6.4 or numpy (`C:\Users\Mathis_Lab_1\AppData\Local\Programs\Python\Python36-32\python.exe`; `make_labview_timing.py` depends on it). Use a throwaway venv for plotting.
