import cv2
import time
import numpy as np
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# =========================================================
# LOAD POSE LANDMARKER
# =========================================================

pose_model = "models/pose_landmarker_lite.task"

pose_base_options = python.BaseOptions(
    model_asset_path=pose_model
)

pose_options = vision.PoseLandmarkerOptions(
    base_options=pose_base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_poses=1,
    output_segmentation_masks=True
)

pose_landmarker = vision.PoseLandmarker.create_from_options(
    pose_options
)


# =========================================================
# LOAD GESTURE RECOGNIZER
# =========================================================

gesture_model = "models/gesture_recognizer.task"

gesture_base_options = python.BaseOptions(
    model_asset_path=gesture_model
)

gesture_options = vision.GestureRecognizerOptions(
    base_options=gesture_base_options,
    running_mode=vision.RunningMode.IMAGE
)

gesture_recognizer = vision.GestureRecognizer.create_from_options(
    gesture_options
)


# =========================================================
# OPEN CAMERA
# =========================================================

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Could not open camera.")
    exit()

print()
print("======================================")
print("      INVISIBILITY MODE")
print("======================================")
print()
print("Get OUT of the camera frame.")
print("Capturing background in 5 seconds...")


# =========================================================
# CAPTURE BACKGROUND
# =========================================================

background = None

start_time = time.time()

while True:

    ret, frame = cap.read()

    if not ret:
        print("Could not read camera.")
        break

    elapsed = time.time() - start_time
    remaining = 5 - int(elapsed)

    if remaining > 0:

        display = frame.copy()

        cv2.putText(
            display,
            f"Background capture in: {remaining}",
            (40, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.1,
            (0, 255, 0),
            3
        )

        cv2.imshow(
            "INVISIBILITY MODE",
            display
        )

    else:

        background = frame.copy()

        print()
        print("Background captured!")
        print()
        print("Now ENTER the frame.")
        print()
        print("Controls:")
        print("OPEN PALM  = INVISIBLE")
        print("CLOSED FIST = VISIBLE")
        print("Q = QUIT")

        break

    if cv2.waitKey(1) & 0xFF == ord("q"):
        cap.release()
        cv2.destroyAllWindows()
        pose_landmarker.close()
        gesture_recognizer.close()
        exit()


# =========================================================
# INVISIBILITY STATE
# =========================================================

invisible = False

timestamp = 0


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    ret, frame = cap.read()

    if not ret:
        print("Could not read camera.")
        break

    timestamp += 1


    # =====================================================
    # PREPARE IMAGE FOR MEDIAPIPE
    # =====================================================

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )


    # =====================================================
    # PERSON SEGMENTATION
    # =====================================================

    pose_result = pose_landmarker.detect_for_video(
        mp_image,
        timestamp
    )


    # =====================================================
    # GESTURE RECOGNITION
    # =====================================================

    gesture_result = gesture_recognizer.recognize(
        mp_image
    )


    # =====================================================
    # CHECK GESTURE
    # =====================================================

    if gesture_result.gestures:

        gesture = gesture_result.gestures[0][0]

        gesture_name = gesture.category_name
        confidence = gesture.score

        # Only accept reasonably confident gestures
        if confidence > 0.60:

            if gesture_name == "Open_Palm":

                invisible = True

            elif gesture_name == "Closed_Fist":

                invisible = False


    # =====================================================
    # CREATE OUTPUT
    # =====================================================

    output = frame.copy()


    # =====================================================
    # APPLY INVISIBILITY
    # =====================================================

    if invisible and pose_result.segmentation_masks:

        mask = pose_result.segmentation_masks[0].numpy_view()

        if len(mask.shape) == 3:
            mask = mask[:, :, 0]

        mask = cv2.resize(
            mask,
            (frame.shape[1], frame.shape[0])
        )

        # Smooth mask edges
        mask = cv2.GaussianBlur(
            mask,
            (7, 7),
            0
        )

        person_mask = mask > 0.5

        # Replace person with background
        output[person_mask] = background[person_mask]


    # =====================================================
    # STATUS DISPLAY
    # =====================================================

    if invisible:

        status = "INVISIBLE"
        instruction = "Closed Fist = Visible"

    else:

        status = "VISIBLE"
        instruction = "Open Palm = Invisible"


    cv2.putText(
        output,
        f"Status: {status}",
        (30, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        output,
        instruction,
        (30, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    # =====================================================
    # SHOW RESULT
    # =====================================================

    cv2.imshow(
        "INVISIBILITY MODE",
        output
    )


    # =====================================================
    # QUIT
    # =====================================================

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# =========================================================
# CLEANUP
# =========================================================

cap.release()

pose_landmarker.close()
gesture_recognizer.close()

cv2.destroyAllWindows()

print()
print("Invisibility Mode stopped.")