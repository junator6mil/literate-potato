"""
Camera Module — modules/camera.py
Team Member 2 (TM2): Camera Module Developer

Provides the CameraManager class for webcam access and frame capture
using OpenCV's VideoCapture. All configuration values are imported
from the shared config.py so nothing is hardcoded here.
"""

import cv2
from config import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT


class CameraManager:
    """Manages webcam access: opening, reading frames, and releasing."""

    def __init__(self, camera_index: int = CAMERA_INDEX):
        """
        Initialize the CameraManager.

        Args:
            camera_index: Index of the camera device to use.
                          Defaults to CAMERA_INDEX from config.py (typically 0).
        """
        self._camera_index = camera_index
        self._cap = None  # Will hold the cv2.VideoCapture object once started

    # ------------------------------------------------------------------
    # Public API (must match the interface contract exactly)
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """
        Open the webcam and configure frame dimensions.

        Returns:
            True if the camera opened successfully, False otherwise.
        """
        try:
            # Create the VideoCapture object for the chosen camera index
            self._cap = cv2.VideoCapture(self._camera_index)

            # Check if the camera was opened successfully
            if not self._cap.isOpened():
                print(f"[CameraManager] ERROR: Could not open camera at index {self._camera_index}.")
                self._cap = None
                return False

            # Set the desired frame width and height from config
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

            # Log the actual resolution the camera settled on
            actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"[CameraManager] Camera opened successfully. Resolution: {actual_w}x{actual_h}")

            return True

        except Exception as e:
            print(f"[CameraManager] ERROR: Exception while opening camera: {e}")
            self._cap = None
            return False

    def read_frame(self) -> tuple:
        """
        Read a single frame from the webcam.

        Returns:
            A tuple (success, frame):
              - success (bool): True if a frame was read, False on failure.
              - frame (numpy.ndarray or None): The BGR image, or None on failure.
        """
        # Guard: camera must be started first
        if self._cap is None or not self._cap.isOpened():
            return (False, None)

        try:
            success, frame = self._cap.read()
            if not success:
                # read() can fail if the camera is disconnected mid-session
                return (False, None)
            return (success, frame)

        except Exception as e:
            print(f"[CameraManager] ERROR: Exception while reading frame: {e}")
            return (False, None)

    def stop(self) -> None:
        """
        Release the webcam and free all associated resources.
        Safe to call multiple times.
        """
        if self._cap is not None:
            self._cap.release()
            print("[CameraManager] Camera released.")
            self._cap = None

    def is_opened(self) -> bool:
        """
        Check whether the camera is currently active.

        Returns:
            True if the camera is open and ready, False otherwise.
        """
        if self._cap is not None:
            return self._cap.isOpened()
        return False

    # ------------------------------------------------------------------
    # Safety cleanup
    # ------------------------------------------------------------------

    def __del__(self):
        """
        Destructor — ensures the camera is released if the object is
        garbage-collected without an explicit stop() call.
        """
        self.stop()
