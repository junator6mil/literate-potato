"""
modules/camera.py — Webcam Capture Module
===========================================
OWNER: TM2 — Camera Module Developer

Provides the CameraManager class for webcam access.

INTERFACE CONTRACT (DO NOT change these method signatures):
    class CameraManager:
        def start(self) -> bool
        def read_frame(self) -> tuple[bool, numpy.ndarray | None]
        def stop(self) -> None
        def is_opened(self) -> bool

See config.py for: CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT
"""

# TODO: TM2 — Replace this stub with your implementation
# This stub exists so other modules can import without errors during development.

import numpy as np
from config import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT


class CameraManager:
    """Manages webcam capture using OpenCV."""

    def __init__(self, camera_index: int = CAMERA_INDEX):
        self._camera_index = camera_index
        self._cap = None

    def start(self) -> bool:
        """Open the camera. Returns True if successful."""
        raise NotImplementedError("TM2: Implement camera start()")

    def read_frame(self) -> tuple:
        """Read a single frame. Returns (success: bool, frame: np.ndarray or None)."""
        raise NotImplementedError("TM2: Implement read_frame()")

    def stop(self) -> None:
        """Release the camera resource."""
        raise NotImplementedError("TM2: Implement camera stop()")

    def is_opened(self) -> bool:
        """Check if the camera is currently active."""
        raise NotImplementedError("TM2: Implement is_opened()")
