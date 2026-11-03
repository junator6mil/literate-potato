"""
modules package — Core processing modules
==========================================
- camera.py          (TM2) — Webcam capture
- hand_detector.py   (TM3) — MediaPipe hand detection
- gesture_recognizer.py (TM4) — Rule-based gesture recognition
"""

from modules.camera import CameraManager
from modules.hand_detector import HandDetector
from modules.gesture_recognizer import GestureRecognizer

__all__ = ["CameraManager", "HandDetector", "GestureRecognizer"]
