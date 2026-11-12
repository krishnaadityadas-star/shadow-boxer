# Shadow-Boxer 🥊

A webcam-based gesture-controlled 2D fighting game built using Python, OpenCV, MediaPipe and Pygame.

Shadow-Boxer allows players to control an in-game character using real-time body movements captured through a webcam.

## Project Overview

- **Track:** Beginners
- **Team Size:** 3
- **Status:** Functional MVP Completed
- **Core Pipeline:** Webcam → OpenCV → MediaPipe Pose → Gesture Recognition → Pygame

## MVP Features

- Real-time webcam capture using OpenCV.
- Body-pose detection using MediaPipe Pose Landmarker (Tasks API).
- Real-time body gesture recognition.
- Gesture-based player movement and actions.
- Standing-position calibration.
- Webcam preview and gesture-status feedback.
- Keyboard controls alongside webcam controls.

## Gesture Controls

| Body Gesture | Game Action |
|---|---|
| Lean left | Move left |
| Lean right | Move right |
| Raise both hands | Jump |
| Crouch | Duck |

### Keyboard Controls

| Key | Action |
|---|---|
| A / D | Move |
| W / Space | Jump |
| S | Duck |
| Q | Punch |
| E | Block |
| C | Calibrate standing position |
| F2 | Webcam overlay |
| F3 | On-screen buttons |
| ESC | Quit |

Punch and Block currently use keyboard controls. Gesture-based controls for these actions are planned for the next development phase.

## Project Structure

```text
Shadow-Boxer/
├── models/
│   └── pose_landmarker_lite.task
├── game.py
├── shadow_boxer_mvp.py
├── gesture_detector.py
├── run.sh
├── requirements.txt
├── HOW_IT_WAS_MADE.txt
├── daily-progress.md
├── README.md
└── .gitignore
```

- `game.py` — Original Pygame game developed by Onkar.
- `shadow_boxer_mvp.py` — Integrated gesture-controlled MVP.
- `gesture_detector.py` — Reusable webcam and gesture-recognition module.
- `models/` — Pretrained MediaPipe pose model.
- `run.sh` — Launch script for the integrated MVP.

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd Shadow-Boxer
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the actual repository URL.

### 2. Create a virtual environment

```bash
python3 -m venv shadowboxer-env
```

### 3. Activate the environment

**macOS / Linux:**

```bash
source shadowboxer-env/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the integrated MVP

```bash
bash run.sh
```

Ensure that your webcam is connected and available.

## Calibration

1. Launch the integrated MVP.
2. Stand upright and face the webcam.
3. Press **C** to calibrate your standing position.
4. Begin controlling the game using body gestures.

Recalibration may be required when restarting the application or changing camera position.

## Technology Stack

- Python
- OpenCV
- MediaPipe Pose Landmarker (Tasks API)
- Pygame
- NumPy
- Git and GitHub

## Team Contributions

- **Krishna:** OpenCV, MediaPipe integration, gesture recognition and integration with Pygame.
- **Tushar:** MediaPipe research, pose-landmark exploration and detection support.
- **Onkar:** Pygame development, game mechanics, graphics and player controls.

## Development Progress

The project has progressed from environment setup and independent component development to a working integrated MVP.

Completed:
- Webcam-based pose detection.
- Four body gestures.
- Gesture-to-game integration.
- Standing-position calibration.
- Keyboard and webcam control compatibility.
- End-to-end MVP testing.

Upcoming:
- Gesture-based Punch and Block controls.
- Improved graphics and animations.
- Gesture accuracy and responsiveness improvements.
- Cross-resolution and device testing.

See `daily-progress.md` and `docs/` for development records and project documentation.

## Project Goal

To demonstrate how computer vision and real-time body-pose detection can be used to create an interactive gaming experience without requiring traditional physical controllers.