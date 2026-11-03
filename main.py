"""
main.py — Application Entry Point
===================================
Wires together all modules and launches the application.

Owner: TM1 (Team Leader)

Usage:
    python main.py
"""

import sys
from modules.camera import CameraManager
from modules.hand_detector import HandDetector
from modules.gesture_recognizer import GestureRecognizer
from ui.app_window import AppWindow


def main():
    """Initialize all modules and start the application."""
    print("=" * 50)
    print("  Hand Sign Recognition — Starting...")
    print("=" * 50)

    # --- Initialize modules ---
    try:
        camera = CameraManager()
        print("[✓] Camera module initialized")
    except Exception as e:
        print(f"[✗] Camera module failed: {e}")
        sys.exit(1)

    try:
        detector = HandDetector()
        print("[✓] Hand detector initialized")
    except Exception as e:
        print(f"[✗] Hand detector failed: {e}")
        sys.exit(1)

    try:
        recognizer = GestureRecognizer()
        print("[✓] Gesture recognizer initialized")
    except Exception as e:
        print(f"[✗] Gesture recognizer failed: {e}")
        sys.exit(1)

    # --- Launch the GUI (this blocks until window is closed) ---
    try:
        print("[✓] Launching GUI...")
        print("=" * 50)
        app = AppWindow(camera, detector, recognizer)
        app.run()
    except Exception as e:
        print(f"[✗] Application error: {e}")
    finally:
        # Clean up all resources
        print("\nShutting down...")
        try:
            camera.stop()
        except Exception:
            pass
        try:
            detector.close()
        except Exception:
            pass
        print("Goodbye!")


if __name__ == "__main__":
    main()
