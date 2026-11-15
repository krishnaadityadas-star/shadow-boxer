# Shadow-Boxer — Combat Validation Update (14 November 2026)

**Status:** Later update to Tushar's historical testing documents.
**Source:** Krishna's reported successful live test; stable detector and integrated game code; `TEST_RESULTS.txt` from the locally committed regression report.
**Not performed by Tushar:** This is **not** an independent Windows verification of combat gestures.

## What changed after the 13 November Windows baseline

- The integrated detector recognizes **PUNCH** using the player's actual right arm and **BLOCK** using the actual left arm.
- Forward punches **toward the webcam** were successfully registered during Krishna's live test on 14 November; he also confirmed repeated punch registration and `GUARD READY` display.
- The integrated game retains short-lived punch actions for the main Pygame loop so they are not lost when camera and game frames do not align.
- The implementation that worked was retained; a later experimental **chin-level-only punch** alternative was **not** adopted.
- The game already contains a **crouch + punch = SWEEP** mechanic, but the final combined-input check remains pending.

## Recorded regression evidence

The team's locally committed `TEST_RESULTS.txt` (commit `0be2c39`) reports these checks as PASS:

| Check | Reported outcome |
|---|---|
| 808 actual webcam CSV frames | 2 forward punches |
| 10 seconds of steady chest guard | No punches |
| Chest guard followed by lifting / lowering to hip | No punches |
| Punch without preceding guard | No punches |
| Forward punches without MediaPipe world coordinates | 2 forward punches |
| Forward punches with foreshortened 2D arm | 2 forward punches |
| One-frame wrist occlusion | 2 forward punches |
| Guard followed by a sideways extension | 1 sideways punch |
| Game event preserved during hit stun | PASS, without duplicate |

These are recorded regression outcomes and are not a substitute for independent final-build cross-platform testing.

## Remaining final checks

- Independently rerun the final build on **Windows**.
- Confirm webcam **BLOCK** and **SWEEP** in the final integrated version.
- Check touch controls only if time allows; do not present them as tested otherwise.
- Record demo evidence after combining any updated Pygame work, without altering the stable gesture detector unless a verified regression necessitates it.

## Git references (local at preparation time)

- `fc9144c` — *Stabilize webcam punch detection and game integration*.
- `0be2c39` — *Add gesture regression test results*.

These were confirmed as **local commits** in Krishna's repository; they were not yet confirmed pushed to GitHub when this update was written.
