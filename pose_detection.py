import math
import cv2
import mediapipe as mp
import time

# --------------------------------
# 1. MediaPipe Setup
# --------------------------------

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="models/pose_landmarker_lite.task"
    ),
    running_mode=RunningMode.VIDEO,
    num_poses=1
)

detector = PoseLandmarker.create_from_options(options)

# --------------------------------
# 2. Pose Drawing Connections
# --------------------------------

connections = [
    (11, 12),
    (11, 13), (13, 15),
    (12, 14), (14, 16),
    (11, 23), (12, 24),
    (23, 24),
    (23, 25), (25, 27),
    (24, 26), (26, 28),
    (27, 29), (29, 31),
    (28, 30), (30, 32)
]


def draw_pose(frame, landmarks):
    height, width, _ = frame.shape

    for start, end in connections:
        p1 = landmarks[start]
        p2 = landmarks[end]

        if p1.visibility > 0.5 and p2.visibility > 0.5:
            x1 = int(p1.x * width)
            y1 = int(p1.y * height)
            x2 = int(p2.x * width)
            y2 = int(p2.y * height)

            cv2.line(
                frame, (x1, y1), (x2, y2),
                (0, 255, 0), 2
            )

    for point in landmarks:
        if point.visibility > 0.5:
            x = int(point.x * width)
            y = int(point.y * height)

            cv2.circle(
                frame, (x, y), 5,
                (0, 0, 255), -1
            )


# --------------------------------
# 3. Lean Detection Settings
# --------------------------------



LEAN_THRESHOLD = 0.04
VISIBILITY_THRESHOLD = 0.5

# Crouch detection settings
CROUCH_THRESHOLD = 0.15
CROUCH_RELEASE_THRESHOLD = 0.08

baseline_hip_y = None
baseline_torso_height = None

crouch_active = False

# Smooth the readings to reduce small fluctuations
smoothed_difference = None
SMOOTHING_FACTOR = 0.25


# --------------------------------
# 4. Webcam Setup
# --------------------------------

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    detector.close()
    raise SystemExit

start_time = time.monotonic()


# --------------------------------
# 5. Main Detection Loop
# --------------------------------

