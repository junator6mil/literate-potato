"""
tests/test_hand_detector.py
===========================
Test suite for HandDetector in modules/hand_detector.py (TM3).

Verifies:
1. HandDetector initialization and cleanup (close)
2. Detection on blank/zero frames (handles absence of hands without error)
3. Interface conformity with TM5's GUI and TM4's Recognizer:
   - detect(frame) -> (annotated_frame, results)
   - results.multi_hand_landmarks[0].landmark[i].x/y/z
   - results.multi_handedness[0].classification[0].label ("Left"/"Right")
4. Structure of legacy compatibility wrapper objects

Run from literate-potato root:
    python tests/test_hand_detector.py
"""

import sys
import os
import unittest
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.hand_detector import (
    HandDetector,
    _LegacyResults,
    _NormalizedLandmarkList,
    _ClassificationList,
    _Classification
)


class FakeCategory:
    def __init__(self, category_name="Right", score=0.95):
        self.category_name = category_name
        self.score = score


class FakeLandmark:
    def __init__(self, x=0.5, y=0.5, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class FakeTasksResult:
    def __init__(self, num_hands=1, handedness_label="Right"):
        if num_hands > 0:
            self.hand_landmarks = [[FakeLandmark() for _ in range(21)] for _ in range(num_hands)]
            self.handedness = [[FakeCategory(handedness_label)] for _ in range(num_hands)]
        else:
            self.hand_landmarks = []
            self.handedness = []


class TestHandDetector(unittest.TestCase):
    def setUp(self):
        self.detector = HandDetector()

    def tearDown(self):
        self.detector.close()

    def test_init_and_close(self):
        """Detector initializes and can be closed cleanly."""
        self.assertIsNotNone(self.detector._landmarker)

    def test_detect_blank_frame(self):
        """Blank image produces annotated frame and None multi_hand_landmarks."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        annotated, results = self.detector.detect(frame)
        
        self.assertEqual(annotated.shape, (480, 640, 3))
        self.assertIsNone(results.multi_hand_landmarks)
        self.assertIsNone(results.multi_handedness)

    def test_legacy_wrapper_no_hands(self):
        """_LegacyResults with empty detection matches legacy MediaPipe output."""
        empty_tasks_res = FakeTasksResult(num_hands=0)
        legacy = _LegacyResults(empty_tasks_res)
        self.assertIsNone(legacy.multi_hand_landmarks)
        self.assertIsNone(legacy.multi_handedness)

    def test_legacy_wrapper_with_hand(self):
        """_LegacyResults provides exact attributes expected by TM4 and TM5."""
        tasks_res = FakeTasksResult(num_hands=1, handedness_label="Right")
        legacy = _LegacyResults(tasks_res)

        # TM5 GUI access pattern:
        # results.multi_hand_landmarks
        self.assertIsNotNone(legacy.multi_hand_landmarks)
        self.assertEqual(len(legacy.multi_hand_landmarks), 1)

        # landmarks = results.multi_hand_landmarks[0]
        # landmarks.landmark (list of 21 points)
        first_hand = legacy.multi_hand_landmarks[0]
        self.assertTrue(hasattr(first_hand, 'landmark'))
        self.assertEqual(len(first_hand.landmark), 21)
        self.assertEqual(first_hand.landmark[0].x, 0.5)

        # handedness = results.multi_handedness[0].classification[0].label
        self.assertIsNotNone(legacy.multi_handedness)
        self.assertEqual(len(legacy.multi_handedness), 1)
        first_handedness = legacy.multi_handedness[0]
        self.assertTrue(hasattr(first_handedness, 'classification'))
        self.assertEqual(len(first_handedness.classification), 1)
        self.assertEqual(first_handedness.classification[0].label, "Right")
        self.assertAlmostEqual(first_handedness.classification[0].score, 0.95)


if __name__ == "__main__":
    unittest.main()
