# Architecture

## Data flow

1. **Webcam:** captures frames.
2. **OpenCV:** reads and prepares frames for processing.
3. **MediaPipe Pose:** estimates body landmarks.
4. **Feature extraction:** derives simple normalized measurements from landmarks.
5. **Gesture recognition:** applies transparent rules to classify a small set of gestures.
6. **Smoothing and cooldowns:** reduce flicker and repeated actions.
7. **Pygame:** converts recognized actions into game controls and renders the game.

## Design principles
- Start with one gesture and prove the full pipeline.
- Prefer clear rule-based recognition for the first version.
- Handle missing or low-confidence landmarks safely.
- Keep camera processing separate from game logic.
- Show the current detected gesture so debugging is easier.

## Initial module idea
- `camera.py` — webcam capture
- `pose_detector.py` — pose landmarks
- `gestures.py` — feature extraction and gesture rules
- `game.py` — Pygame game
- `main.py` — connects the components

These are proposed names; create them when implementation begins.
