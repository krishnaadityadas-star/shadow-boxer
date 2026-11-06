# Shadow-Boxer

A beginner-friendly hackathon project: use webcam-based body-pose detection to control a simple 2D game.

## Project direction
- Track: Beginners
- Team size: 3
- Core pipeline: Webcam → OpenCV → MediaPipe Pose → gesture rules → Pygame

## MVP
1. Capture webcam video.
2. Detect body landmarks with a pretrained pose model.
3. Convert a small set of body movements into game actions.
4. Control a simple 2D game.
5. Display the camera feed, pose landmarks, and detected action.

The proposed gestures (lean left/right, raise both hands, crouch) must be tested and adjusted. They are not yet implemented.

## Suggested tools
Python, OpenCV, MediaPipe, Pygame, Git and GitHub.

See `docs/` for planning, architecture, learning and progress notes.
