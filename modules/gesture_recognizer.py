"""
modules/gesture_recognizer.py — Rule-Based Gesture Recognition
================================================================
OWNER: TM4 — Gesture Recognition Developer

Provides the GestureRecognizer class that analyzes MediaPipe hand landmarks
to determine which gesture is being made.

IMPLEMENTATION ADAPTED FROM:
    TM3's standalone module at gesture_recognition/recognizer.py
    Original standalone functions have been wrapped in the GestureRecognizer
    class to match the team's interface contract.

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

import math
from config import GESTURE_MAP, GESTURE_STABILITY_FRAMES


# ═══════════════════════════════════════════════════════════════════
# LANDMARK INDEX CONSTANTS
# ═══════════════════════════════════════════════════════════════════
# Named constants for each of the 21 hand landmarks.
# These are identical to the ones in config.py's LANDMARK_NAMES but
# stored as simple integers for fast access in recognition logic.

WRIST = 0

# Thumb
THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP  = 3
THUMB_TIP = 4

# Index finger
INDEX_MCP = 5
INDEX_PIP = 6
INDEX_DIP = 7
INDEX_TIP = 8

# Middle finger
MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12

# Ring finger
RING_MCP = 13
RING_PIP = 14
RING_DIP = 15
RING_TIP = 16

# Pinky
PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS — LANDMARK COORDINATE ACCESS
# ═══════════════════════════════════════════════════════════════════
# MediaPipe landmarks can come in different forms:
#   1. From mp.solutions.hands:  results.multi_hand_landmarks[0].landmark[i]
#      -> each has .x, .y, .z attributes
#   2. As tuples: (x, y, z) from manual conversion
#
# These helpers handle both formats using hasattr().

def _get_x(landmark):
    """Get x-coordinate from a landmark (supports .x attribute or tuple)."""
    if hasattr(landmark, 'x'):
        return landmark.x
    return landmark[0]


def _get_y(landmark):
    """Get y-coordinate (y=0 is TOP, y=1 is BOTTOM of image)."""
    if hasattr(landmark, 'y'):
        return landmark.y
    return landmark[1]


# ═══════════════════════════════════════════════════════════════════
# FINGER STATE DETECTION — CORE LOGIC
# ═══════════════════════════════════════════════════════════════════
# A finger is "extended" when its tip is ABOVE (lower y value) its
# PIP joint.  The thumb is special — it moves sideways, so we check
# x-coordinates and use the handedness parameter to know which
# direction means "extended".

def _is_finger_extended(landmarks, tip_idx, pip_idx, mcp_idx):
    """
    Check if a non-thumb finger is extended (pointing upward).

    Logic: tip.y < pip.y AND tip.y < mcp.y
    (lower y = higher on screen = finger pointing up)
    """
    tip_y = _get_y(landmarks[tip_idx])
    pip_y = _get_y(landmarks[pip_idx])
    mcp_y = _get_y(landmarks[mcp_idx])
    return tip_y < pip_y and tip_y < mcp_y


def _is_thumb_extended(landmarks, is_right_hand):
    """
    Check if the thumb is extended outward from the palm.

    Uses x-coordinates because the thumb moves sideways:
    - Right hand: thumb extends LEFT  -> thumb_tip.x < thumb_ip.x
    - Left hand:  thumb extends RIGHT -> thumb_tip.x > thumb_ip.x

    Args:
        landmarks: list of 21 landmark objects
        is_right_hand: True if the hand is a right hand
    """
    thumb_tip_x = _get_x(landmarks[THUMB_TIP])
    thumb_ip_x  = _get_x(landmarks[THUMB_IP])
    thumb_mcp_x = _get_x(landmarks[THUMB_MCP])

    min_extension = 0.02  # minimum distance to count as extended

    if is_right_hand:
        return (thumb_tip_x < thumb_ip_x and
                abs(thumb_tip_x - thumb_mcp_x) > min_extension)
    else:
        return (thumb_tip_x > thumb_ip_x and
                abs(thumb_tip_x - thumb_mcp_x) > min_extension)


def _is_thumb_pointing_up(landmarks):
    """
    Check if thumb points UPWARD (for thumbs_up gesture).
    Thumb tip must be significantly above thumb MCP and above wrist.
    """
    thumb_tip_y = _get_y(landmarks[THUMB_TIP])
    thumb_mcp_y = _get_y(landmarks[THUMB_MCP])
    wrist_y     = _get_y(landmarks[WRIST])
    return (thumb_tip_y < thumb_mcp_y - 0.05 and
            thumb_tip_y < wrist_y)


def _is_thumb_pointing_down(landmarks):
    """
    Check if thumb points DOWNWARD (for thumbs_down gesture).
    Thumb tip must be significantly below thumb MCP and below wrist.
    """
    thumb_tip_y = _get_y(landmarks[THUMB_TIP])
    thumb_mcp_y = _get_y(landmarks[THUMB_MCP])
    wrist_y     = _get_y(landmarks[WRIST])
    return (thumb_tip_y > thumb_mcp_y + 0.05 and
            thumb_tip_y > wrist_y)


# ═══════════════════════════════════════════════════════════════════
# THE GESTURE RECOGNIZER CLASS
# ═══════════════════════════════════════════════════════════════════
# This class wraps the recognition logic to match the team's
# interface contract.  The key differences from the standalone
# module:
#   1. Methods live on a class instead of being module-level functions
#   2. "handedness" is passed in explicitly (not auto-detected)
#   3. Return values are lowercase config.py keys, not uppercase labels
#   4. None is mapped to "unknown"

class GestureRecognizer:
    """Classifies hand gestures using rule-based finger position analysis."""

    def __init__(self):
        # Validate that our gesture keys match config.GESTURE_MAP
        self._required_keys = set(GESTURE_MAP.keys()) - {"unknown"}

    def get_finger_states(self, landmarks, handedness: str = "Right") -> list:
        """
        Determine which fingers are extended.

        Args:
            landmarks: MediaPipe NormalizedLandmarkList (has .landmark attribute)
                       OR a plain list of 21 objects with .x, .y, .z
            handedness: "Left" or "Right" (from MediaPipe multi_handedness)

        Returns:
            List of 5 booleans: [thumb, index, middle, ring, pinky]
            True means the finger is extended/open.
        """
        # Normalize input: if it's a NormalizedLandmarkList, access .landmark
        lm = self._normalize_landmarks(landmarks)
        if lm is None:
            return [False, False, False, False, False]

        is_right = (handedness == "Right")

        thumb  = _is_thumb_extended(lm, is_right)
        index  = _is_finger_extended(lm, INDEX_TIP,  INDEX_PIP,  INDEX_MCP)
        middle = _is_finger_extended(lm, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP)
        ring   = _is_finger_extended(lm, RING_TIP,   RING_PIP,   RING_MCP)
        pinky  = _is_finger_extended(lm, PINKY_TIP,  PINKY_PIP,  PINKY_MCP)

        return [thumb, index, middle, ring, pinky]

    def recognize(self, hand_landmarks, handedness: str = "Right") -> str:
        """
        Analyze hand landmarks and return the gesture name.

        Args:
            hand_landmarks: MediaPipe NormalizedLandmarkList with 21 landmarks.
                            OR a plain list of 21 objects with .x, .y, .z
            handedness: "Left" or "Right" — needed for thumb detection.

        Returns:
            A key from config.GESTURE_MAP (e.g., "thumbs_up", "peace", "unknown")
        """
        # Normalize input
        lm = self._normalize_landmarks(hand_landmarks)
        if lm is None:
            return "unknown"

        # Get finger states
        fingers = self.get_finger_states(hand_landmarks, handedness)
        thumb, index, middle, ring, pinky = fingers
        extended_count = sum(fingers)

        # ─── GESTURE MATCHING (most specific → least specific) ───

        # THUMBS UP: only thumb visible, pointing upward
        if (not index and not middle and not ring and not pinky
                and _is_thumb_pointing_up(lm)):
            return "thumbs_up"

        # THUMBS DOWN: only thumb visible, pointing downward
        if (not index and not middle and not ring and not pinky
                and _is_thumb_pointing_down(lm)):
            return "thumbs_down"

        # FIST: all fingers curled
        if extended_count == 0:
            return "fist"

        # POINT: only index finger extended
        if not thumb and index and not middle and not ring and not pinky:
            return "point"

        # PEACE (V sign): index + middle extended, rest curled
        if not thumb and index and middle and not ring and not pinky:
            return "peace"

        # THREE: index + middle + ring extended
        if not thumb and index and middle and ring and not pinky:
            return "three"

        # FOUR: all except thumb extended
        if not thumb and index and middle and ring and pinky:
            return "four"

        # ROCK: index + pinky extended (devil horns)
        if not thumb and index and not middle and not ring and pinky:
            return "rock"

        # CALL ME: thumb + pinky extended
        if thumb and not index and not middle and not ring and pinky:
            return "call_me"

        # OPEN PALM: all (or 4+) fingers extended
        if index and middle and ring and pinky and extended_count >= 4:
            return "open_palm"

        # No match
        return "unknown"

    def _normalize_landmarks(self, landmarks):
        """
        Convert various landmark input formats to a plain list.

        MediaPipe results come as NormalizedLandmarkList objects
        which have a .landmark attribute containing the actual list.
        TM2's hand_detector passes these directly.

        We also handle plain lists (for testing) and validate length.

        Returns:
            list of 21 landmarks, or None if input is invalid.
        """
        if landmarks is None:
            return None

        # If it's a MediaPipe NormalizedLandmarkList, extract .landmark
        if hasattr(landmarks, 'landmark'):
            lm = landmarks.landmark
        else:
            lm = landmarks

        # Validate length
        try:
            if len(lm) != 21:
                return None
        except TypeError:
            return None

        return lm
