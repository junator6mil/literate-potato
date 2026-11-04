"""
ui/app_window.py — Tkinter Desktop GUI for Hand Sign Recognition
================================================================
Team Member 5 (GUI Developer)

This module creates the main application window using Tkinter.
It connects the camera, hand detector, and gesture recognizer modules
and displays everything in a clean, user-friendly interface.

Layout:
┌─────────────────────────────────────────────────┐
│              Hand Sign Recognition              │  ← Title bar
├───────────────────────┬─────────────────────────┤
│                       │  Current Gesture:       │
│                       │  ┌───────────────────┐  │
│   Live Camera Feed    │  │   "Hello"         │  │  ← Gesture label
│   (640 × 480)         │  └───────────────────┘  │
│                       │                         │
│                       │  Recognized Text:       │
│                       │  ┌───────────────────┐  │
│                       │  │ Hello              │  │  ← Accumulated text
│                       │  │ Yes                │  │
│                       │  │ Peace              │  │
│                       │  └───────────────────┘  │
├───────────────────────┴─────────────────────────┤
│  [ Start Camera ] [ Stop Camera ] [ Clear ] [X] │  ← Buttons
├─────────────────────────────────────────────────┤
│  Status: Camera running — Detecting gestures    │  ← Status bar
└─────────────────────────────────────────────────┘
"""

import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk
import cv2
import sys

# ---------------------------------------------------------------------------
# Try to import shared config; fall back to sensible defaults so the GUI
# can still be tested before TM1 pushes config.py.
# ---------------------------------------------------------------------------
try:
    import config
    VIDEO_WIDTH = getattr(config, "VIDEO_WIDTH", 640)
    VIDEO_HEIGHT = getattr(config, "VIDEO_HEIGHT", 480)
    UPDATE_INTERVAL_MS = getattr(config, "UPDATE_INTERVAL_MS", 30)
    WINDOW_TITLE = getattr(config, "WINDOW_TITLE", "Hand Sign Recognition")
    GESTURE_STABILITY_FRAMES = getattr(config, "GESTURE_STABILITY_FRAMES", 15)
except ImportError:
    VIDEO_WIDTH = 640
    VIDEO_HEIGHT = 480
    UPDATE_INTERVAL_MS = 30
    WINDOW_TITLE = "Hand Sign Recognition"
    GESTURE_STABILITY_FRAMES = 15


# =====================================================================
# Colour palette & style constants (easy to tweak in one place)
# =====================================================================
_BG_DARK = "#1e1e2e"        # Main background (dark charcoal)
_BG_PANEL = "#2a2a3c"       # Side-panel background
_BG_BUTTON = "#3b3b50"      # Button background
_BG_BUTTON_HOVER = "#50506a"  # Button hover
_BG_ACCENT = "#7c3aed"      # Accent purple
_BG_DANGER = "#ef4444"      # Exit button red
_FG_PRIMARY = "#e2e2e2"     # Primary text
_FG_SECONDARY = "#a0a0b8"   # Secondary / muted text
_FG_GESTURE = "#38bdf8"     # Gesture name (bright cyan)
_FG_ACCENT = "#ffffff"      # Accent text (white on purple)
_BORDER_COLOR = "#3b3b50"   # Subtle border colour


