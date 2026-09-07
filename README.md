# 🖐️ AI Air Canvas

Draw in the air using hand gestures with just your webcam! No mouse, no touchscreen — simply move your finger and watch your ideas come to life.

## ✨ Features

- **Gesture-based drawing** with finger tracking
- **6 colors** to choose from (Blue, Green, Red, White, Cyan, Orange)
- **Eraser mode** for corrections
- **Undo** support (up to 20 steps)
- **Save your artwork** as PNG
- **Optional screen recording** (AVI)
- **Works with laptop camera or phone camera** (IP Webcam)

## 🎮 Controls

### Hand Gestures

| Gesture | Action |
|---------|--------|
| ☝️ Index finger up | Draw |
| ✌️ Index + Middle up | Stop drawing |
| ✊ Fist | Eraser mode |
| 👍 Thumb up | Undo (in air) |

### On-Screen Buttons

- **Color buttons** (top-left) — select drawing color
- **UNDO** — undo last stroke
- **SAVE** — save canvas as PNG
- **CLOSE** — exit application

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Toggle recording ON/OFF |
| `u` | Undo |
| `s` | Save canvas as PNG |

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/your-username/air-canvas.git
cd air-canvas

# Install dependencies
pip install opencv-python mediapipe numpy
```

## 🚀 Usage

### With Laptop / Built-in Camera

```bash
python aircanvas.py
```

### With Phone Camera (IP Webcam)

1. Install **IP Webcam** app from the Play Store on your phone
2. Make sure phone and PC are on the **same WiFi**
3. Open the app and tap **"Start Server"**
4. Note the URL shown at the bottom (e.g. `http://192.168.1.105:8080/video`)

Then run:

```bash
# Default phone IP
python aircanvas.py --phone

# Custom phone IP
python aircanvas.py --ip http://192.168.1.105:8080/video
```

### Other Options

```bash
# Use a specific camera index (external webcam, etc.)
python aircanvas.py --cam 1

# Show help
python aircanvas.py --help
```

## 📁 Project Structure

```
air-canvas/
├── aircanvas.py      # Main application
├── saves/            # Saved canvas drawings (auto-created)
└── requirements.txt  # Python dependencies
```

## 🛠️ How It Works

1. **MediaPipe Hands** detects hand landmarks in real-time from the video feed
2. **Finger counting** determines the current gesture/mode:
   - One finger → draw
   - Two fingers → pause drawing
   - Fist → erase
3. **OpenCV** renders the canvas, UI overlay, and handles video I/O
4. Canvas strokes are stored in memory, enabling undo & save functionality

## 🤝 Contributing

Feel free to open issues or submit pull requests. Suggestions for new features are always welcome!

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
