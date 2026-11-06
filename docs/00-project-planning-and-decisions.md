# Project Planning and Decisions

## Project
**Shadow-Boxer — Full-Body Kinetic Controller**

## Goal
Build a small game that a player can control using body movements captured by a webcam.

## Track and constraints
- Track: Beginners
- Team: 3 members
- Build window: 10 days
- Prioritize a reliable working MVP over optional features.

## MVP scope
- Webcam input.
- Pretrained pose detection.
- A few rule-based gestures.
- A simple Pygame game.
- Basic on-screen feedback showing the detected gesture.

## Proposed gesture mapping (to test)
- Lean left/right → move left/right.
- Raise both hands → jump.
- Crouch → duck or slide.
- Neutral pose → no movement.

These mappings are hypotheses, not completed features. Test them with all teammates and tune thresholds.

## Suggested team split
- Teammate A: webcam capture and pose-detection pipeline.
- Teammate B: landmark features, gesture rules and smoothing.
- Teammate C: Pygame game and display/dashboard.

All members should understand the complete data flow and review one another's work.

## Working agreements
- Keep the MVP small.
- Commit working changes frequently.
- Test in realistic lighting and camera positions.
- Do not claim a feature works until it has been tested.
- Record decisions and blockers in the shared progress log.
