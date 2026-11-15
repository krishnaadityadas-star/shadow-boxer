# Shadow-Boxer 🥊

**Shadow-Boxer** is a webcam-controlled 2D fighting game built with Python, OpenCV, MediaPipe Pose Landmarker and Pygame. Players use body gestures to move and fight, with keyboard controls available as an alternative.

## Project overview

- **Track:** Beginners
- **Team size:** 3
- **Status:** Functional, integrated MVP; final gameplay refinements and submission preparation in progress (15 November 2026)
- **Processing pipeline:** Webcam → OpenCV → MediaPipe Pose Landmarker (Tasks API) → gesture recognition → Pygame

## Features

- Live webcam capture and body-pose landmark detection.
- Six webcam actions: move left, move right, jump, duck, punch and block.
- Standing-position calibration and on-screen gesture feedback, including chest-guard readiness.
- Forward punches toward the webcam, with chest-guard rearming to avoid repeated triggers while holding a pose.
- **SWEEP** low attack by crouching and punching together.
- Keyboard controls for movement, combat and calibration; an optional webcam overlay and on-screen buttons.
- Player-versus-bot fighting gameplay, including health, rounds and visual effects.

## Controls

### Webcam gestures

| Your movement | In-game action |
| --- | --- |
| Lean left | Move left |
| Lean right | Move right |
| Raise both hands | Jump |
| Crouch | Duck |
| Move **right fist** from chest guard into a punch **toward the webcam** | Punch (one action per detected punch; return fist to chest guard to rearm) |
| Raise **left fist** near the chin in the blocking pose | Block |
| Crouch and perform the right-arm punch | SWEEP low attack |

**Calibration:** Stand upright facing the camera, with your shoulders and hips visible, then press **C**. Bring your right fist to chest guard before attempting a webcam punch. The gesture status display helps indicate when the guard is ready.

### Keyboard controls

| Key | Action |
| --- | --- |
| `A` / Left arrow | Move left |
| `D` / Right arrow | Move right |
| `W` / Up arrow / Space | Jump |
| `S` / Down arrow | Duck |
| `Q` | Punch |
| `E` | Block |
| Hold `S`, then press `Q` | SWEEP low attack |
| `C` | Calibrate standing position (with active webcam) |
| `Enter` | Start / restart round |
| `F2` | Toggle webcam overlay |
| `F3` | Toggle on-screen buttons |
| `Esc` | Quit |

## Installation and launch

**Requirements:** Python, a functioning webcam for gesture control, and the dependencies in `requirements.txt`. Keyboard gameplay can serve as a fallback when camera detection is unavailable. Commands below are run from the repository's root folder (containing `shadow_boxer_mvp.py`).

### 1. Download the project

Clone the project's GitHub repository or download it as a ZIP and extract it. If cloning, copy the actual clone URL from the repository page:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Open a terminal in the extracted/cloned project folder before following the next steps.

### 2. macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python shadow_boxer_mvp.py
```

You can also use `run.sh` if its interpreter selection matches your environment. Running `python shadow_boxer_mvp.py` from the activated environment is the most direct option.

### 3. Windows (Command Prompt)

Open the project folder in File Explorer, click the address bar, type `cmd`, and press Enter. Then run:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python shadow_boxer_mvp.py
```

These Windows steps were used during Tusar's baseline testing with Python 3.12.4. For more details, see [Windows setup and project guide](docs/tusar/PROJECT_AND_WINDOWS_SETUP.md).

### 4. Check the pose model and camera

The project folder must contain:

```text
models/pose_landmarker_lite.task
```

Allow camera access if your operating system requests permission. Use a well-lit space, and stand far enough from the webcam for your upper body and relevant landmarks to be visible.

### 5. Start playing

1. Run `python shadow_boxer_mvp.py`.
2. Press `Enter` to start a round.
3. Stand normally and press `C` to calibrate.
4. Try the movement gestures, followed by right-arm PUNCH, left-arm BLOCK and SWEEP.
5. If camera tracking becomes unreliable, use the keyboard controls.

## Project structure

```text
Shadow-Boxer/
├── README.md
├── game.py                      # Original standalone Pygame game
├── shadow_boxer_mvp.py          # Integrated webcam-controlled game
├── gesture_detector.py         # MediaPipe pose and gesture recognition
├── pose_detection.py           # Separate pose-detection utility
├── models/
│   └── pose_landmarker_lite.task
├── requirements.txt
├── run.sh                       # macOS/Linux launcher
├── TEST_RESULTS.txt             # Recorded regression test summary
├── HOW_IT_WAS_MADE.txt
└── docs/
    ├── architecture.md
    ├── daily-progress.md
    └── tusar/
        ├── README.md
        ├── BASELINE_TEST_REPORT_2026-11-13.md
        ├── PROJECT_AND_WINDOWS_SETUP.md
        ├── DEMO_PLAN_AND_EVIDENCE.md
        ├── VALIDATION_UPDATE_2026-11-14.md
        └── original_docx/      # Original Word documents
```

`game.py` is Onkar's original game, while **`shadow_boxer_mvp.py` is the integrated game entry point**. The Pygame refinement being prepared separately should not be assumed included until it is reviewed and merged.

## Testing and verification

- **13 November — Tusar's Windows baseline:** The application launched, imports and model file were checked, all six tested keyboard actions worked, and the four original webcam movement gestures were reported working. A slight but playable webcam response delay was reported. Webcam PUNCH/BLOCK were **not yet verified in this older baseline**.
- **14 November — Combat integration:** Forward webcam PUNCH, repeated punching and chest-guard feedback were confirmed in live testing of the updated integrated game. The project's regression summary reports passing checks using **808 recorded webcam frames**, including forward punches, hip-lowering rejection and event delivery.
- **15 November — SWEEP:** Keyboard `S + Q` and webcam DUCK + PUNCH were confirmed working in live gameplay testing.

See [regression test results](TEST_RESULTS.txt), [Tusar's baseline report](docs/tusar/BASELINE_TEST_REPORT_2026-11-13.md) and [combat validation update](docs/tusar/VALIDATION_UPDATE_2026-11-14.md). The baseline report and demo plan describe an earlier build; their historical limitations should not be mistaken for the status of the newer tested integration.

**Not fully verified:** Touch-control compatibility, varied lighting/camera placements, long-duration stability, and final integration of Onkar's refinements. The project has been tested on individual machines, not exhaustively across operating systems.

## Team contributions

- **Krishna:** OpenCV/MediaPipe integration, gesture recognition, combat controls, calibration, debugging, webcam-to-Pygame event handling, and final integration.
- **Onkar:** Original Pygame game, gameplay mechanics, graphics, interface, and player controls; additional refinements pending integration.
- **Tusar:** Independent Windows setup/testing, regression observations, documentation, Windows setup guide, and demo preparation.

## Documentation and demo

- [Project architecture](docs/architecture.md)
- [Development progress](docs/daily-progress.md)
- [Tusar's documentation index](docs/tusar/README.md)
- [Demo plan and evidence checklist](docs/tusar/DEMO_PLAN_AND_EVIDENCE.md)

## Project goal

To demonstrate how real-time computer vision and body-pose detection can create an interactive fighting game without requiring a traditional physical controller.
