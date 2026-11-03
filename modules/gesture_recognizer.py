"""
modules/gesture_recognizer.py — Rule-Based Gesture Recognition
================================================================
OWNER: TM4 — Gesture Recognition Developer

Provides the GestureRecognizer class that analyzes MediaPipe hand landmarks
to determine which gesture is being made.

INTERFACE CONTRACT (DO NOT change these method signatures):
    class GestureRecognizer:
        def recognize(self, hand_landmarks, handedness: str) -> str
            # hand_landmarks: MediaPipe NormalizedLandmarkList (21 landmarks)
            # handedness: "Left" or "Right"
            # Returns: gesture key from config.GESTURE_MAP (e.g., "thumbs_up", "peace")
        def get_finger_states(self, landmarks, handedness: str) -> list[bool]
            # Returns: [thumb, index, middle, ring, pinky] — True = extended

See config.py for: GESTURE_MAP, GESTURE_STABILITY_FRAMES
"""

# TODO: TM4 — Replace this stub with your implementation
# This stub exists so other modules can import without errors during development.

from config import GESTURE_MAP, GESTURE_STABILITY_FRAMES


class GestureRecognizer:
    """Classifies hand gestures using rule-based finger position analysis."""

    def __init__(self):
        pass

    def recognize(self, hand_landmarks, handedness: str = "Right") -> str:
        """
        Analyze hand landmarks and return the gesture name.

        Args:
            hand_landmarks: MediaPipe NormalizedLandmarkList with 21 landmarks.
            handedness: "Left" or "Right" — needed for thumb detection.

        Returns:
            A key from config.GESTURE_MAP (e.g., "thumbs_up", "peace", "unknown")
        """
        raise NotImplementedError("TM4: Implement recognize()")

    def get_finger_states(self, landmarks, handedness: str = "Right") -> list:
        """
        Determine which fingers are extended.

        Args:
            landmarks: MediaPipe NormalizedLandmarkList
            handedness: "Left" or "Right"

        Returns:
            List of 5 booleans: [thumb, index, middle, ring, pinky]
            True means the finger is extended/open.
        """
        raise NotImplementedError("TM4: Implement get_finger_states()")