class AppWindow:
    """
    Main application window for the Hand Sign Recognition app.

    Parameters
    ----------
    camera : CameraManager
        Instance from modules/camera.py (TM2).
    detector : HandDetector
        Instance from modules/hand_detector.py (TM3).
    recognizer : GestureRecognizer
        Instance from modules/gesture_recognizer.py (TM4).
    """

    def __init__(self, camera, detector, recognizer):
        # ---- Store references to the other team members' modules ----
        self.camera = camera
        self.detector = detector
        self.recognizer = recognizer

        # ---- Internal state ----
        self._is_running = False          # True while the camera loop is active
        self._update_job = None           # Tkinter after() job id
        self._photo_image = None          # Keep a reference so GC doesn't discard it
        self._last_gesture = ""           # Previous frame's gesture
        self._gesture_counter = 0         # Consecutive frames with the same gesture
        self._confirmed_gesture = ""      # Gesture displayed to the user

        # ---- Build the Tkinter UI ----
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.configure(bg=_BG_DARK)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)

        # Fonts
        self._font_title = tkfont.Font(family="Segoe UI", size=18, weight="bold")
        self._font_heading = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        self._font_gesture = tkfont.Font(family="Segoe UI", size=28, weight="bold")
        self._font_button = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self._font_status = tkfont.Font(family="Segoe UI", size=9)
        self._font_text = tkfont.Font(family="Consolas", size=11)

        self._build_layout()

    # =================================================================
    # Layout Construction
    # =================================================================

    def _build_layout(self):
        """Construct every widget and grid them into the window."""

        # ---- Title Banner ----
        title_frame = tk.Frame(self.root, bg=_BG_ACCENT, pady=8)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        tk.Label(
            title_frame,
            text="✋  Hand Sign Recognition",
            font=self._font_title,
            bg=_BG_ACCENT,
            fg=_FG_ACCENT,
        ).pack()

        # ---- Main Content Area ----
        content_frame = tk.Frame(self.root, bg=_BG_DARK, padx=10, pady=10)
        content_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # -- Left: Video Feed --
        video_frame = tk.Frame(
            content_frame, bg=_BORDER_COLOR, padx=2, pady=2
        )
        video_frame.grid(row=0, column=0, padx=(0, 10), sticky="n")

        self.video_label = tk.Label(
            video_frame,
            bg="#000000",
            width=VIDEO_WIDTH,
            height=VIDEO_HEIGHT,
        )
        self.video_label.pack()

        # -- Right: Info Panel --
        info_frame = tk.Frame(content_frame, bg=_BG_PANEL, padx=16, pady=16, width=300)
        info_frame.grid(row=0, column=1, sticky="nsew")
        info_frame.grid_propagate(False)
        info_frame.configure(width=300)

        # Current Gesture heading
        tk.Label(
            info_frame,
            text="CURRENT GESTURE",
            font=self._font_heading,
            bg=_BG_PANEL,
            fg=_FG_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        # Gesture display box
        gesture_box = tk.Frame(info_frame, bg=_BG_DARK, padx=12, pady=14)
        gesture_box.pack(fill="x", pady=(0, 20))

        self.gesture_var = tk.StringVar(value="No hand detected")
        self.gesture_label = tk.Label(
            gesture_box,
            textvariable=self.gesture_var,
            font=self._font_gesture,
            bg=_BG_DARK,
            fg=_FG_GESTURE,
            anchor="center",
        )
        self.gesture_label.pack(fill="x")

        # Separator
        tk.Frame(info_frame, bg=_BORDER_COLOR, height=1).pack(fill="x", pady=(0, 14))

        # Recognized Text heading
        tk.Label(
            info_frame,
            text="RECOGNIZED TEXT",
            font=self._font_heading,
            bg=_BG_PANEL,
            fg=_FG_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        # Text area (scrollable)
        text_wrapper = tk.Frame(info_frame, bg=_BORDER_COLOR, padx=1, pady=1)
        text_wrapper.pack(fill="both", expand=True)

        self.text_area = tk.Text(
            text_wrapper,
            font=self._font_text,
            bg=_BG_DARK,
            fg=_FG_PRIMARY,
            insertbackground=_FG_PRIMARY,
            selectbackground=_BG_ACCENT,
            relief="flat",
            wrap="word",
            state="disabled",       # Read-only; we insert programmatically
            padx=8,
            pady=8,
        )
        self.text_area.pack(fill="both", expand=True, side="left")

        scrollbar = tk.Scrollbar(
            text_wrapper, command=self.text_area.yview, bg=_BG_DARK,
            troughcolor=_BG_PANEL, activebackground=_BG_BUTTON_HOVER,
        )
        scrollbar.pack(fill="y", side="right")
        self.text_area.configure(yscrollcommand=scrollbar.set)

        # ---- Button Bar ----
        button_frame = tk.Frame(self.root, bg=_BG_DARK, pady=8)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

        # Shared button style kwargs
        btn_common = dict(
            font=self._font_button,
            fg=_FG_ACCENT,
            activeforeground=_FG_ACCENT,
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=6,
            bd=0,
        )

        self.btn_start = tk.Button(
            button_frame,
            text="▶  Start Camera",
            bg="#22c55e",              # Green
            activebackground="#16a34a",
            command=self._start_camera,
            **btn_common,
        )
        self.btn_start.pack(side="left", padx=(20, 6))

        self.btn_stop = tk.Button(
            button_frame,
            text="■  Stop Camera",
            bg=_BG_BUTTON,
            activebackground=_BG_BUTTON_HOVER,
            command=self._stop_camera,
            state="disabled",
            **btn_common,
        )
        self.btn_stop.pack(side="left", padx=6)

        self.btn_clear = tk.Button(
            button_frame,
            text="🗑  Clear Text",
            bg=_BG_BUTTON,
            activebackground=_BG_BUTTON_HOVER,
            command=self._clear_text,
            **btn_common,
        )
        self.btn_clear.pack(side="left", padx=6)

        self.btn_exit = tk.Button(
            button_frame,
            text="✕  Exit",
            bg=_BG_DANGER,
            activebackground="#dc2626",
            command=self._on_exit,
            **btn_common,
        )
        self.btn_exit.pack(side="right", padx=(6, 20))

        # ---- Status Bar ----
        status_frame = tk.Frame(self.root, bg=_BG_PANEL, pady=4)
        status_frame.grid(row=3, column=0, columnspan=2, sticky="ew")

        self.status_var = tk.StringVar(value="Ready — Press 'Start Camera' to begin")
        tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=self._font_status,
            bg=_BG_PANEL,
            fg=_FG_SECONDARY,
            anchor="w",
            padx=12,
        ).pack(fill="x")

    # =================================================================
    # Camera Control
    # =================================================================

    def _start_camera(self):
        """Open the camera and start the frame-update loop."""
        if self._is_running:
            return  # Already running

        # Attempt to start the camera (TM2's CameraManager)
        try:
            success = self.camera.start()
        except Exception as e:
            self.status_var.set(f"Error: Could not start camera — {e}")
            return

        if not success:
            self.status_var.set("Error: Camera failed to open. Check connection.")
            return

        self._is_running = True
        self.status_var.set("Camera running — Show your hand to the webcam")

        # Toggle button states
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")

        # Kick off the update loop
        self._update_frame()

    def _stop_camera(self):
        """Stop the camera and cancel the update loop."""
        self._is_running = False

        # Cancel any pending after() callback
        if self._update_job is not None:
            self.root.after_cancel(self._update_job)
            self._update_job = None

        # Release camera resources (TM2)
        try:
            self.camera.stop()
        except Exception:
            pass  # Fail silently on cleanup

        # Clear the video panel to black
        self.video_label.configure(image="")
        self._photo_image = None

        # Reset gesture state
        self._last_gesture = ""
        self._gesture_counter = 0
        self._confirmed_gesture = ""
        self.gesture_var.set("No hand detected")

        # Toggle button states
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_var.set("Camera stopped — Press 'Start Camera' to resume")

    # =================================================================
    # Frame Update Loop (called every UPDATE_INTERVAL_MS milliseconds)
    # =================================================================

    def _update_frame(self):
        """Read a frame, run detection + recognition, and refresh the UI."""
        if not self._is_running:
            return

        try:
            # --- Step 1: Read frame from camera (TM2) ---
            success, frame = self.camera.read_frame()

            if not success or frame is None:
                self.status_var.set("Warning: Failed to read frame from camera")
                self._schedule_next_update()
                return

            # --- Step 2: Detect hands using MediaPipe (TM3) ---
            annotated_frame, results = self.detector.detect(frame)

            # --- Step 3: Recognize gesture (TM4) ---
            gesture_name = self._process_gesture(results)

            # --- Step 4: Update the gesture display ---
            self._update_gesture_display(gesture_name)

            # --- Step 5: Convert frame for Tkinter and display ---
            self._display_frame(annotated_frame)

        except Exception as e:
            # Gracefully handle any unexpected errors without crashing
            self.status_var.set(f"Error during processing: {e}")

        # Schedule next update
        self._schedule_next_update()

    def _schedule_next_update(self):
        """Schedule the next frame update using Tkinter's after()."""
        if self._is_running:
            self._update_job = self.root.after(UPDATE_INTERVAL_MS, self._update_frame)

    # =================================================================
    # Gesture Processing
    # =================================================================

    def _process_gesture(self, results):
        """
        Extract hand landmarks from detection results and pass them
        to the GestureRecognizer (TM4).

        Parameters
        ----------
        results : object
            The detection results returned by HandDetector.detect().
            Expected to have `.multi_hand_landmarks` and
            `.multi_handedness` attributes (standard MediaPipe format).

        Returns
        -------
        str
            The name of the recognised gesture, or "" if no hand found.
        """
        # Check whether hands were detected
        if results is None:
            return ""

        # MediaPipe results typically use .multi_hand_landmarks
        hand_landmarks_list = getattr(results, "multi_hand_landmarks", None)
        handedness_list = getattr(results, "multi_handedness", None)

        if not hand_landmarks_list:
            return ""

        # Use the first detected hand
        hand_landmarks = hand_landmarks_list[0]

        # Determine handedness label ("Left" or "Right")
        handedness = "Right"  # Default
        if handedness_list:
            try:
                handedness = handedness_list[0].classification[0].label
            except (IndexError, AttributeError):
                pass

        # Call TM4's recognizer
        try:
            gesture_name = self.recognizer.recognize(hand_landmarks, handedness)
        except Exception:
            gesture_name = ""

        return gesture_name if gesture_name else ""

    def _update_gesture_display(self, gesture_name):
        """
        Apply gesture stability logic and update the UI label.

        The same gesture must be detected for GESTURE_STABILITY_FRAMES
        consecutive frames before it is "confirmed" and appended to the
        text area.  This prevents flickery, accidental activations.
        """
        if gesture_name == "":
            # No hand / unknown gesture — reset counter
            self._last_gesture = ""
            self._gesture_counter = 0
            self.gesture_var.set("No hand detected")
            self.status_var.set("Camera running — Show your hand to the webcam")
            return

        # Show the raw (unconfirmed) gesture immediately for feedback
        self.gesture_var.set(gesture_name)
        self.status_var.set(f"Detecting: {gesture_name}")

        # Stability counter
        if gesture_name == self._last_gesture:
            self._gesture_counter += 1
        else:
            self._last_gesture = gesture_name
            self._gesture_counter = 1

        # Once stable long enough AND it's a *new* confirmed gesture, append
        if (
            self._gesture_counter == GESTURE_STABILITY_FRAMES
            and gesture_name != self._confirmed_gesture
        ):
            self._confirmed_gesture = gesture_name
            self._append_text(gesture_name)
            self.status_var.set(f"✓ Confirmed: {gesture_name}")

    # =================================================================
    # Video Display
    # =================================================================

    def _display_frame(self, frame):
        """
        Convert an OpenCV BGR frame into a Tkinter-compatible image
        and display it on the video label.

        Pipeline: BGR → RGB → PIL.Image → PIL.ImageTk.PhotoImage → Label
        """
        # OpenCV uses BGR; convert to RGB for PIL
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Resize to fit the video panel (ensures consistent display)
        frame_rgb = cv2.resize(frame_rgb, (VIDEO_WIDTH, VIDEO_HEIGHT))

        # Convert numpy array → PIL Image → Tkinter PhotoImage
        pil_image = Image.fromarray(frame_rgb)
        self._photo_image = ImageTk.PhotoImage(image=pil_image)

        # Update the label widget
        self.video_label.configure(image=self._photo_image)

    # =================================================================
    # Text Area Helpers
    # =================================================================

    def _append_text(self, text):
        """Append a line of text to the read-only text area."""
        self.text_area.configure(state="normal")
        self.text_area.insert("end", text + "\n")
        self.text_area.see("end")  # Auto-scroll to the latest line
        self.text_area.configure(state="disabled")

    def _clear_text(self):
        """Clear all accumulated text from the text area."""
        self.text_area.configure(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.configure(state="disabled")
        self._confirmed_gesture = ""  # Reset so the same gesture can re-trigger
        self.status_var.set("Text cleared")

    # =================================================================
    # Application Lifecycle
    # =================================================================

    def _on_exit(self):
        """Cleanly shut down the camera and close the window."""
        # Stop the camera loop first
        self._stop_camera()

        # Close the hand detector resources (TM3)
        try:
            self.detector.close()
        except Exception:
            pass

        # Destroy the Tkinter window and exit
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        """
        Start the Tkinter main event loop.

        This is called from main.py (TM1) and blocks until the
        window is closed.
        """
        # Centre the window on screen
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

        self.root.mainloop()


# =====================================================================
# Standalone quick-test (only runs when executed directly)
# =====================================================================
if __name__ == "__main__":
    # ------------------------------------------------------------------
    # This block lets TM5 test the GUI window *without* the real camera
    # or detector modules.  It creates lightweight stub objects that
    # satisfy the same interface so the window opens and buttons work.
    # Remove or ignore this section during final integration.
    # ------------------------------------------------------------------
    import numpy as np

    class _StubCamera:
        """Fake camera that produces a solid-colour test frame."""
        def start(self):
            print("[StubCamera] Camera started")
            return True
        def read_frame(self):
            frame = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
            # Draw a dark-grey checkerboard pattern so we know it's working
            for r in range(0, VIDEO_HEIGHT, 40):
                for c in range(0, VIDEO_WIDTH, 40):
                    if (r // 40 + c // 40) % 2 == 0:
                        frame[r:r+40, c:c+40] = (50, 50, 50)
            cv2.putText(
                frame, "Stub Camera — No real feed",
                (80, VIDEO_HEIGHT // 2), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (200, 200, 200), 2,
            )
            return True, frame
        def stop(self):
            print("[StubCamera] Camera stopped")
        def is_opened(self):
            return True

    class _StubDetector:
        """Fake detector that returns the frame unchanged, no results."""
        def detect(self, frame):
            return frame, None
        def close(self):
            print("[StubDetector] Detector closed")

    class _StubRecognizer:
        """Fake recognizer that always returns empty string."""
        def recognize(self, hand_landmarks, handedness):
            return ""

    app = AppWindow(
        camera=_StubCamera(),
        detector=_StubDetector(),
        recognizer=_StubRecognizer(),
    )
    app.run()
