"""
modules/hand_detector.py — MediaPipe Hand Detection
=====================================================
OWNER: TM3 — Hand Detection Developer

Detects hands in a video frame using MediaPipe and returns the annotated
frame plus a results object conforming to the team interface contract.

INTERFACE CONTRACT (DO NOT change these method signatures):
    class HandDetector:
        def detect(self, frame: np.ndarray) -> tuple[np.ndarray, object]
            # Returns (annotated_frame, mediapipe_results)
            # annotated_frame: the input frame with hand landmarks drawn on it
            # mediapipe_results: object with .multi_hand_landmarks and .multi_handedness
        def close(self) -> None

DUAL-ENGINE ARCHITECTURE:
    1. Legacy mp.solutions.hands Engine:
       Used automatically if running in Python 3.12 / standard MediaPipe
       (as specified in README.md). Requires no external model file.
    2. Modern Tasks API (HandLandmarker) Engine:
       Used automatically on newer MediaPipe (>= 1.0) / Python 3.14+.
       Automatically downloads hand_landmarker.task if not already present.
       Wraps results in a compatibility layer with .multi_hand_landmarks and
       .multi_handedness so TM4's recognizer and TM5's GUI work without changes.

See config.py for: MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE
"""

import os
import cv2
import numpy as np
import mediapipe as mp

from config import MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: LEGACY COMPATIBILITY WRAPPERS (FOR TASKS API ENGINE)
# ═══════════════════════════════════════════════════════════════════

class _Classification:
    """Mimics a single MediaPipe legacy Classification entry."""
    def __init__(self, label, score=1.0):
        self.label = label          # "Left" or "Right"
        self.score = score          # Confidence score
        self.index = 0
        self.display_name = label


class _ClassificationList:
    """Mimics a MediaPipe legacy ClassificationList (has .classification)."""
    def __init__(self, label, score=1.0):
        self.classification = [_Classification(label, score)]


class _NormalizedLandmarkList:
    """Mimics a MediaPipe legacy NormalizedLandmarkList (has .landmark)."""
    def __init__(self, landmarks):
        self.landmark = landmarks   # list of NormalizedLandmark objects


class _LegacyResults:
    """
    Wraps a Tasks-API HandLandmarkerResult into the legacy format.

    After wrapping:
        wrapped.multi_hand_landmarks  ->  list of _NormalizedLandmarkList
        wrapped.multi_handedness      ->  list of _ClassificationList
    """
    def __init__(self, tasks_result):
        self.multi_hand_landmarks = None
        self.multi_handedness = None

        if tasks_result is None:
            return

        hands = tasks_result.hand_landmarks       # list of lists
        handedness = tasks_result.handedness       # list of lists of Category

        if not hands:
            return

        # Convert hand landmarks
        self.multi_hand_landmarks = []
        for hand_lm_list in hands:
            self.multi_hand_landmarks.append(
                _NormalizedLandmarkList(hand_lm_list)
            )

        # Convert handedness
        self.multi_handedness = []
        for h_list in handedness:
            if h_list:
                cat = h_list[0]
                label = getattr(cat, "category_name", "Right")
                score = getattr(cat, "score", 1.0)
                self.multi_handedness.append(
                    _ClassificationList(label, score)
                )
            else:
                self.multi_handedness.append(
                    _ClassificationList("Right", 1.0)
                )


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: HAND DRAWING FOR TASKS API ENGINE
# ═══════════════════════════════════════════════════════════════════

HAND_BONE_CONNECTIONS = [
    # Thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Index finger
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Middle finger
    (0, 9), (9, 10), (10, 11), (11, 12),
    # Ring finger
    (0, 13), (13, 14), (14, 15), (15, 16),
    # Pinky
    (0, 17), (17, 18), (18, 19), (19, 20),
    # Palm connections
    (5, 9), (9, 13), (13, 17),
]

FINGERTIP_INDICES = {4, 8, 12, 16, 20}
LANDMARK_COLOR = (0, 0, 255)        # Red dots
FINGERTIP_BORDER = (255, 255, 255)  # White border on tips
CONNECTION_COLOR = (0, 255, 255)    # Yellow lines


