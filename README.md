# 🤟 Hand Sign Recognition — literate-potato

**Real-time hand sign recognition** using your webcam. Built with Python, OpenCV, and MediaPipe.

Shows hand gestures on camera and converts them to readable text in real time.

---

## 🚀 Quick Setup

### Prerequisites

> ⚠️ **Python 3.12 is required.** MediaPipe does NOT support Python 3.13 or 3.14 yet.

1. **Install Python 3.12** from [python.org/downloads](https://www.python.org/downloads/release/python-3129/)
   - ✅ Check "Add Python to PATH" during installation
   - If you have multiple Python versions, use `py -3.12` instead of `python`

2. **Install Git** from [git-scm.com](https://git-scm.com/downloads)

### Clone & Run

```bash
# Clone the repo
git clone https://github.com/<USERNAME>/literate-potato.git
cd literate-potato

# Create a virtual environment with Python 3.12
py -3.12 -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

---

## 🏗️ Project Structure

```
literate-potato/
├── main.py                  # App entry point (wires all modules)
├── config.py                # Shared settings & constants
├── requirements.txt         # Python dependencies
│
├── modules/
│   ├── camera.py            # Webcam capture (TM2)
│   ├── hand_detector.py     # MediaPipe hand detection (TM3)
│   └── gesture_recognizer.py # Gesture classification (TM4)
│
├── ui/
│   └── app_window.py        # Tkinter GUI (TM5)
│
└── utils/
    └── helpers.py           # Shared utility functions
```

---

## ✋ Supported Gestures

| Gesture | Displayed Text |
|---------|---------------|
| Open Palm | Hello |
| Fist | Fist |
| Thumbs Up | Yes |
| Thumbs Down | No |
| Peace Sign | Peace |
| Point | Point |
| Three Fingers | Three |
| Four Fingers | Four |
| Rock Sign | Rock On |
| Call Me | Call Me |

---

## 🛠️ Technologies

- **Python 3.12** — Language
- **OpenCV** — Webcam & image processing
- **MediaPipe** — Hand detection & landmark extraction
- **Tkinter** — Desktop GUI
- **Pillow** — Image conversion
- **NumPy** — Numerical operations

---

## 👥 Team

| Role | Member | Branch |
|------|--------|--------|
| Team Leader | TM1 | `dev/team-leader` |
| Camera Module | TM2 | `dev/camera-module` |
| Hand Detection | TM3 | `dev/hand-detection` |
| Gesture Recognition | TM4 | `dev/gesture-recognition` |
| GUI Interface | TM5 | `dev/gui-interface` |
