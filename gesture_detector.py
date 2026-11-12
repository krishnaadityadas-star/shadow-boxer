import time

import cv2
import mediapipe as mp


class GestureDetector:
    """
    Webcam-based gesture detector for Shadow-Boxer.

    Public API:
        detector = GestureDetector()
        gesture = detector.update()   # LEFT, RIGHT, JUMP, DUCK, NEUTRAL
        detector.calibrate()          # call when the player presses C
        detector.close()              # call when the game exits

    LOW VISIBILITY and NO BODY DETECTED are exposed through `status`,
    while update() returns NEUTRAL for those cases so the game does not
    keep moving based on an unreliable pose.
    """

    LEAN_THRESHOLD = 0.04
    VISIBILITY_THRESHOLD = 0.5

    CROUCH_THRESHOLD = 0.15
    CROUCH_RELEASE_THRESHOLD = 0.08

    SMOOTHING_FACTOR = 0.25

    # Selected pose connections used by the optional debug preview.
    CONNECTIONS = [
        (11, 12),
        (11, 13), (13, 15),
        (12, 14), (14, 16),
        (11, 23), (12, 24),
        (23, 24),
        (23, 25), (25, 27),
        (24, 26), (26, 28),
        (27, 29), (29, 31),
        (28, 30), (30, 32),
    ]

    def __init__(
        self,
        camera_index=0,
        model_path="models/pose_landmarker_lite.task",
        show_preview=False,
    ):
        self.show_preview = show_preview

        self.baseline_hip_y = None
        self.baseline_torso_height = None
        self.crouch_active = False

        self.smoothed_difference = None
        self.current_hip_center_y = None
        self.current_torso_height = None

        self.status = "STARTING"
        self.last_frame = None
        self.last_lean_difference = None
        self.is_calibrated = False

        self._start_time = time.monotonic()
        self._closed = False

        base_options = mp.tasks.BaseOptions(
            model_asset_path=model_path
        )

        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_poses=1,
        )

        self.detector = mp.tasks.vision.PoseLandmarker.create_from_options(
            options
        )

        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            self.detector.close()
            self._closed = True
            raise RuntimeError("Could not open webcam.")

    def _draw_pose(self, frame, landmarks):
        height, width, _ = frame.shape

        for start, end in self.CONNECTIONS:
            p1 = landmarks[start]
            p2 = landmarks[end]

            if (
                p1.visibility is not None
                and p2.visibility is not None
                and p1.visibility > self.VISIBILITY_THRESHOLD
                and p2.visibility > self.VISIBILITY_THRESHOLD
            ):
                x1, y1 = int(p1.x * width), int(p1.y * height)
                x2, y2 = int(p2.x * width), int(p2.y * height)

                cv2.line(
                    frame, (x1, y1), (x2, y2),
                    (0, 255, 0), 2
                )

        for point in landmarks:
            if (
                point.visibility is not None
                and point.visibility > self.VISIBILITY_THRESHOLD
            ):
                x = int(point.x * width)
                y = int(point.y * height)
                cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)

    def calibrate(self):
        """
        Save the most recent reliable standing measurements as baseline.
        Call this after the player stands upright and presses C.
        """
        if (
            self.current_hip_center_y is None
            or self.current_torso_height is None
            or self.current_torso_height <= 0
        ):
            return False

        self.baseline_hip_y = self.current_hip_center_y
        self.baseline_torso_height = self.current_torso_height
        self.crouch_active = False
        self.is_calibrated = True

        print("Standing position calibrated!")
        return True

    def update(self):
        """
        Read one webcam frame, detect pose and return one game gesture.

        Possible return values:
            LEFT, RIGHT, JUMP, DUCK, NEUTRAL
        """
        if self._closed:
            raise RuntimeError("GestureDetector is already closed.")

        success, frame = self.cap.read()

        self.current_hip_center_y = None
        self.current_torso_height = None
        self.last_lean_difference = None

        if not success:
            self.status = "CAMERA ERROR"
            self.last_frame = None
            return "NEUTRAL"

        frame = cv2.flip(frame, 1)
        self.last_frame = frame.copy()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )

        timestamp_ms = int(
            (time.monotonic() - self._start_time) * 1000
        )

        result = self.detector.detect_for_video(mp_image, timestamp_ms)

        game_gesture = "NEUTRAL"
        self.status = "NO BODY DETECTED"

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]

            if self.show_preview:
                self._draw_pose(frame, landmarks)

            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_hip = landmarks[23]
            right_hip = landmarks[24]

            required_points = [
                left_shoulder,
                right_shoulder,
                left_hip,
                right_hip,
            ]

            reliable = all(
                point.visibility is not None
                and point.visibility >= self.VISIBILITY_THRESHOLD
                for point in required_points
            )

            if reliable:
                shoulder_center_x = (
                    left_shoulder.x + right_shoulder.x
                ) / 2

                hip_center_x = (
                    left_hip.x + right_hip.x
                ) / 2

                raw_difference = shoulder_center_x - hip_center_x

                if self.smoothed_difference is None:
                    self.smoothed_difference = raw_difference
                else:
                    self.smoothed_difference = (
                        self.SMOOTHING_FACTOR * raw_difference
                        + (1 - self.SMOOTHING_FACTOR)
                        * self.smoothed_difference
                    )

                self.last_lean_difference = self.smoothed_difference

                left_wrist = landmarks[15]
                right_wrist = landmarks[16]

                wrists_visible = (
                    left_wrist.visibility is not None
                    and right_wrist.visibility is not None
                    and left_wrist.visibility >= self.VISIBILITY_THRESHOLD
                    and right_wrist.visibility >= self.VISIBILITY_THRESHOLD
                )

                shoulder_center_y = (
                    left_shoulder.y + right_shoulder.y
                ) / 2

                hip_center_y = (
                    left_hip.y + right_hip.y
                ) / 2

                torso_height = hip_center_y - shoulder_center_y

                self.current_hip_center_y = hip_center_y
                self.current_torso_height = torso_height

                is_crouching = False

                if (
                    self.baseline_hip_y is not None
                    and self.baseline_torso_height is not None
                    and self.baseline_torso_height > 0
                ):
                    hip_drop = hip_center_y - self.baseline_hip_y
                    normalized_hip_drop = (
                        hip_drop / self.baseline_torso_height
                    )

                    # Keep the tested hysteresis thresholds unchanged.
                    if self.crouch_active:
                        self.crouch_active = (
                            normalized_hip_drop
                            > self.CROUCH_RELEASE_THRESHOLD
                        )
                    else:
                        self.crouch_active = (
                            normalized_hip_drop
                            > self.CROUCH_THRESHOLD
                        )

                    is_crouching = self.crouch_active

                else:
                    self.crouch_active = False

                both_hands_raised = (
                    wrists_visible
                    and left_wrist.y < left_shoulder.y
                    and right_wrist.y < right_shoulder.y
                )

                # Preserve the original gesture priority.
                if both_hands_raised:
                    game_gesture = "JUMP"
                elif is_crouching:
                    game_gesture = "DUCK"
                elif self.last_lean_difference < -self.LEAN_THRESHOLD:
                    game_gesture = "LEFT"
                elif self.last_lean_difference > self.LEAN_THRESHOLD:
                    game_gesture = "RIGHT"
                else:
                    game_gesture = "NEUTRAL"

                self.status = game_gesture

            else:
                self.crouch_active = False
                self.status = "LOW VISIBILITY"

        else:
            self.smoothed_difference = None
            self.crouch_active = False

        if self.show_preview:
            cv2.putText(
                frame,
                "Gesture: " + self.status,
                (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            calibration_text = (
                "Calibrated" if self.is_calibrated
                else "Press C in game to calibrate"
            )

            cv2.putText(
                frame,
                calibration_text,
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2,
            )

            cv2.imshow("Shadow-Boxer - Gesture Preview", frame)

        return game_gesture

    def close(self):
        """Release the webcam and MediaPipe resources."""
        if self._closed:
            return

        self.cap.release()
        self.detector.close()

        if self.show_preview:
            cv2.destroyWindow("Shadow-Boxer - Gesture Preview")

        self._closed = True
        print("Gesture detector closed.")
