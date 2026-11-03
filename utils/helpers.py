"""
utils/helpers.py — Shared Utility Functions
============================================
Reusable helpers used across multiple modules.

Owner: TM1 (Team Leader)
"""

import time


class FPSCounter:
    """Tracks and calculates frames per second for performance monitoring."""

    def __init__(self, avg_over: int = 30):
        """
        Args:
            avg_over: Number of frames to average FPS over.
        """
        self._avg_over = avg_over
        self._timestamps: list[float] = []

    def tick(self) -> float:
        """Call once per frame. Returns the current average FPS."""
        now = time.time()
        self._timestamps.append(now)

        # Keep only the last N timestamps
        if len(self._timestamps) > self._avg_over:
            self._timestamps = self._timestamps[-self._avg_over:]

        if len(self._timestamps) < 2:
            return 0.0

        elapsed = self._timestamps[-1] - self._timestamps[0]
        if elapsed == 0:
            return 0.0

        return (len(self._timestamps) - 1) / elapsed

    def reset(self):
        """Reset the FPS counter."""
        self._timestamps.clear()


def format_gesture_text(gesture_history: list[str], separator: str = " → ") -> str:
    """
    Format a list of recognized gestures into a display string.

    Args:
        gesture_history: List of gesture text strings (e.g., ["Hello", "Peace", "Yes"])
        separator: String to join gestures with.

    Returns:
        Formatted string like "Hello → Peace → Yes"
    """
    if not gesture_history:
        return "No gestures detected yet"
    return separator.join(gesture_history)


def safe_cleanup(*closeable_objects):
    """
    Safely call close/stop/release on multiple objects.
    Ignores any errors during cleanup so the app exits cleanly.

    Args:
        closeable_objects: Objects that have close(), stop(), or release() methods.
    """
    for obj in closeable_objects:
        for method_name in ("stop", "close", "release"):
            method = getattr(obj, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception:
                    pass
                break
