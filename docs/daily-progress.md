# Daily Progress Log

Copy this template for each day.

## Date
### Completed
- 

### Demonstrated / tested
- 

### What we learned
- 

### Blockers
- 

### Next tasks
- Teammate A:
- Teammate B:
- Teammate C:

### Tomorrow's measurable deliverable
- 

---

## Initial status
- Project direction selected: Shadow-Boxer.
- Track selected: Beginners.
- Starter planning documents prepared.
- No implementation should be marked complete until it has been built and tested.

# Day 2 — November 6, 2026

### Completed
- Finalized Shadow-Boxer as our hackathon project.
- Created and organized our shared ChatGPT Project.
- Created the GitHub repository.
- Uploaded the README, .gitignore and project documentation.
- Organized the four documentation files inside the docs folder.
- Verified the repository structure.

### What we learned
- Basic GitHub repository structure.
- How to upload files and commit changes.
- How to organize files into folders using GitHub.

### Blockers
- Teammate invitations and collaborative GitHub workflow are still pending.
- No application code has been implemented yet.

### Tomorrow's tasks
- Invite both teammates to the GitHub repository.
- Verify that all three members can access it.
- Learn GitHub branches, commits, pushes and pulls.
- Begin the Python fundamentals required for the project.

### Tomorrow's measurable deliverable
All three teammates have repository access, understand the basic collaboration workflow, and have started the required Python preparation.

# Day 3 — 7 November 2026
## Shadow-Boxer: Development Progress

### Objective
Set up the Python development environment and verify that OpenCV, MediaPipe, and webcam connectivity are working correctly.

### Work Completed

**1. Python Environment Setup**
- Configured Python 3.12 for the project.
- Created a dedicated virtual environment named `shadowboxer-env`.
- Upgraded pip.
- Prepared an isolated environment for project dependencies.

**2. OpenCV Installation**
- Installed OpenCV successfully.
- Verified the installation and checked the installed version.
- Prepared OpenCV for webcam access and image processing.

**3. MediaPipe Installation**
- Installed MediaPipe successfully.
- Verified the installed version.
- Explored the available MediaPipe functionality.
- Identified that the installed version supports the newer Tasks API rather than the legacy Solutions API.

**4. Webcam Connectivity Test**
- Created a basic webcam testing script.
- Accessed the webcam through OpenCV.
- Successfully captured live webcam frames.
- Confirmed that the camera was working correctly within the Python environment.

### Team Contributions

**Krishna**
- Participated in Python environment configuration.
- Installed and verified OpenCV and MediaPipe.
- Worked on preparing the computer vision development environment.
- Coordinated the initial technical setup.

**Tushar**
- Participated in the initial environment setup.
- Assisted with installing and verifying OpenCV and MediaPipe.
- Helped test the webcam connection and verify camera functionality.

### Technologies Used
- Python 3.12
- OpenCV
- MediaPipe
- pip
- VS Code / Terminal

### Outcome
The initial development environment was successfully configured.

OpenCV and MediaPipe were installed and verified, and webcam connectivity was successfully tested.

**Status: Day 3 objectives completed.**

### Next Steps
- Explore MediaPipe Pose Landmarker.
- Understand body landmark detection.
- Implement real-time pose detection.
- Prepare for gesture-recognition development.

---

**Project:** Shadow-Boxer  
**Development Day:** 3  
**Date:** 7 November 2026

# Day 4 — 8 November 2026
## Shadow-Boxer: Development Progress

### Objective
Move from initial environment setup to implementation of real-time pose detection, body gesture recognition and Pygame game development.

---

### 1. Krishna — OpenCV and Gesture Integration

**Work completed:**

