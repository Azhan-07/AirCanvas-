import cv2
import mediapipe as mp
import numpy as np
import datetime
import os
import sys


class AirCanvas:
    def __init__(self, camera_source=0):
        self.width = 1280
        self.height = 720

        # Webcam (camera_source = 0 for laptop, or IP URL for phone)
        self.cap = cv2.VideoCapture(camera_source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Canvas
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.prev_x = -1
        self.prev_y = -1
        self.is_drawing = False
        self.brush_size = 6
        self.eraser_size = 35
        self.draw_color = (0, 255, 0)  # Default GREEN
        self.color_name = "GREEN"

        # Undo history (store last N canvas states)
        self.max_history = 20
        self.history = []

        # MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.draw = mp.solutions.drawing_utils

        # Recording (disabled by default, press 'r' to toggle)
        self.recording = False
        self.recorder = None

    # ─── UI Buttons ─────────────────────────────────────────────
    def get_buttons(self):
        """Returns list of (x1,y1,x2,y2,color,label)"""
        return [
            (10, 10, 90, 60, (255, 0, 0), "BLUE"),
            (100, 10, 180, 60, (0, 255, 0), "GREEN"),
            (190, 10, 270, 60, (0, 0, 255), "RED"),
            (280, 10, 360, 60, (255, 255, 255), "WHITE"),
            (370, 10, 450, 60, (0, 255, 255), "CYAN"),
            (460, 10, 540, 60, (0, 165, 255), "ORANGE"),
            # Undo button
            (700, 10, 790, 60, (80, 80, 80), "UNDO"),
            # Save button
            (800, 10, 890, 60, (80, 80, 80), "SAVE"),
            # Close button
            (1150, 10, 1270, 60, (40, 40, 120), "CLOSE"),
        ]

    def draw_ui(self, frame, is_eraser=False):
        buttons = self.get_buttons()
        for (x1, y1, x2, y2, color, label) in buttons:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
            text_color = (0, 0, 0) if sum(color) > 400 else (255, 255, 255)
            cv2.putText(frame, label, (x1 + 8, y1 + 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, text_color, 2)

        # Highlight current color button with border
        for (x1, y1, x2, y2, color, label) in buttons:
            if color == self.draw_color and label not in ("UNDO", "SAVE", "CLOSE"):
                cv2.rectangle(frame, (x1 - 3, y1 - 3), (x2 + 3, y2 + 3), (0, 255, 255), 3)

        # Eraser indicator
        if is_eraser:
            cv2.putText(frame, "ERASER MODE", (500, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        # Brush size info
        cv2.putText(frame, f"Brush: {self.brush_size}", (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Recording indicator
        if self.recording:
            cv2.circle(frame, (1260, 100), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (1220, 140),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # ─── Finger Detection ──────────────────────────────────────
    def fingers_up(self, hand):
        tips = [4, 8, 12, 16, 20]
        fingers = []
        # Thumb (check x-axis movement)
        fingers.append(hand.landmark[tips[0]].x < hand.landmark[tips[0] - 1].x)
        # Other 4 fingers (check y-axis)
        for t in tips[1:]:
            fingers.append(hand.landmark[t].y < hand.landmark[t - 2].y)
        return fingers  # [thumb, index, middle, ring, pinky]

    # ─── Canvas State Management (Undo) ────────────────────────
    def save_state(self):
        if len(self.history) >= self.max_history:
            self.history.pop(0)
        self.history.append(self.canvas.copy())

    def undo(self):
        if self.history:
            self.canvas = self.history.pop()
        else:
            self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)

    # ─── Save Canvas as PNG ────────────────────────────────────
    def save_canvas(self):
        os.makedirs("saves", exist_ok=True)
        filename = f"saves/aircanvas_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        cv2.imwrite(filename, self.canvas)
        return filename

    # ─── Recording ─────────────────────────────────────────────
    def toggle_recording(self):
        if self.recording:
            self.recorder.release()
            self.recorder = None
            self.recording = False
        else:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            filename = f"aircanvas_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
            self.recorder = cv2.VideoWriter(filename, fourcc, 20, (self.width, self.height))
            self.recording = True

    # ─── UI Touch Detection ────────────────────────────────────
    def check_ui_touch(self, x, y):
        """Returns action: 'none', 'draw', 'close', 'undo', 'save', 'recording'"""
        if y < 80:
            for (x1, y1, x2, y2, color, label) in self.get_buttons():
                if x1 < x < x2:
                    if label == "CLOSE":
                        return "close"
                    elif label == "UNDO":
                        return "undo"
                    elif label == "SAVE":
                        return "save"
                    else:
                        self.draw_color = color
                        self.color_name = label
                        self.is_drawing = False
                        self.prev_x, self.prev_y = -1, -1
                        return "color"
            # Clicked empty space in top bar
            self.is_drawing = False
            self.prev_x, self.prev_y = -1, -1
            return "none"
        return "draw"

    # ─── Main Loop ─────────────────────────────────────────────
    def run(self):
        print("[INFO] Controls:")
        print("  Index finger UP         = Draw")
        print("  Index + Middle UP       = Stop drawing")
        print("  Fist (all fingers down) = Eraser")
        print("  Thumb UP (in air)       = Undo")
        print("  Press 'q'               = Quit")
        print("  Press 'r'               = Toggle recording")
        print("  Press 'u'               = Undo")
        print("  Press 's'               = Save canvas")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb)

            is_eraser = False

            if result.multi_hand_landmarks:
                for hand in result.multi_hand_landmarks:
                    self.draw.draw_landmarks(frame, hand, self.mp_hands.HAND_CONNECTIONS)
                    fingers = self.fingers_up(hand)

                    x = int(hand.landmark[8].x * self.width)
                    y = int(hand.landmark[8].y * self.height)

                    index_up = fingers[1]
                    middle_up = fingers[2]
                    all_down = not any(fingers[1:])

                    # Eraser Mode (Fist)
                    if all_down:
                        is_eraser = True
                        self.is_drawing = False
                        self.prev_x, self.prev_y = -1, -1
                        cv2.circle(self.canvas, (x, y), self.eraser_size, (0, 0, 0), -1)
                        # Draw eraser cursor on frame
                        cv2.circle(frame, (x, y), self.eraser_size, (0, 0, 255), 2)

                    # Draw Mode (Index only)
                    elif index_up and not middle_up and not all_down:
                        action = self.check_ui_touch(x, y)
                        if action == "close":
                            self.cleanup()
                            return
                        elif action == "undo":
                            self.undo()
                            continue
                        elif action == "save":
                            path = self.save_canvas()
                            print(f"[SAVED] {path}")
                            continue
                        elif action == "none":
                            continue

                        if not self.is_drawing:
                            self.is_drawing = True
                            self.prev_x, self.prev_y = x, y
                            # Save state before starting new stroke
                            self.save_state()

                        cv2.line(self.canvas,
                                 (self.prev_x, self.prev_y),
                                 (x, y),
                                 self.draw_color,
                                 self.brush_size)
                        self.prev_x, self.prev_y = x, y
                        # Draw cursor on frame
                        cv2.circle(frame, (x, y), self.brush_size + 2, self.draw_color, -1)

                    # Stop Drawing
                    elif index_up and middle_up:
                        self.is_drawing = False
                        self.prev_x, self.prev_y = -1, -1

            # Merge canvas with frame
            final = cv2.add(frame, self.canvas)
            self.draw_ui(final, is_eraser)

            # Recording
            if self.recording and self.recorder:
                self.recorder.write(final)

            cv2.imshow("AI Air Canvas", final)

            # Keyboard controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.toggle_recording()
                print(f"[REC] {'ON' if self.recording else 'OFF'}")
            elif key == ord('u'):
                self.undo()
                print("[UNDO]")
            elif key == ord('s'):
                path = self.save_canvas()
                print(f"[SAVED] {path}")

        self.cleanup()

    def cleanup(self):
        if self.recording and self.recorder:
            self.recorder.release()
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # Camera source selection
    args = sys.argv[1:]

    if "--phone" in args:
        # Find IP after --ip or use default
        url = None
        if "--ip" in args:
            idx = args.index("--ip")
            if idx + 1 < len(args):
                url = args[idx + 1]
        if not url:
            url = "http://YOUR_PHONE_IP:8080/video"
            print("[WARN] No --ip given, using placeholder. Pass your phone IP:")
            print("       python aircanvas.py --ip http://YOUR_PHONE_IP:8080/video")
        source = url
        print(f"[CAMERA] Using phone IP webcam: {url}")
    elif "--help" in args or "-h" in args:
        print("Usage:")
        print("  python aircanvas.py                 = Laptop camera")
        print("  python aircanvas.py --phone         = Phone camera (default IP)")
        print("  python aircanvas.py --ip URL        = Phone camera with custom IP")
        print("      Example: python aircanvas.py --ip http://192.168.1.105:8080/video")
        print("  python aircanvas.py --cam N         = Use camera index N")
        sys.exit(0)
    elif "--cam" in args:
        idx = args.index("--cam")
        source = int(args[idx + 1])
        print(f"[CAMERA] Using camera index: {source}")
    else:
        source = 0
        print("[CAMERA] Using default laptop camera (index 0)")

    AirCanvas(camera_source=source).run()
