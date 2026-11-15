> **Historical baseline — 13 November 2026 (commit `e9f0a58`).** This document transcribes Tushar's original Windows testing report. The words **PASS — reported** describe observations rather than automated instrumentation. Do not reinterpret these as validation of the newer webcam combat build. For subsequent work, see [the 14 November validation update](VALIDATION_UPDATE_2026-11-14.md).

**SHADOW-BOXER
BASELINE TESTING REPORT**

*Independent testing record — Tushar*

| **Test date**           | 13 November 2026                                              |
|-------------------------|---------------------------------------------------------------|
| **Test platform**       | Windows (Python 3.12.4)                                       |
| **Repository snapshot** | GitHub repository shadow-boxer; visible latest commit e9f0a58 |

# 1. Test environment and setup

- Downloaded the repository as a ZIP from GitHub and extracted it locally. No changes were made to the shared GitHub repository.

- Created and activated a local virtual environment named .venv.

- Installed packages using: python -m pip install -r requirements.txt

- Verified imports for OpenCV, MediaPipe, Pygame and NumPy; the import check completed successfully.

- Verified that models\pose_landmarker_lite.task exists (5,777,746 bytes).

- Launched the application using: python shadow_boxer_mvp.py

# 2. Keyboard control results

| **Control** | **Expected result** | **Actual result** | **Status** |
|-------------|---------------------|-------------------|------------|
| A           | Move left           | Reported working  | PASS       |
| D           | Move right          | Reported working  | PASS       |
| W           | Jump                | Reported working  | PASS       |
| S           | Duck                | Reported working  | PASS       |
| Q           | Punch               | Reported working  | PASS       |
| E           | Block               | Reported working  | PASS       |

# 3. Webcam and gesture results

| **Test**                 | **Actual result**                                                        | **Status / notes**                                   |
|--------------------------|--------------------------------------------------------------------------|------------------------------------------------------|
| Webcam activation        | Webcam feed became active during game testing.                           | PASS — reported                                      |
| Calibration              | Calibration was performed after pressing C.                              | Performed; exact on-screen confirmation not recorded |
| Lean left (LEFT)         | Reported working.                                                        | PASS — reported                                      |
| Lean right (RIGHT)       | Reported working.                                                        | PASS — reported                                      |
| Both hands raised (JUMP) | Reported working.                                                        | PASS — reported                                      |
| Crouch (DUCK)            | Reported working.                                                        | PASS — reported                                      |
| Response delay           | Slight delay; user selected the 'slight delay but playable' description. | Observation; not a failure                           |

# 4. Stability and additional tests

| **Area**                                                                                | **Result**                                                                                                        |
|-----------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| Continuous-play observation                                                             | Approximately 2 minutes of play was reported.                                                                     |
| Freezing / webcam disconnection / accidental detections / repeated movements / slowdown | User reported no problems in response to the stability check. Detailed individual measurements were not recorded. |
| Touch controls                                                                          | NOT TESTED.                                                                                                       |
| Different lighting and camera positions                                                 | NOT TESTED / not documented.                                                                                      |
| Long-duration stability                                                                 | NOT TESTED.                                                                                                       |

# 5. Summary

The application was successfully launched on the tester's Windows computer. The local Python environment, core package imports and MediaPipe model file were verified. All six keyboard controls and the four baseline webcam gestures were reported working. A slight webcam response delay was observed, described as playable. The short stability observation did not reveal reported problems. Touch controls remain untested.

# 6. Issues and recommendations for Krishna

- Note the slight webcam gesture-response delay for further evaluation; no measured latency value was collected.

- Arrange a separate touch-control test before claiming touch compatibility is verified.

- If time permits, repeat gesture tests under different lighting and camera distances and record any false detections or conflicts.

- PUNCH and BLOCK were exercised through keyboard keys Q and E only. This report does not validate any webcam-based PUNCH or BLOCK gestures.

# 7. Evidence and reporting limitations

Results in this report are based on the tester's verbal observations during the session. No video recording, screenshots of each individual test, measured latency, or automated test logs were supplied. A 'PASS — reported' status means the tester stated that the control worked; it is not an instrumented measurement.

**Prepared by: Tushar — Testing, Validation and Documentation**