- Initialized MediaPipe Pose Landmarker using the Tasks API.
- Downloaded and configured `pose_landmarker_lite.task`.
- Integrated OpenCV webcam capture with MediaPipe.
- Implemented real-time pose detection.
- Added body landmark visualization using skeleton connections and landmark points.
- Extracted shoulder, wrist, hip, knee and ankle landmarks.
- Implemented shoulder and hip midpoint calculations.
- Added exponential smoothing for stable lean measurements.
- Successfully implemented left and right lean detection.
- Implemented jump detection using wrist positions relative to shoulders.
- Developed calibrated crouch detection using vertical hip displacement.
- Added C-key calibration for recording the standing baseline.

**Gesture recognition results:**

| Gesture | Status |
|---|---|
| Lean Left | Working |
| Lean Right | Working |
| Jump | Working |
| Duck | Working |
| Neutral | Working |

**Crouch detection improvement:**

The initial knee-angle approach required the user to stand sideways for reliable detection. This was unsuitable for natural front-facing gameplay.

After several rounds of testing and changes, the detection method was redesigned around calibrated hip displacement.

Current configuration:
- Activation threshold: `0.15`
- Release threshold: `0.08`
- Calibration key: `C`
- Normalization: Baseline torso height

The revised approach successfully detected comfortable front-facing crouching and returned to NEUTRAL when the user stood upright.

### 2. Tushar — MediaPipe and Pose Detection

**Work completed:**

- Explored MediaPipe Pose Landmarker.
- Investigated the available MediaPipe APIs.
- Identified that the installed version supports the Tasks API rather than the legacy Solutions API.
- Explored pose landmark detection and landmark visibility.
- Worked with model configuration and Pose Landmarker initialization.
- Investigated the body landmarks required for gesture detection.
- Supported the team's understanding of pose tracking and its technical requirements.

### 3. Onkar — Pygame Development

**Work completed:**

- Set up and tested Pygame.
- Successfully launched the game window.
- Created an initial player object using a blue rectangle.
- Implemented initial W and S keyboard-based movement.
- Started improving the game's graphics and visual appearance.
- Worked on adapting the game to laptop and mobile screen resolutions.
- Continued developing the game-side foundation for future gesture integration.

---

### 4. Technologies Used

- Python 3.12
- OpenCV
- MediaPipe Tasks API
- MediaPipe Pose Landmarker
- NumPy
- Pygame
- VS Code
- Webcam

### 5. Major Challenges and Solutions

**Challenge 1: MediaPipe API Compatibility**

The legacy Solutions API was unavailable in the installed MediaPipe version.

**Solution:** Explored and implemented the newer Tasks API and successfully initialized Pose Landmarker.

**Challenge 2: Front-Facing Crouch Detection**

The initial knee-angle method was unreliable when facing the webcam directly.

**Solution:** Replaced the approach with calibrated vertical hip displacement, normalized using torso height.

**Challenge 3: Gesture Stability**

Small landmark fluctuations affected lean measurements.

**Solution:** Introduced exponential smoothing and separate crouch activation and release thresholds.

**Challenge 4: Game and Gesture Integration**

The computer-vision and Pygame components were being developed separately.

**Solution:** Established a reusable gesture-detection module as the next integration step.

### 6. Milestones Achieved

- [x] MediaPipe Pose Landmarker initialized.
- [x] Live webcam pose detection working.
- [x] Skeleton and landmark visualization working.
- [x] Left lean recognition implemented.
- [x] Right lean recognition implemented.
- [x] Jump recognition implemented.
- [x] Front-facing crouch recognition implemented and tested.
- [x] Standing-position calibration implemented.
- [x] Pygame environment configured.
- [x] Initial game window and player object created.
- [x] Initial keyboard movement implemented.

### 7. Pending Work

- Connect gesture recognition with Pygame.
- Implement direct player movement through body gestures.
- Integrate jumping and ducking actions.
- Add calibration to the gameplay startup process.
- Perform end-to-end testing.
- Complete the first MVP.

### 8. Overall Status

**Day 4 objectives substantially completed.**

The computer-vision component can recognize all four proposed body gestures, and the Pygame component has its initial game foundation.

The next major milestone is integrating both components into one working application.

---

**Project:** Shadow-Boxer  
**Development Day:** 4  
**Date:** 8 November 2026
