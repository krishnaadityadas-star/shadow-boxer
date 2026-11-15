# Shadow-Boxer — Project Documentation & Windows Setup Guide

**Prepared by:** Tushar (Testing, Validation and Documentation)
**Source document date:** 14 November 2026
**Integration update:** 15 November 2026, based on the team's later confirmed working combat version

> This readable GitHub guide updates Tushar's 14 November project documentation to distinguish his **13 November Windows baseline** from Krishna's **14 November combat integration**. The unmodified source DOCX is preserved in [`original_docx/`](original_docx/). The newer combat version has **not** been independently retested on Windows in the original baseline report.

## 1. Project overview

Shadow-Boxer is a webcam-controlled 2D fighting game created with **Python, OpenCV, MediaPipe Pose Landmarker (Tasks API), and Pygame**.

`Webcam → OpenCV → MediaPipe pose landmarks → Gesture recognition → Pygame actions and rendering`

A keyboard is supported as an alternative to the webcam. The integrated entry point is **`shadow_boxer_mvp.py`**, not the original standalone `game.py`.

## 2. Current feature status

| Feature | Implementation / evidence |
|---|---|
| Pygame player-versus-bot game, health, rounds, effects | Present in integrated game code |
| LEFT / RIGHT / JUMP / DUCK via webcam | Reported working in Tushar's Windows baseline (13 Nov) |
| Standing-position calibration via `C` | Available; performed in baseline (confirmation message not recorded in that test) |
| Keyboard A / D / W / S / Q / E | All reported working by Tushar (13 Nov) |
| Right-arm webcam **PUNCH** | Implemented in later build; **Krishna confirmed successful live forward punches and repeated punches on 14 Nov** |
| Left-arm webcam **BLOCK** | Implemented in later build; separate final-build Windows regression still needed |
| Chest guard and punch-event preservation | Implemented in later build; Krishna confirmed guard-readiness feedback and punch registration |
| Crouch + PUNCH → SWEEP | Mechanic present in game code; final combined-control behavior not yet independently confirmed |
| Touch controls | Present in code; **not tested** in Tushar baseline |
| Long-duration / varied-lighting stability | **Not fully tested** |

See [the baseline testing report](BASELINE_TEST_REPORT_2026-11-13.md) and [the newer validation update](VALIDATION_UPDATE_2026-11-14.md). Do not use the 13 November report to claim Tushar tested webcam PUNCH or BLOCK.

## 3. Controls

| Input | Action | Notes |
|---|---|---|
| A / Left Arrow | Move left | Keyboard |
| D / Right Arrow | Move right | Keyboard |
| W / Up Arrow / Space | Jump | Keyboard |
| S / Down Arrow | Duck | Keyboard |
| Q | Punch | Keyboard; crouch + punch invokes sweep logic |
| E | Block | Keyboard |
| C | Calibrate standing pose | Stand upright, facing camera |
| F2 | Toggle webcam preview | Keyboard |
| F3 | Toggle on-screen buttons | Keyboard |
| Enter | Start / restart | Keyboard |
| Esc | Quit | Keyboard |
| Lean torso left / right | Move left / right | Webcam |
| Raise both hands | Jump | Webcam |
| Crouch / lower body | Duck | Webcam |
| Extend **right arm from chest guard** | Punch | Webcam, later integrated version; aim toward camera |
| Raise **left arm near chin** | Block | Webcam, later integrated version |

The game horizontally flips the webcam preview before MediaPipe processing, so the detector has an explicit corrected arm mapping for the player's actual right and left arms.

## 4. Project file guide

| File | Role |
|---|---|
| `shadow_boxer_mvp.py` | Integrated Pygame application and webcam action handling |
| `gesture_detector.py` | Webcam capture, MediaPipe Pose Landmarker and gesture recognition |
| `game.py` | Original Pygame implementation developed by Onkar |
| `pose_detection.py` | Separate pose-detection/visualization utility, not the main launcher |
| `models/pose_landmarker_lite.task` | MediaPipe model required by detector |
| `requirements.txt` | Dependencies, including OpenCV, MediaPipe, Pygame and NumPy |
| `run.sh` | Shell launcher for macOS/Linux; **not** a Windows CMD launcher |
| `README.md` | Repository entry point and project overview |
| `HOW_IT_WAS_MADE.txt` | Build/process notes |
| `docs/` | Planning, architecture, progress and testing documents |

## 5. Windows setup (independently used by Tushar)

From the extracted project folder containing `shadow_boxer_mvp.py`, `requirements.txt`, and `models/`:

1. In File Explorer, open the project folder, enter `cmd` in the address bar, and press Enter.
2. Create a virtual environment (once):

   ```bat
   python -m venv .venv
   ```

3. Activate it:

   ```bat
   .venv\Scripts\activate
   ```

4. Install dependencies:

   ```bat
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

5. Confirm `models\pose_landmarker_lite.task` exists (Tushar's baseline model was 5,777,746 bytes).
6. Launch from the **project folder**:

   ```bat
   python shadow_boxer_mvp.py
   ```

7. Allow camera permissions if prompted; stand where the camera can see shoulders and hips; press **C** to calibrate, then **Enter** to start.
8. To leave the environment later, use `deactivate`.

Tushar's recorded setup was Windows with Python **3.12.4**; this is a tested environment, not a universal version requirement.

## 6. Architecture overview

1. **Camera:** OpenCV captures and flips webcam frames.
2. **Pose model:** MediaPipe Pose Landmarker estimates body landmark coordinates.
3. **Gesture features:** The detector computes torso, shoulder, hip, wrist and arm measurements.
4. **Action classification:** Gesture rules generate movement and combat actions; standing calibration supports body-relative measurements.
5. **Input handoff:** The main game merges recognized webcam actions with keyboard and touch input. The later build preserves brief PUNCH events for game-loop consumption.
6. **Gameplay:** Pygame updates fighter and bot states, collisions, effects and display.

## 7. Calibration and first use

- Use a well-lit area and a stable camera position.
- Open the integrated game and allow webcam access.
- Stand upright with shoulders and hips visible; press **C** to calibrate.
- Verify left/right lean, both-hands jump, and crouch.
- For the newer combat build, raise the right fist to chest guard, then punch **toward the webcam**; return to chest guard before another punch.
- Use the left-hand chin-level guard for BLOCK; test both arms before recording the demo.
- If camera actions are unreliable, keyboard controls remain available.

## 8. Known limitations and evidence boundaries

- Tracking depends on framing, lighting, occlusion and body-landmark visibility.
- Tushar observed a **slight but playable delay** on the baseline Windows version; there is no measured latency value.
- Tushar's baseline observation covered about **two minutes**, not long-duration stress testing.
- Webcam PUNCH/BLOCK were **not part of Tushar's 13 November verification**, even though the later implementation includes them.
- Touch interactions and varying device/lighting configurations have not been verified by his report.
- The sweep move exists in the code but final gameplay confirmation is pending.

## 9. Team contributions

- **Onkar:** Original Pygame mechanics, player controls and presentation; updated refinement deliverable handled separately.
- **Krishna:** OpenCV / MediaPipe integration, gesture logic, combat controls, debugging, and final repository integration.
- **Tushar:** Independent Windows testing, setup verification, project documentation, baseline report and demo planning.

*Source basis: Tushar's three 13–14 November DOCX reports, the team's confirmed 14 November working result, and review of the stable integrated Python files. Historical findings and later status are explicitly separated.*
