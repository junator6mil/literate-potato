"""
modules/gesture_recognizer.py — Rule-Based Gesture Recognition
================================================================
OWNER: TM4 — Gesture Recognition Developer

Provides the GestureRecognizer class that analyzes MediaPipe hand landmarks
to determine which gesture is being made.

This implementation is lightweight, uses only the MediaPipe landmark geometry,
and includes a stability system that requires a gesture to be seen for
GESTURE_STABILITY_FRAMES consecutive frames before it is confirmed.

No external ML libraries are used.  The code is deliberately simple and
heavily commented so that it can be explained easily during a presentation.

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

from __future__ import annotations

import math
from typing import List

from config import GESTURE_MAP, GESTURE_STABILITY_FRAMES


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _extract_landmarks(landmarks) -> List[object]:
    """Return a flat list of landmark objects.

    MediaPipe's ``NormalizedLandmarkList`` exposes the landmarks via a
    ``.landmark`` attribute, while a simple ``list`` of ``NormalizedLandmark``
    objects can be passed directly.  This helper abstracts that difference.
    """
    if hasattr(landmarks, "landmark"):
        return list(landmarks.landmark)
    return list(landmarks)


def _is_finite_number(value) -> bool:
    """Check that *value* is a real, finite number (not NaN/inf)."""
    return isinstance(value, (int, float)) and math.isfinite(value)


# ---------------------------------------------------------------------------
# Landmark index constants (for readability)
# ---------------------------------------------------------------------------

WRIST      = 0
THUMB_MCP  = 2
THUMB_IP   = 3
THUMB_TIP  = 4
INDEX_PIP  = 6
INDEX_TIP  = 8
MIDDLE_PIP = 10
MIDDLE_TIP = 12
RING_PIP   = 14
RING_TIP   = 16
PINKY_PIP  = 18
PINKY_TIP  = 20

# Indices that must have valid coordinates for recognition to proceed
_REQUIRED_INDICES = [WRIST, THUMB_MCP, THUMB_IP, THUMB_TIP,
                     INDEX_PIP, INDEX_TIP, MIDDLE_PIP, MIDDLE_TIP,
                     RING_PIP, RING_TIP, PINKY_PIP, PINKY_TIP]


# ═══════════════════════════════════════════════════════════════════════════
# GestureRecognizer class
# ═══════════════════════════════════════════════════════════════════════════

class GestureRecognizer:
    """Classifies hand gestures using rule-based finger position analysis.

    The public API consists of ``__init__``, ``get_finger_states`` and
    ``recognize``.  Internally the class maintains a small amount of state
    to implement the *gesture stability* requirement.
    """

    # -----------------------------------------------------------------
    # Internal state initialisation
    # -----------------------------------------------------------------
    def __init__(self) -> None:
        """Initialise the recogniser.

        * ``_candidate_gesture`` – the gesture currently being counted
          (or ``None`` if the last frame was invalid / unknown).
        * ``_prev_gesture`` – the last *confirmed* gesture that satisfied
          the stability requirement.
        * ``_consecutive_count`` – how many consecutive frames the current
          candidate has been observed.
        """
        self._candidate_gesture: str | None = None
        self._prev_gesture: str | None = None
        self._consecutive_count: int = 0

    # -----------------------------------------------------------------
    # Finger state detection
    # -----------------------------------------------------------------
    def get_finger_states(
        self,
        landmarks,
        handedness: str = "Right",
    ) -> list[bool]:
        """Determine which fingers are extended.

        Args:
            landmarks: MediaPipe NormalizedLandmarkList (has .landmark
                       attribute) OR a plain list/tuple of 21+ objects
                       each with ``.x`` and ``.y`` attributes.
            handedness: ``"Left"`` or ``"Right"`` (case-insensitive).
                        Determines the thumb direction rule.

        Returns:
            ``[thumb, index, middle, ring, pinky]`` — ``True`` = extended.

        Raises:
            ValueError: If the input is malformed or contains non-numeric
                        coordinates.
        """
        # --- Normalise handedness -------------------------------------------
        handedness_norm = handedness.strip().lower()
        if handedness_norm not in {"left", "right"}:
            raise ValueError(f"Invalid handedness: {handedness}")

        # --- Extract landmark list ------------------------------------------
        lm = _extract_landmarks(landmarks)
        if len(lm) < 21:
            raise ValueError("Expected at least 21 hand landmarks")

        # --- Validate required landmark coordinates -------------------------
        for i in _REQUIRED_INDICES:
            pt = lm[i]
            if not (_is_finite_number(getattr(pt, "x", None))
                    and _is_finite_number(getattr(pt, "y", None))):
                raise ValueError(f"Invalid coordinates for landmark {i}")

        # --- Thumb detection (x-axis, handedness-dependent) -----------------
        # Right hand: thumb tip is to the LEFT of the IP joint (smaller x).
        # Left hand:  thumb tip is to the RIGHT of the IP joint (larger x).
        thumb_extended: bool = (
            lm[THUMB_TIP].x < lm[THUMB_IP].x
            if handedness_norm == "right"
            else lm[THUMB_TIP].x > lm[THUMB_IP].x
        )

        # --- Four fingers (y-axis) ------------------------------------------
        # MediaPipe y increases downward, so a smaller tip.y means the
        # finger is pointing upward → extended.
        index_extended:  bool = lm[INDEX_TIP].y  < lm[INDEX_PIP].y
        middle_extended: bool = lm[MIDDLE_TIP].y < lm[MIDDLE_PIP].y
        ring_extended:   bool = lm[RING_TIP].y   < lm[RING_PIP].y
        pinky_extended:  bool = lm[PINKY_TIP].y  < lm[PINKY_PIP].y

        return [thumb_extended, index_extended, middle_extended,
                ring_extended, pinky_extended]

    # -----------------------------------------------------------------
    # Gesture classification + stability
    # -----------------------------------------------------------------
    def recognize(self, hand_landmarks, handedness: str = "Right") -> str:
        """Analyse hand landmarks and return a stable gesture key.

        Args:
            hand_landmarks: MediaPipe NormalizedLandmarkList with 21
                            landmarks, or equivalent sequence.
            handedness: ``"Left"`` or ``"Right"`` (case-insensitive).

        Returns:
            A key from ``config.GESTURE_MAP`` (e.g. ``"peace"``,
            ``"thumbs_up"``), or ``"unknown"`` when the gesture cannot
            be determined or has not yet met the stability threshold.
        """
        # --- Step 1: get finger states (resets on error) --------------------
        try:
            finger_states = self.get_finger_states(hand_landmarks, handedness)
        except Exception:
            # Invalid input → reset pending candidate and counter
            self._candidate_gesture = None
            self._consecutive_count = 0
            return "unknown"

        # --- Step 2: map finger pattern to a candidate gesture key ----------
        pattern = tuple(finger_states)

        # Lookup table  — (thumb, index, middle, ring, pinky) → gesture key
        _PATTERN_TO_GESTURE = {
            (True,  True,  True,  True,  True):  "open_palm",
            (False, False, False, False, False):  "fist",
            (True,  False, False, False, False):  "thumbs_up",   # refined below
            (False, True,  True,  False, False):  "peace",
            (False, True,  False, False, False):  "point",
            (False, True,  True,  True,  False):  "three",
            (False, True,  True,  True,  True):   "four",
            (False, True,  False, False, True):   "rock",
            (True,  False, False, False, True):   "call_me",
        }

        candidate = _PATTERN_TO_GESTURE.get(pattern, "unknown")

        # --- Step 3: thumbs-up vs thumbs-down direction check ---------------
        # Both gestures share the pattern (True, False, False, False, False).
        # We compare thumb tip Y with wrist Y to tell them apart.
        if candidate == "thumbs_up":          # the only key the pattern maps to
            lm = _extract_landmarks(hand_landmarks)
            thumb_tip_y = lm[THUMB_TIP].y
            wrist_y     = lm[WRIST].y

            if thumb_tip_y < wrist_y:
                candidate = "thumbs_up"       # tip above wrist → up
            elif thumb_tip_y > wrist_y:
                candidate = "thumbs_down"     # tip below wrist → down
            else:
                candidate = "unknown"         # ambiguous

        # --- Step 4: stability logic ----------------------------------------
        if candidate == "unknown":
            self._candidate_gesture = None
            self._consecutive_count = 0
            return "unknown"

        # Already confirmed and still the same → keep returning it
        if self._prev_gesture == candidate:
            return candidate

        # New or continuing candidate
        if self._candidate_gesture != candidate:
            # Different from what we were counting → start fresh
            self._candidate_gesture = candidate
            self._consecutive_count = 1
        else:
            self._consecutive_count += 1

        # Check if we have reached the stability threshold
        if self._consecutive_count >= GESTURE_STABILITY_FRAMES:
            self._prev_gesture = candidate
            return candidate

        # Not stable yet
        return "unknown"

    # -----------------------------------------------------------------
    # Optional manual reset
    # -----------------------------------------------------------------
    def reset(self) -> None:
        """Reset internal stability counters.

        Not used by the core recognition logic, but available for the
        GUI to call when the video stream is stopped and restarted.
        """
        self._candidate_gesture = None
        self._prev_gesture = None
        self._consecutive_count = 0
