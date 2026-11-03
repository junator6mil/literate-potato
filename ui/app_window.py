"""
ui/app_window.py — Tkinter Desktop GUI
========================================
OWNER: TM5 — GUI Developer

Provides the AppWindow class — the main application window that displays
the camera feed, recognized gestures, and accumulated text.

INTERFACE CONTRACT (DO NOT change these method signatures):
    class AppWindow:
        def __init__(self, camera, detector, recognizer)
            # camera:     CameraManager instance (from modules.camera)
            # detector:   HandDetector instance (from modules.hand_detector)
            # recognizer: GestureRecognizer instance (from modules.gesture_recognizer)
        def run(self) -> None
            # Starts the Tkinter main loop (blocks until window is closed)

LAYOUT REQUIREMENTS:
    - Video panel showing camera feed with hand landmarks (640x480)
    - Current gesture label (large text)
    - Text history area (accumulated recognized gestures)
    - Buttons: Start Camera, Stop Camera, Clear Text, Exit

MAIN LOOP PATTERN (use Tkinter's after()):
    def update_frame(self):
        success, frame = self.camera.read_frame()
        if success:
            annotated, results = self.detector.detect(frame)
            if results.multi_hand_landmarks:
                landmarks = results.multi_hand_landmarks[0]
                handedness = results.multi_handedness[0].classification[0].label
                gesture = self.recognizer.recognize(landmarks, handedness)
                # Update display...
            # Convert frame for Tkinter display...
        self.root.after(UPDATE_INTERVAL_MS, self.update_frame)

See config.py for: WINDOW_TITLE, VIDEO_WIDTH, VIDEO_HEIGHT, UPDATE_INTERVAL_MS
"""

# TODO: TM5 — Replace this stub with your implementation
# This stub exists so other modules can import without errors during development.

from config import WINDOW_TITLE, VIDEO_WIDTH, VIDEO_HEIGHT, UPDATE_INTERVAL_MS


class AppWindow:
    """Main Tkinter application window for hand sign recognition."""

    def __init__(self, camera, detector, recognizer):
        self.camera = camera
        self.detector = detector
        self.recognizer = recognizer

    def run(self) -> None:
        """Start the Tkinter main loop."""
        raise NotImplementedError("TM5: Implement the GUI")
