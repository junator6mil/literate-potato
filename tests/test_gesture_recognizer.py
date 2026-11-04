"""
tests/test_gesture_recognizer.py
================================
Test suite for the GestureRecognizer class in modules/gesture_recognizer.py.

Tests the team-integrated version that wraps TM3's recognition algorithm
into the GestureRecognizer class with the team's interface contract:
    - recognize(hand_landmarks, handedness) -> str  (config.py keys)
    - get_finger_states(landmarks, handedness) -> list[bool]

Run from the literate-potato repo root:
    python tests/test_gesture_recognizer.py

Author: Team Member 3
"""

import sys
import os

# Add the repo root to sys.path so we can import config and modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.gesture_recognizer import GestureRecognizer
from config import GESTURE_MAP


# ═══════════════════════════════════════════════════════════════════
# SIMULATED LANDMARK DATA
# ═══════════════════════════════════════════════════════════════════
# We create simple objects with .x, .y, .z to mimic MediaPipe's
# NormalizedLandmark objects without needing MediaPipe installed.

class FakeLandmark:
    """Mimics MediaPipe's NormalizedLandmark with .x, .y, .z attributes."""
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class FakeLandmarkList:
    """Mimics MediaPipe's NormalizedLandmarkList with .landmark attribute."""
    def __init__(self, landmarks):
        self.landmark = landmarks


def _make_base_landmarks():
    """
    Create a base set of 21 landmarks representing a RIGHT-HAND FIST.
    All fingertips are positioned BELOW their PIP joints (curled).
    Wrist at (0.45, 0.85), middle_mcp at (0.50, 0.65) -> right hand.
    """
    lm = [None] * 21

    # Wrist
    lm[0] = FakeLandmark(0.45, 0.85)

    # Thumb (curled into palm) - right hand, so tip.x > ip.x = curled
    lm[1] = FakeLandmark(0.40, 0.75)   # THUMB_CMC
    lm[2] = FakeLandmark(0.38, 0.70)   # THUMB_MCP
    lm[3] = FakeLandmark(0.40, 0.67)   # THUMB_IP
    lm[4] = FakeLandmark(0.42, 0.65)   # THUMB_TIP (x > ip.x = curled for right)

    # Index (curled: tip.y > pip.y)
    lm[5] = FakeLandmark(0.48, 0.65)   # INDEX_MCP
    lm[6] = FakeLandmark(0.48, 0.58)   # INDEX_PIP
    lm[7] = FakeLandmark(0.48, 0.62)   # INDEX_DIP
    lm[8] = FakeLandmark(0.48, 0.65)   # INDEX_TIP (below PIP = curled)

    # Middle (curled)
    lm[9]  = FakeLandmark(0.50, 0.65)  # MIDDLE_MCP
    lm[10] = FakeLandmark(0.50, 0.56)  # MIDDLE_PIP
    lm[11] = FakeLandmark(0.50, 0.60)  # MIDDLE_DIP
    lm[12] = FakeLandmark(0.50, 0.64)  # MIDDLE_TIP (below PIP = curled)

    # Ring (curled)
    lm[13] = FakeLandmark(0.52, 0.65)  # RING_MCP
    lm[14] = FakeLandmark(0.52, 0.58)  # RING_PIP
    lm[15] = FakeLandmark(0.52, 0.62)  # RING_DIP
    lm[16] = FakeLandmark(0.52, 0.65)  # RING_TIP (below PIP = curled)

    # Pinky (curled)
    lm[17] = FakeLandmark(0.55, 0.68)  # PINKY_MCP
    lm[18] = FakeLandmark(0.55, 0.62)  # PINKY_PIP
    lm[19] = FakeLandmark(0.55, 0.65)  # PINKY_DIP
    lm[20] = FakeLandmark(0.55, 0.68)  # PINKY_TIP (below PIP = curled)

    return lm


def _extend_finger(lm, tip_idx, pip_idx, mcp_idx):
    """Move fingertip ABOVE pip and mcp (tip.y < pip.y)."""
    pip_y = lm[pip_idx].y
    lm[tip_idx] = FakeLandmark(lm[tip_idx].x, pip_y - 0.15)


def _extend_thumb(lm):
    """Extend thumb outward for a right hand (tip.x < ip.x)."""
    lm[4] = FakeLandmark(0.30, 0.60)   # TIP far left
    lm[3] = FakeLandmark(0.38, 0.62)   # IP
    lm[2] = FakeLandmark(0.40, 0.65)   # MCP


def _thumb_pointing_up(lm):
    """Position thumb tip pointing upward (tip.y << mcp.y and < wrist.y)."""
    lm[4] = FakeLandmark(0.38, 0.45)   # TIP very high
    lm[3] = FakeLandmark(0.38, 0.60)   # IP
    lm[2] = FakeLandmark(0.38, 0.65)   # MCP


