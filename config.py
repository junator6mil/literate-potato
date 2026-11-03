"""
config.py — Shared Configuration Constants
===========================================
All modules import settings from here. Change values here to tune
the application without touching module code.

Owner: TM1 (Team Leader)
"""

# ──────────────────────────────────────────────
# Camera Settings
# ──────────────────────────────────────────────
CAMERA_INDEX = 0                # Default webcam (change to 1 for external cam)
FRAME_WIDTH = 640               # Capture width in pixels
FRAME_HEIGHT = 480              # Capture height in pixels

# ──────────────────────────────────────────────
# MediaPipe Hand Detection Settings
# ──────────────────────────────────────────────
MAX_HANDS = 1                   # Number of hands to detect (keep 1 for speed)
DETECTION_CONFIDENCE = 0.7      # Min confidence to detect a hand (0.0 – 1.0)
TRACKING_CONFIDENCE = 0.7       # Min confidence to track a hand (0.0 – 1.0)

# ──────────────────────────────────────────────
# GUI / Display Settings
# ──────────────────────────────────────────────
WINDOW_TITLE = "Hand Sign Recognition"
VIDEO_WIDTH = 640               # Display width in the Tkinter window
VIDEO_HEIGHT = 480              # Display height in the Tkinter window
UPDATE_INTERVAL_MS = 30         # Milliseconds between frame updates (~33 FPS)

# ──────────────────────────────────────────────
# Gesture Recognition Settings
# ──────────────────────────────────────────────
GESTURE_STABILITY_FRAMES = 15   # Same gesture must be seen for N frames to confirm
                                # At ~33 FPS, 15 frames ≈ 0.5 seconds

# ──────────────────────────────────────────────
# Gesture-to-Text Mapping
# ──────────────────────────────────────────────
GESTURE_MAP = {
    "open_palm":    "Hello",
    "fist":         "Fist",
    "thumbs_up":    "Yes",
    "thumbs_down":  "No",
    "peace":        "Peace",
    "point":        "Point",
    "three":        "Three",
    "four":         "Four",
    "rock":         "Rock On",
    "call_me":      "Call Me",
    "unknown":      "?",
}

# ──────────────────────────────────────────────
# MediaPipe Landmark Indices (reference for TM3/TM4)
# ──────────────────────────────────────────────
# See: https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
#
# WRIST = 0
# THUMB:  CMC=1, MCP=2, IP=3,  TIP=4
# INDEX:  MCP=5, PIP=6, DIP=7, TIP=8
# MIDDLE: MCP=9, PIP=10, DIP=11, TIP=12
# RING:   MCP=13, PIP=14, DIP=15, TIP=16
# PINKY:  MCP=17, PIP=18, DIP=19, TIP=20

LANDMARK_NAMES = {
    0: "WRIST",
    4: "THUMB_TIP", 3: "THUMB_IP", 2: "THUMB_MCP", 1: "THUMB_CMC",
    8: "INDEX_TIP", 7: "INDEX_DIP", 6: "INDEX_PIP", 5: "INDEX_MCP",
    12: "MIDDLE_TIP", 11: "MIDDLE_DIP", 10: "MIDDLE_PIP", 9: "MIDDLE_MCP",
    16: "RING_TIP", 15: "RING_DIP", 14: "RING_PIP", 13: "RING_MCP",
    20: "PINKY_TIP", 19: "PINKY_DIP", 18: "PINKY_PIP", 17: "PINKY_MCP",
}