try:
    while True:

        success, frame = cap.read()

        if not success:
            print("Could not read webcam frame.")
            break

        # Mirror webcam image
        frame = cv2.flip(frame, 1)

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(
            frame, cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        timestamp_ms = int(
            (time.monotonic() - start_time) * 1000
        )

        # Run pose detection
        result = detector.detect_for_video(
            mp_image, timestamp_ms
        )

        gesture = "NO BODY DETECTED"
        lean_difference = None

        # --------------------------------
        # 6. Calculate Body Lean
        # --------------------------------
        current_hip_center_y = None
        current_torso_height = None        
        if result.pose_landmarks:

            landmarks = result.pose_landmarks[0]

            draw_pose(frame, landmarks)

            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_hip = landmarks[23]
            right_hip = landmarks[24]

            def calculate_angle(a, b, c):

                angle1 = math.atan2(a.y - b.y, a.x - b.x)
                angle2 = math.atan2(c.y - b.y, c.x - b.x)

                angle = abs(math.degrees(angle1 - angle2))

                if angle > 180:
                    angle = 360 - angle

                return angle

            # Check landmark visibility
            points = [
                left_shoulder,
                right_shoulder,
                left_hip,
                right_hip
            ]

            reliable = all(
                point.visibility is not None
                and point.visibility >= VISIBILITY_THRESHOLD
                for point in points
            )

            if reliable:

                # Calculate shoulder midpoint
                shoulder_center_x = (
                    left_shoulder.x + right_shoulder.x
                ) / 2

                # Calculate hip midpoint
                hip_center_x = (
                    left_hip.x + right_hip.x
                ) / 2

                # Calculate lean difference
                raw_difference = (
                    shoulder_center_x - hip_center_x
                )

                # Smooth the difference
                if smoothed_difference is None:
                    smoothed_difference = raw_difference
                else:
                    smoothed_difference = (
                        SMOOTHING_FACTOR * raw_difference
                        + (1 - SMOOTHING_FACTOR)
                        * smoothed_difference
                    )

                lean_difference = smoothed_difference

                # Check wrist visibility
                
                left_wrist = landmarks[15]
                right_wrist = landmarks[16]

                wrists_visible = (
                    left_wrist.visibility is not None
                    and right_wrist.visibility is not None
                    and left_wrist.visibility >= VISIBILITY_THRESHOLD
                    and right_wrist.visibility >= VISIBILITY_THRESHOLD
                )

                
                # Get knee and ankle landmarks
                left_knee = landmarks[25]
                right_knee = landmarks[26]

                left_ankle = landmarks[27]
                right_ankle = landmarks[28]

                # Check visibility of knee and ankle landmarks
                knees_visible = all(
                    point.visibility is not None
                    and point.visibility >= VISIBILITY_THRESHOLD
                    for point in [
                        left_knee,
                        right_knee,
                        left_ankle,
                        right_ankle
                    ]
                )

                
                # Calculate shoulder and hip positions
                shoulder_center_y = (
                    left_shoulder.y + right_shoulder.y
                ) / 2

                hip_center_y = (
                    left_hip.y + right_hip.y
                ) / 2

                torso_height = hip_center_y - shoulder_center_y

                # Store current measurements for calibration
                current_hip_center_y = hip_center_y
                current_torso_height = torso_height

                # Crouch detection using calibrated hip movement
                is_crouching = False

                if (
                    baseline_hip_y is not None
                    and baseline_torso_height is not None
                    and baseline_torso_height > 0
                ):

                    hip_drop = hip_center_y - baseline_hip_y

                    normalized_hip_drop = (
                        hip_drop / baseline_torso_height
                    )

                    # Hysteresis prevents rapid switching
                    if crouch_active:
                        crouch_active = (
                            normalized_hip_drop
                            > CROUCH_RELEASE_THRESHOLD
                        )
                    else:
                        crouch_active = (
                            normalized_hip_drop
                            > CROUCH_THRESHOLD
                        )

                    is_crouching = crouch_active

                # Detect raised hands
                both_hands_raised = (
                    wrists_visible
                    and left_wrist.y < left_shoulder.y
                    and right_wrist.y < right_shoulder.y
                )

                # Classify gestures
                if both_hands_raised:
                    gesture = "JUMP"

                elif is_crouching:
                    gesture = "DUCK"

                elif lean_difference < -LEAN_THRESHOLD:
                    gesture = "LEAN LEFT"

                elif lean_difference > LEAN_THRESHOLD:
                    gesture = "LEAN RIGHT"

                else:
                    gesture = "NEUTRAL"

            else:
                gesture = "LOW VISIBILITY"

        else:
            smoothed_difference = None
        # --------------------------------
        # 7. Display Gesture on Webcam
        # --------------------------------

        cv2.putText(
            frame,
            "Gesture: " + gesture,
            (20, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        if lean_difference is not None:
            cv2.putText(
                frame,
                "Lean: " + str(round(lean_difference, 3)),
                (20, 85),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

        cv2.imshow(
            "Shadow-Boxer - Live Lean Detection",
            frame
        )

        # --------------------------------
        # 8. Keyboard Controls
        # --------------------------------

        key = cv2.waitKey(1) & 0xFF

        # Calibrate standing position
        if key == ord("c"):

            if (
                current_hip_center_y is not None
                and current_torso_height is not None
                and current_torso_height > 0
            ):
                baseline_hip_y = current_hip_center_y
                baseline_torso_height = current_torso_height

                crouch_active = False

                print("Standing position calibrated!")

            else:
                print("Body landmarks not reliable. Try again.")

        if key == ord("q"):
            break

finally:

    cap.release()
    detector.close()
    cv2.destroyAllWindows()

    print("Webcam closed. Lean detection stopped.")