def _thumb_pointing_down(lm):
    """Position thumb tip pointing downward (tip.y >> mcp.y and > wrist.y)."""
    lm[4] = FakeLandmark(0.38, 0.95)   # TIP very low
    lm[3] = FakeLandmark(0.38, 0.80)   # IP
    lm[2] = FakeLandmark(0.38, 0.75)   # MCP
    lm[0] = FakeLandmark(0.45, 0.60)   # Wrist above tip


# ═══════════════════════════════════════════════════════════════════
# GESTURE BUILDERS — create landmarks for each specific gesture
# ═══════════════════════════════════════════════════════════════════

def make_fist():
    return _make_base_landmarks()

def make_open_palm():
    lm = _make_base_landmarks()
    _extend_thumb(lm)
    _extend_finger(lm, 8, 6, 5)     # Index
    _extend_finger(lm, 12, 10, 9)   # Middle
    _extend_finger(lm, 16, 14, 13)  # Ring
    _extend_finger(lm, 20, 18, 17)  # Pinky
    return lm

def make_thumbs_up():
    lm = _make_base_landmarks()
    _thumb_pointing_up(lm)
    return lm

def make_thumbs_down():
    lm = _make_base_landmarks()
    _thumb_pointing_down(lm)
    return lm

def make_peace():
    lm = _make_base_landmarks()
    _extend_finger(lm, 8, 6, 5)     # Index
    _extend_finger(lm, 12, 10, 9)   # Middle
    return lm

def make_point():
    lm = _make_base_landmarks()
    _extend_finger(lm, 8, 6, 5)     # Index only
    return lm

def make_three():
    lm = _make_base_landmarks()
    _extend_finger(lm, 8, 6, 5)     # Index
    _extend_finger(lm, 12, 10, 9)   # Middle
    _extend_finger(lm, 16, 14, 13)  # Ring
    return lm

def make_four():
    lm = _make_base_landmarks()
    _extend_finger(lm, 8, 6, 5)     # Index
    _extend_finger(lm, 12, 10, 9)   # Middle
    _extend_finger(lm, 16, 14, 13)  # Ring
    _extend_finger(lm, 20, 18, 17)  # Pinky
    return lm

def make_rock():
    lm = _make_base_landmarks()
    _extend_finger(lm, 8, 6, 5)     # Index
    _extend_finger(lm, 20, 18, 17)  # Pinky
    return lm

def make_call_me():
    lm = _make_base_landmarks()
    _extend_thumb(lm)
    _extend_finger(lm, 20, 18, 17)  # Pinky
    return lm


# ═══════════════════════════════════════════════════════════════════
# TEST RUNNER
# ═══════════════════════════════════════════════════════════════════