def _draw_hand_on_frame(frame, landmarks):
    """Draw landmarks and connections onto frame."""
    h, w, _ = frame.shape
    points = []
    for lm in landmarks:
        px = int(lm.x * w)
        py = int(lm.y * h)
        points.append((px, py))

    for start_idx, end_idx in HAND_BONE_CONNECTIONS:
        cv2.line(frame, points[start_idx], points[end_idx],
                 CONNECTION_COLOR, 2, cv2.LINE_AA)

    for idx, (px, py) in enumerate(points):
        if idx in FINGERTIP_INDICES:
            cv2.circle(frame, (px, py), 6, LANDMARK_COLOR, -1, cv2.LINE_AA)
            cv2.circle(frame, (px, py), 6, FINGERTIP_BORDER, 1, cv2.LINE_AA)
        else:
            cv2.circle(frame, (px, py), 4, LANDMARK_COLOR, -1, cv2.LINE_AA)


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: HAND DETECTOR IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════

_DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "hand_landmarker.task"
)

_MODEL_DOWNLOAD_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)


class HandDetector:
    """Detects hands and extracts landmarks using MediaPipe."""

    def __init__(self, model_path: str = _DEFAULT_MODEL_PATH):
        """
        Initialise HandDetector. Auto-detects whether to use legacy
        mp.solutions.hands or modern Tasks API HandLandmarker.
        """
        self._use_legacy = hasattr(mp, "solutions") and hasattr(mp.solutions, "hands")
        self._hands = None
        self._landmarker = None

        if self._use_legacy:
            # Legacy engine (MediaPipe < 1.0, Python 3.12 recommended)
            self._mp_draw = mp.solutions.drawing_utils
            self._mp_hands = mp.solutions.hands
            self._hands = self._mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=MAX_HANDS,
                min_detection_confidence=DETECTION_CONFIDENCE,
                min_tracking_confidence=TRACKING_CONFIDENCE,
            )
        else:
            # Modern Tasks API engine (MediaPipe >= 1.0, Python 3.14+)
            if not os.path.exists(model_path):
                print(f"[HandDetector] Model file not found at {model_path}. Downloading...")
                import urllib.request
                try:
                    urllib.request.urlretrieve(_MODEL_DOWNLOAD_URL, model_path)
                    print("[HandDetector] Model downloaded successfully.")
                except Exception as err:
                    raise FileNotFoundError(
                        f"MediaPipe model file not found at {model_path} and automatic download failed: {err}\n"
                        f"Please manually download the model from:\n  {_MODEL_DOWNLOAD_URL}"
                    )

            BaseOptions = mp.tasks.BaseOptions
            HandLandmarker = mp.tasks.vision.HandLandmarker
            HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
            RunningMode = mp.tasks.vision.RunningMode

            options = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=RunningMode.IMAGE,
                num_hands=MAX_HANDS,
                min_hand_detection_confidence=DETECTION_CONFIDENCE,
                min_hand_presence_confidence=DETECTION_CONFIDENCE,
                min_tracking_confidence=TRACKING_CONFIDENCE,
            )
            self._landmarker = HandLandmarker.create_from_options(options)

    def detect(self, frame: np.ndarray) -> tuple:
        """
        Process a BGR frame and detect hands.

        Args:
            frame: BGR image from OpenCV (numpy array, shape H x W x 3)

        Returns:
            tuple of (annotated_frame, results)
            - annotated_frame: frame with hand landmarks drawn
            - results: object with .multi_hand_landmarks and .multi_handedness
        """
        annotated = frame.copy()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self._use_legacy:
            # 1. Legacy execution
            results = self._hands.process(rgb_frame)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self._mp_draw.draw_landmarks(
                        annotated,
                        hand_landmarks,
                        self._mp_hands.HAND_CONNECTIONS,
                    )
            return annotated, results
        else:
            # 2. Tasks API execution
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame,
            )
            tasks_result = self._landmarker.detect(mp_image)
            results = _LegacyResults(tasks_result)

            if results.multi_hand_landmarks:
                for hand_lm_list in results.multi_hand_landmarks:
                    _draw_hand_on_frame(annotated, hand_lm_list.landmark)

            return annotated, results

    def close(self) -> None:
        """Release MediaPipe resources."""
        if self._hands is not None:
            self._hands.close()
            self._hands = None
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None
