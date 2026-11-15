import time
import math

import cv2
import mediapipe as mp


class GestureDetector:
    """
    Webcam-based gesture detector for Shadow-Boxer.

    Public API:
        detector = GestureDetector()
        gesture = detector.update()   # primary detected action
        detector.calibrate()          # call when the player presses C
        detector.close()              # call when the game exits

    LOW VISIBILITY and NO BODY DETECTED are exposed through `status`,
    while update() returns NEUTRAL for those cases so the game does not
    keep moving based on an unreliable pose.
    """

    LEAN_THRESHOLD = 0.025
    LEAN_RELEASE_THRESHOLD = 0.015
    VISIBILITY_THRESHOLD = 0.5

    CROUCH_THRESHOLD = 0.15
    CROUCH_RELEASE_THRESHOLD = 0.08

    SMOOTHING_FACTOR = 0.40

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

        # Punching starts locked. The player must first establish chest guard.
        self._punch_armed = False
        self._guard_frames = 0
        self._guard_origin = None
        self._extension_frames = 0
        self._untracked_frames = 0
        self._last_punch_time = 0.0
        self.PUNCH_COOLDOWN_SECONDS = 0.45

        self.smoothed_difference = None
        self.lean_action = None
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
        if self.cap.isOpened():
            # Match the exact capture size used by punch_trace.py. A
            # different field of view/aspect ratio can change normalized
            # pose geometry, so replayed thresholds would not transfer.
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

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
        # After calibration, require chest guard before the first punch.
        self._punch_armed = False
        self._guard_frames = 0
        self._guard_origin = None
        self._extension_frames = 0
        self._untracked_frames = 0
        self.is_calibrated = True

        print("Standing position calibrated!")
        return True

    def update_actions(self):
        """Read one webcam frame and return all detected game actions."""
        if self._closed:
            raise RuntimeError("GestureDetector is already closed.")

        success, frame = self.cap.read()
        self.current_hip_center_y = None
        self.current_torso_height = None
        self.last_lean_difference = None

        if not success:
            self.status = "CAMERA ERROR"
            self.last_frame = None
            self._punch_armed = False
            self._guard_frames = 0
            self._guard_origin = None
            self._extension_frames = 0
            self.lean_action = None
            return set()

        frame = cv2.flip(frame, 1)
        self.last_frame = frame.copy()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int((time.monotonic() - self._start_time) * 1000)
        result = self.detector.detect_for_video(mp_image, timestamp_ms)

        actions = set()
        self.status = "NO BODY DETECTED"
        punch_pose_active = False

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            if self.show_preview:
                self._draw_pose(frame, landmarks)

            left_shoulder, right_shoulder = landmarks[11], landmarks[12]
            left_hip, right_hip = landmarks[23], landmarks[24]
            required_points = [
                left_shoulder, right_shoulder, left_hip, right_hip
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
                hip_center_x = (left_hip.x + right_hip.x) / 2
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

                left_wrist, right_wrist = landmarks[15], landmarks[16]
                left_elbow, right_elbow = landmarks[13], landmarks[14]

                def visible(*points):
                    return all(
                        point.visibility is not None
                        and point.visibility >= self.VISIBILITY_THRESHOLD
                        for point in points
                    )

                wrists_visible = visible(left_wrist, right_wrist)
                shoulder_center_y = (
                    left_shoulder.y + right_shoulder.y
                ) / 2
                hip_center_y = (left_hip.y + right_hip.y) / 2
                torso_height = hip_center_y - shoulder_center_y
                self.current_hip_center_y = hip_center_y
                self.current_torso_height = torso_height

                is_crouching = False
                if (
                    self.baseline_hip_y is not None
                    and self.baseline_torso_height is not None
                    and self.baseline_torso_height > 0
                ):
                    normalized_hip_drop = (
                        (hip_center_y - self.baseline_hip_y)
                        / self.baseline_torso_height
                    )
                    # Preserve the already-tested crouch hysteresis values.
                    if self.crouch_active:
                        self.crouch_active = (
                            normalized_hip_drop
                            > self.CROUCH_RELEASE_THRESHOLD
                        )
                    else:
                        self.crouch_active = (
                            normalized_hip_drop > self.CROUCH_THRESHOLD
                        )
                    is_crouching = self.crouch_active
                else:
                    self.crouch_active = False

                both_hands_raised = (
                    wrists_visible
                    and left_wrist.y < left_shoulder.y
                    and right_wrist.y < right_shoulder.y
                )

                # Movement uses a responsive smoothed lean value with a small
                # release band. This avoids flickering between LEFT/RIGHT.
                if both_hands_raised:
                    actions.add("JUMP")
                    self.lean_action = None
                elif is_crouching:
                    actions.add("DUCK")
                    self.lean_action = None
                else:
                    lean = self.last_lean_difference
                    if self.lean_action == "LEFT":
                        if lean > -self.LEAN_RELEASE_THRESHOLD:
                            self.lean_action = None
                    elif self.lean_action == "RIGHT":
                        if lean < self.LEAN_RELEASE_THRESHOLD:
                            self.lean_action = None

                    if self.lean_action is None:
                        if lean < -self.LEAN_THRESHOLD:
                            self.lean_action = "LEFT"
                        elif lean > self.LEAN_THRESHOLD:
                            self.lean_action = "RIGHT"

                    if self.lean_action:
                        actions.add(self.lean_action)

                # IMPORTANT: the camera frame is flipped with cv2.flip(frame, 1)
                # before MediaPipe sees it. That reverses MediaPipe's anatomical
                # left/right labels relative to the player's real arms.
                # Therefore:
                #   real RIGHT arm = MediaPipe LEFT landmarks = PUNCH
                #   real LEFT arm  = MediaPipe RIGHT landmarks = BLOCK
                punch_pose_active = False
                punch_rearm_pose = False
                punch_kinematics_valid = False
                if torso_height > 0 and visible(
                    left_shoulder, left_elbow, left_wrist
                ):
                    upper_dx = left_elbow.x - left_shoulder.x
                    upper_dy = left_elbow.y - left_shoulder.y
                    fore_dx = left_wrist.x - left_elbow.x
                    fore_dy = left_wrist.y - left_elbow.y
                    upper_len = math.hypot(upper_dx, upper_dy)
                    fore_len = math.hypot(fore_dx, fore_dy)
                    shoulder_to_wrist = math.hypot(
                        left_wrist.x - left_shoulder.x,
                        left_wrist.y - left_shoulder.y,
                    )
                    if upper_len > 0 and fore_len > 0:
                        punch_kinematics_valid = True
                        cosine = (
                            upper_dx * fore_dx + upper_dy * fore_dy
                        ) / (upper_len * fore_len)
                        arm_extension = shoulder_to_wrist / (
                            upper_len + fore_len
                        )
                        # All these thresholds are normalized by torso size.
                        # They are based on the user's recorded guard, forward
                        # punch, sideways punch and lowering movements.
                        wrist_level = (
                            left_wrist.y - shoulder_center_y
                        ) / torso_height
                        wrist_from_shoulder = shoulder_to_wrist / torso_height

                        # Tasks API world coordinates allow us to measure
                        # actual 3D arm *straightening*. A forward punch can
                        # change this even if the 2D wrist barely moves.
                        # Importantly, raw MediaPipe z is NOT assumed to
                        # always decrease as the player punches forward.
                        world_extension = None
                        world_poses = getattr(result, "pose_world_landmarks", None)
                        if world_poses and len(world_poses[0]) > 15:
                            ws, we, ww = (
                                world_poses[0][i] for i in (11, 13, 15)
                            )
                            try:
                                a = math.dist(
                                    (ws.x, ws.y, ws.z),
                                    (we.x, we.y, we.z),
                                )
                                b = math.dist(
                                    (we.x, we.y, we.z),
                                    (ww.x, ww.y, ww.z),
                                )
                                if a + b > 1e-6:
                                    candidate = math.dist(
                                        (ws.x, ws.y, ws.z),
                                        (ww.x, ww.y, ww.z),
                                    ) / (a + b)
                                    if math.isfinite(candidate):
                                        world_extension = candidate
                            except (AttributeError, TypeError, ValueError):
                                pass

                        # Measure depth RELATIVE to the punching shoulder,
                        # not relative to the camera or the player's body.
                        # MediaPipe depth can flip sign as the hand approaches.
                        image_depth = left_wrist.z - left_shoulder.z
                        world_depth = None
                        if world_poses and len(world_poses[0]) > 15:
                            ws, ww = world_poses[0][11], world_poses[0][15]
                            if (
                                isinstance(ws.z, (int, float))
                                and isinstance(ww.z, (int, float))
                                and math.isfinite(ws.z)
                                and math.isfinite(ww.z)
                            ):
                                world_depth = ww.z - ws.z
                        elbow_level = (
                            left_elbow.y - shoulder_center_y
                        ) / torso_height

                        # Bent fist at the upper chest is the ONLY way to
                        # arm. Don't arm from the hip or an already-extended
                        # fist. Allow a natural range of guard positions.
                        punch_rearm_pose = (
                            -0.44 < wrist_level < 0.54
                            and wrist_from_shoulder < 0.85
                            and arm_extension < 0.72
                            and cosine < 0.83
                            and (
                                world_extension is None
                                or world_extension < 0.92
                            )
                        )

                        if self._guard_origin is not None:
                            origin = self._guard_origin
                            # The wrist must NOT travel down toward the hip.
                            # In a forward punch, screen x may hardly move.
                            no_downward_swing = (
                                wrist_level <= origin[3] + 0.14
                                and wrist_level < 0.48
                            )
                            image_extension = (
                                arm_extension > 0.70
                                and arm_extension - origin[2] > 0.25
                                and wrist_from_shoulder > 0.42
                            )
                            # From the player's recording, a punch directly
                            # into the lens also lifts the fist AND elbow.
                            # This does not require sideways image movement.
                            guard_relative_reach = (
                                origin[3] - wrist_level > 0.21
                                and origin[5] - elbow_level > 0.14
                                and (
                                    arm_extension - origin[2] > 0.10
                                    or (
                                        world_extension is not None
                                        and origin[4] is not None
                                        and world_extension - origin[4] > 0.035
                                    )
                                )
                            )
                            # For an almost motionless 2D punch, accept a
                            # paired depth + world-arm change, regardless of
                            # the sign of MediaPipe's z movement.
                            world_depth_change = (
                                world_depth is not None
                                and origin[7] is not None
                                and abs(world_depth - origin[7]) > 0.055
                            )
                            depth_reach = (
                                abs(image_depth - origin[6]) > 0.065
                                and world_depth_change
                                and world_extension is not None
                                and origin[4] is not None
                                and world_extension - origin[4] > 0.025
                            )
                            world_reach = (
                                world_extension is not None
                                and origin[4] is not None
                                and world_extension - origin[4] > 0.075
                                and world_extension > 0.83
                                and (
                                    origin[3] - wrist_level > 0.10
                                    or world_depth_change
                                )
                            )
                            punch_pose_active = (
                                no_downward_swing
                                and (
                                    image_extension
                                    or guard_relative_reach
                                    or depth_reach
                                    or world_reach
                                )
                            )

                # Real LEFT fist near chin with a bent elbow = held BLOCK.
                # With the mirrored input, this is MediaPipe's RIGHT side.
                block_pose_active = False
                if torso_height > 0 and visible(
                    right_shoulder, right_elbow, right_wrist
                ):
                    chin_x = (left_shoulder.x + right_shoulder.x) / 2
                    chin_y = shoulder_center_y - torso_height * 0.28
                    wrist_to_chin = math.hypot(
                        right_wrist.x - chin_x,
                        right_wrist.y - chin_y,
                    )
                    upper_dx = right_elbow.x - right_shoulder.x
                    upper_dy = right_elbow.y - right_shoulder.y
                    fore_dx = right_wrist.x - right_elbow.x
                    fore_dy = right_wrist.y - right_elbow.y
                    upper_len = math.hypot(upper_dx, upper_dy)
                    fore_len = math.hypot(fore_dx, fore_dy)
                    elbow_bent = False
                    if upper_len > 0 and fore_len > 0:
                        cosine = (
                            upper_dx * fore_dx + upper_dy * fore_dy
                        ) / (upper_len * fore_len)
                        elbow_bent = cosine < 0.78
                    block_pose_active = (
                        not both_hands_raised
                        and wrist_to_chin < torso_height * 0.62
                        and right_wrist.y
                        < right_shoulder.y + torso_height * 0.18
                        and elbow_bent
                    )

                if block_pose_active:
                    actions.add("BLOCK")


                # PUNCH STATE MACHINE: a held, bent chest guard is required.
                # A single fleeting pass through chest height while lowering
                # cannot arm the detector. The fist must then move distinctly
                # away from that guard into a high, extended punch pose.
                if not self._punch_armed:
                    if punch_rearm_pose:
                        self._guard_frames += 1
                        if self._guard_frames >= 3:
                            self._punch_armed = True
                            self._guard_origin = (
                                left_wrist.x, left_wrist.y, arm_extension,
                                wrist_level, world_extension,
                                elbow_level, image_depth, world_depth,
                            )
                            self._extension_frames = 0
                    else:
                        self._guard_frames = 0

                if self._punch_armed and torso_height > 0:
                    # Any loss of tracking or a return to a low resting
                    # position cancels the pending punch, not fires it.
                    if (
                        not punch_kinematics_valid
                        or not visible(left_shoulder, left_elbow, left_wrist)
                    ):
                        # A forward fist can briefly occlude the elbow or
                        # wrist. Do not lose guard from one bad camera frame.
                        self._untracked_frames += 1
                        self._extension_frames = 0
                        if self._untracked_frames >= 4:
                            self._punch_armed = False
                            self._guard_origin = None
                            self._untracked_frames = 0
                    else:
                        self._untracked_frames = 0
                        wrist_level = (left_wrist.y - shoulder_center_y) / torso_height
                        elbow_level = (left_elbow.y - shoulder_center_y) / torso_height
                        if (
                            wrist_level > 0.72
                            or (
                                self._guard_origin is not None
                                and wrist_level > self._guard_origin[3] + 0.32
                            )
                        ):
                            self._punch_armed = False
                            self._guard_origin = None
                            self._extension_frames = 0
                        elif punch_pose_active and not both_hands_raised:
                            self._extension_frames += 1
                            if self._extension_frames >= 2:
                                actions.add("PUNCH")
                                self._last_punch_time = time.monotonic()
                                self._punch_armed = False
                                self._guard_frames = 0
                                self._guard_origin = None
                                self._extension_frames = 0
                        else:
                            self._extension_frames = 0

                # Combat action takes priority over lateral movement for this
                # frame so movement does not overwrite punch/block animation.
                if "PUNCH" in actions or "BLOCK" in actions:
                    actions.discard("LEFT")
                    actions.discard("RIGHT")

                self.status = (
                    " + ".join(sorted(actions)) if actions else (
                        "GUARD READY" if self._punch_armed else "NEUTRAL"
                    )
                )
            else:
                self.crouch_active = False
                self._punch_armed = False
                self._guard_frames = 0
                self._guard_origin = None
                self._extension_frames = 0
                self.lean_action = None
                self.status = "LOW VISIBILITY"
        else:
            self.smoothed_difference = None
            self.crouch_active = False
            self._punch_armed = False
            self._guard_frames = 0
            self._guard_origin = None
            self._extension_frames = 0
            self.lean_action = None

        if self.show_preview:
            cv2.putText(
                frame, "Gesture: " + self.status, (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
            )
            calibration_text = (
                "Calibrated" if self.is_calibrated
                else "Press C in game to calibrate"
            )
            cv2.putText(
                frame, calibration_text, (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2,
            )
            cv2.imshow("Shadow-Boxer - Gesture Preview", frame)

        return actions

    def update(self):
        """Backward-compatible API returning one primary gesture string."""
        actions = self.update_actions()
        for gesture in ("JUMP", "DUCK", "LEFT", "RIGHT", "PUNCH", "BLOCK"):
            if gesture in actions:
                return gesture
        return "NEUTRAL"

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
