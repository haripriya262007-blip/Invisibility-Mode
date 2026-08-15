import cv2
import time
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# Load Gesture Recognizer model
model_path = "models/gesture_recognizer.task"

base_options = python.BaseOptions(
    model_asset_path=model_path
)

options = vision.GestureRecognizerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.LIVE_STREAM,
    result_callback=lambda result, output_image, timestamp_ms:
        print_gesture(result)
)

recognizer = vision.GestureRecognizer.create_from_options(options)


def print_gesture(result):
    if result.gestures:
        gesture = result.gestures[0][0]

        print(
            "Gesture:",
            gesture.category_name,
            "Confidence:",
            round(gesture.score, 2)
        )


# Open camera
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Could not open camera.")
    exit()

print("Gesture recognition started!")
print("Show your hand to the camera.")
print("Press Q to quit.")

timestamp = 0

while True:

    ret, frame = cap.read()

    if not ret:
        print("Could not read camera.")
        break

    # Convert BGR → RGB
    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    timestamp += 1

    # Send frame to MediaPipe
    recognizer.recognize_async(
        mp_image,
        timestamp
    )

    cv2.imshow(
        "Gesture Recognition Test",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
recognizer.close()
cv2.destroyAllWindows()