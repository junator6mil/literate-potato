"""
modules/hand_detector.py — MediaPipe Hand Detection
=====================================================
OWNER: TM3 — Hand Detection Developer

Provides the HandDetector class that uses MediaPipe to detect hands
and extract 21 landmarks per hand.

INTERFACE CONTRACT (DO NOT change these method signatures):
    class HandDetector:
        def detect(self, frame: np.ndarray) -> tuple[np.ndarray, object]
            # Returns (annotated_frame, mediapipe_results)
            # annotated_frame: the input frame with hand landmarks drawn on it
            # mediapipe_results: the raw results from mp.solutions.hands
        def close(self) -> None

See config.py for: MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE
"""

# TODO: TM3 — Replace this stub with your implementation
# This stub exists so other modules can import without errors during development.

import numpy as np
from config import MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE


class HandDetector:
    """Detects hands and extracts landmarks using MediaPipe."""

    def __init__(self):
        pass

    def detect(self, frame: np.ndarray) -> tuple:
        """
        Process a BGR frame and detect hands.

        Args:
            frame: BGR image from OpenCV (numpy array)

        Returns:
            tuple of (annotated_frame, results)
            - annotated_frame: frame with landmarks drawn
            - results: MediaPipe results object (has .multi_hand_landmarks, .multi_handedness)
        """
        raise NotImplementedError("TM3: Implement detect()")

    def close(self) -> None:
        """Release MediaPipe resources."""
        raise NotImplementedError("TM3: Implement close()")