def run_tests():
    recognizer = GestureRecognizer()
    passed = 0
    failed = 0
    total = 0

    print("=" * 68)
    print("  GESTURE RECOGNIZER - TEAM INTEGRATION TEST SUITE")
    print("  Tests modules/gesture_recognizer.py (GestureRecognizer class)")
    print("=" * 68)
    print()

    # ── Test 1: All 10 gesture recognitions ──────────────────────
    print("Part 1: Gesture Recognition Tests (recognize method)")
    print()
    print("  {:<20s} {:<16s} {:<16s} {:<8s}".format(
        "Gesture", "Expected", "Got", "Status"))
    print("  {:<20s} {:<16s} {:<16s} {:<8s}".format(
        "-" * 20, "-" * 16, "-" * 16, "-" * 8))

    gesture_tests = [
        ("open_palm",    make_open_palm()),
        ("fist",         make_fist()),
        ("thumbs_up",    make_thumbs_up()),
        ("thumbs_down",  make_thumbs_down()),
        ("peace",        make_peace()),
        ("point",        make_point()),
        ("three",        make_three()),
        ("four",         make_four()),
        ("rock",         make_rock()),
        ("call_me",      make_call_me()),
    ]

    for expected, landmarks in gesture_tests:
        total += 1
        result = recognizer.recognize(landmarks, "Right")
        ok = (result == expected)
        status = "[PASS]" if ok else "[FAIL]"
        if ok:
            passed += 1
        else:
            failed += 1
        print("  {:<20s} {:<16s} {:<16s} {:<8s}".format(
            expected, expected, result, status))

    print()

    # ── Test 2: NormalizedLandmarkList wrapper ────────────────────
    print("Part 2: MediaPipe NormalizedLandmarkList Compatibility")
    print()

    total += 1
    wrapped = FakeLandmarkList(make_thumbs_up())
    result = recognizer.recognize(wrapped, "Right")
    ok = (result == "thumbs_up")
    status = "[PASS]" if ok else "[FAIL]"
    if ok:
        passed += 1
    else:
        failed += 1
    print("  NormalizedLandmarkList  expected=thumbs_up  got={}  {}".format(
        result, status))

    print()

    # ── Test 3: Handedness (Left hand) ───────────────────────────
    print("Part 3: Handedness Tests (Left hand)")
    print()

    # For left hand: thumb extends RIGHT (tip.x > ip.x)
    total += 1
    lm_left = _make_base_landmarks()
    # Flip wrist/middle_mcp for left hand
    lm_left[0] = FakeLandmark(0.55, 0.85)   # Wrist to the RIGHT
    lm_left[9] = FakeLandmark(0.50, 0.65)   # Middle MCP to the LEFT
    # Left hand thumb extends RIGHT
    lm_left[4] = FakeLandmark(0.70, 0.60)   # TIP far right
    lm_left[3] = FakeLandmark(0.62, 0.62)   # IP
    lm_left[2] = FakeLandmark(0.60, 0.65)   # MCP
    _extend_finger(lm_left, 20, 18, 17)     # Pinky
    result = recognizer.recognize(lm_left, "Left")
    ok = (result == "call_me")
    status = "[PASS]" if ok else "[FAIL]"
    if ok:
        passed += 1
    else:
        failed += 1
    print("  Left-hand call_me     expected=call_me    got={}  {}".format(
        result, status))

    print()

    # ── Test 4: get_finger_states ────────────────────────────────
    print("Part 4: Finger States Test (get_finger_states method)")
    print()

    total += 1
    states = recognizer.get_finger_states(make_open_palm(), "Right")
    all_extended = all(states)
    status = "[PASS]" if all_extended else "[FAIL]"
    if all_extended:
        passed += 1
    else:
        failed += 1
    finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
    for name, state in zip(finger_names, states):
        print("  {:10s} -> {}".format(name, "Extended" if state else "Curled"))
    print("  All extended for OPEN_PALM: {}".format(status))

    total += 1
    states_fist = recognizer.get_finger_states(make_fist(), "Right")
    none_extended = not any(states_fist)
    status = "[PASS]" if none_extended else "[FAIL]"
    if none_extended:
        passed += 1
    else:
        failed += 1
    print("  All curled for FIST:        {}".format(status))

    print()

    # ── Test 5: Edge cases ───────────────────────────────────────
    print("Part 5: Edge Cases")
    print()

    edge_tests = [
        ("None input",         None,             "unknown"),
        ("Empty list",         [],               "unknown"),
        ("Too few landmarks",  [FakeLandmark(0,0)] * 5,  "unknown"),
        ("Too many landmarks", [FakeLandmark(0,0)] * 30, "unknown"),
    ]

    for name, input_data, expected in edge_tests:
        total += 1
        result = recognizer.recognize(input_data, "Right")
        ok = (result == expected)
        status = "[PASS]" if ok else "[FAIL]"
        if ok:
            passed += 1
        else:
            failed += 1
        print("  {:<22s} expected={:<10s} got={:<10s} {}".format(
            name, expected, result, status))

    print()

    # ── Test 6: All returned keys exist in config.GESTURE_MAP ────
    print("Part 6: Config Compatibility Check")
    print()

    total += 1
    all_results = set()
    for _, landmarks in gesture_tests:
        r = recognizer.recognize(landmarks, "Right")
        all_results.add(r)
    all_results.add("unknown")  # Add the fallback

    missing = all_results - set(GESTURE_MAP.keys())
    ok = len(missing) == 0
    status = "[PASS]" if ok else "[FAIL]"
    if ok:
        passed += 1
    else:
        failed += 1
    print("  All returned keys in GESTURE_MAP: {}".format(status))
    if missing:
        print("  MISSING KEYS: {}".format(missing))

    total += 1
    unimplemented = set(GESTURE_MAP.keys()) - all_results
    ok2 = len(unimplemented) == 0
    status2 = "[PASS]" if ok2 else "[FAIL]"
    if ok2:
        passed += 1
    else:
        failed += 1
    print("  All GESTURE_MAP keys covered:     {}".format(status2))
    if unimplemented:
        print("  UNCOVERED KEYS: {}".format(unimplemented))

    print()

    # ── Summary ──────────────────────────────────────────────────
    print("=" * 68)
    if failed == 0:
        print("  RESULTS: {}/{} tests passed -- ALL TESTS PASSED!".format(
            passed, total))
    else:
        print("  RESULTS: {}/{} tests passed ({} FAILED)".format(
            passed, total, failed))
    print("=" * 68)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
