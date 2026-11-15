# Shadow-Boxer — Demo Plan, Feature Checklist & Evidence Guide

**Prepared by:** Tushar (14 November 2026)
**Integration update:** 15 November 2026 (reflecting Krishna's later working webcam PUNCH test)

> The original demo plan is preserved in [`original_docx/`](original_docx/). The older plan did not include verified webcam combat gestures because its source snapshot predated the successful forward-punch test. This version updates the **demonstration plan**, not the historical Windows test results.

## 1. Demo objective

In approximately **3–4 minutes**, show the integrated game, its keyboard fallback, webcam movement and combat gestures, and the relationship between pose landmarks and in-game actions. Do not present untested features as proven.

## 2. Suggested demo sequence

| Time | Segment | What to show |
|---|---|---|
| 0:00–0:25 | Introduction | Shadow-Boxer is a 2D fighting game controlled by webcam body gestures. |
| 0:25–0:55 | Launch | Run `python shadow_boxer_mvp.py`, show title/game window. |
| 0:55–1:35 | Keyboard fallback | Demonstrate A/D, W/S, Q/E. If verified in final run, demonstrate S + Q SWEEP. |
| 1:35–2:55 | Webcam controls | Press C to calibrate. Demonstrate LEFT, RIGHT, JUMP, DUCK, then right-arm **forward PUNCH** with `GUARD READY` / `PUNCH DETECTED` feedback. Demonstrate left-arm BLOCK only after confirming it in the final build. |
| 2:55–3:25 | Technology | Explain webcam → OpenCV → MediaPipe → gesture logic → Pygame. |
| 3:25–4:00 | Closing | Summarize what was verified and honestly mention lighting/latency and testing limits. |

## 3. Feature validation checklist before filming

| Feature | Evidence status | Demo action |
|---|---|---|
| Game starts on Windows | Reported PASS by Tushar (13 Nov baseline) | Launch final version on demo laptop |
| Keyboard A/D/W/S/Q/E | Reported PASS by Tushar (13 Nov baseline) | Demonstrate briefly |
| Webcam LEFT / RIGHT / JUMP / DUCK | Reported PASS by Tushar (13 Nov baseline) | Show all four |
| Right-arm forward PUNCH | **Confirmed live by Krishna on newer Mac build (14 Nov)** | Show chest guard then forward punch |
| Punch-event queue and guard feedback | Confirmed by Krishna in newer build | Point out `GUARD READY` and detected punch feedback |
| Left-arm webcam BLOCK | Implemented in newer code; independent final regression pending | Test before demonstrating |
| SWEEP (crouch + punch) | Implemented in Pygame; final test pending | Do not claim tested until demonstrated |
| Touch input | Not tested by Tushar | Omit unverified claim |
| Long play / varied lighting | Not adequately tested | Describe limitation |

## 4. Capture the following evidence

1. Game title screen and control instructions.
2. Active gameplay, health display and opponent.
3. Webcam overlay showing detected pose/gesture feedback.
4. Gesture indicator for movement or jump/duck.
5. `GUARD READY` followed by successful webcam forward PUNCH.
6. If confirmed in final run, BLOCK and SWEEP gameplay.
7. One short **continuous** demonstration video showing calibration and visible game response.

Store media locally in a folder such as `Shadow-Boxer-Demo-Evidence/`. Include relevant screenshots/video in the final submission only if your team chooses to publish them.

## 5. Pre-demo reliability checks

- Plug in laptop power and close competing camera apps.
- Confirm camera permission and good lighting; include shoulders and hips in view.
- Open the project root with the MediaPipe model available in `models/`.
- Activate the correct virtual environment and run `python shadow_boxer_mvp.py`.
- Calibrate using C before demonstrating gestures.
- Check keyboard fallback and perform one full rehearsal.
- Preserve the working `gesture_detector.py` and `shadow_boxer_mvp.py`; do not install an experimental punch build just before the demo.

## 6. Short explanation for judges

> Shadow-Boxer is a gesture-controlled 2D fighting game. OpenCV captures webcam frames, MediaPipe estimates body landmarks, and our gesture rules translate body movements into game controls. Pygame renders the match and processes movement and combat actions. We also provide keyboard controls as a fallback. After repeated testing, we successfully demonstrated punches directed toward the camera using guard-based detection and event handling.

## 7. Limitations and evidence notes

- A slight playable webcam response delay was reported in Tushar's 13 November baseline; latency was not measured.
- Tracking depends on visibility, framing and lighting.
- The 13 November Windows baseline did **not** test webcam PUNCH/BLOCK. The later successful forward-punch demo was confirmed separately by Krishna.
- Touch controls and longer-term stability were not comprehensively tested.
- Keep claims about Omkar's final game refinement separate until it has been integrated and tested.

## 8. Handoff

Tushar's deliverables: baseline report, project/Windows guide, demo plan, and available evidence. Krishna is responsible for final GitHub integration and release approval. See the [documentation index](README.md) for sources and status.
