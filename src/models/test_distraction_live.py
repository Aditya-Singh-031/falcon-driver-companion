"""
Falcon — Live Distraction Test
Webcam demo with overlay, alerts, EAR drowsiness, and session logging.

Controls:
  Q  — quit
  S  — save snapshot
  C  — toggle calibration mode (adjust thresholds live)
  R  — reset session logger

Run:
  python src/models/test_distraction_live.py [--camera N]
"""

import argparse
import time
from pathlib import Path

import cv2
import numpy as np

from src.models.distraction_detector import DistractionDetector
from src.models.alert_manager import AlertManager
from src.models.session_logger import SessionLogger


# ─── Colours ───────────────────────────────────────────────────────────────────
GREEN  = (80,  200, 80)
RED    = (50,  60,  220)
YELLOW = (30,  200, 220)
WHITE  = (240, 240, 240)
GRAY   = (120, 120, 120)
BLACK  = (10,  10,  10)
ORANGE = (30,  140, 255)

LABEL_COLOUR = {
    "attentive":        GREEN,
    "distracted_left":  RED,
    "distracted_right": RED,
    "distracted_down":  ORANGE,
    "distracted_up":    ORANGE,
    "drowsy":           YELLOW,
    "no_face":          GRAY,
}

LABEL_ICON = {
    "attentive":        "\u2714  ATTENTIVE",
    "distracted_left":  "\u26a0  DISTRACTED LEFT",
    "distracted_right": "\u26a0  DISTRACTED RIGHT",
    "distracted_down":  "\u26a0  DISTRACTED DOWN",
    "distracted_up":    "\u26a0  DISTRACTED UP",
    "drowsy":           "\u25cf  DROWSY",
    "no_face":          "\u2014  NO FACE",
}


def draw_bar(img, x, y, w, h, value, colour, bg=(50, 50, 50)):
    cv2.rectangle(img, (x, y), (x + w, y + h), bg, -1)
    fill = int(w * max(0.0, min(value, 1.0)))
    if fill > 0:
        cv2.rectangle(img, (x, y), (x + fill, y + h), colour, -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), (80, 80, 80), 1)


def overlay(frame, label, confidence, pose, ear, alerts, fps):
    H, W = frame.shape[:2]
    colour = LABEL_COLOUR.get(label, GRAY)
    text   = LABEL_ICON.get(label, label.upper())
    font   = cv2.FONT_HERSHEY_SIMPLEX

    # ── Top banner ────────────────────────────────────────────────────────
    cv2.rectangle(frame, (0, 0), (W, 52), (20, 20, 20), -1)
    cv2.putText(frame, text, (12, 36), font, 0.9, colour, 2, cv2.LINE_AA)

    # Confidence bar
    draw_bar(frame, W - 160, 14, 140, 18, confidence, colour)
    cv2.putText(frame, f"{confidence*100:.0f}%", (W - 168, 30),
                font, 0.45, WHITE, 1, cv2.LINE_AA)

    # ── Alert sustain progress bar (bottom of banner) ─────────────────────
    prog = alerts.sustain_progress()
    if prog > 0:
        draw_bar(frame, 0, 50, W, 4, prog, RED, bg=(40, 20, 20))

    # ── FPS top-right ────────────────────────────────────────────────────
    cv2.putText(frame, f"{fps:.0f} fps", (W - 68, 14),
                font, 0.4, GRAY, 1, cv2.LINE_AA)

    # ── Bottom panel ─────────────────────────────────────────────────────
    panel_h = 64
    cv2.rectangle(frame, (0, H - panel_h), (W, H), (20, 20, 20), -1)
    cv2.line(frame, (0, H - panel_h), (W, H - panel_h), (50, 50, 50), 1)

    if pose:
        items = [
            (f"Yaw   {pose.yaw:+.1f}\u00b0",   16),
            (f"Pitch {pose.pitch:+.1f}\u00b0",  W // 3 + 8),
            (f"Roll  {pose.roll:+.1f}\u00b0",   2 * W // 3 + 8),
        ]
        for txt, x in items:
            cv2.putText(frame, txt, (x, H - panel_h + 22),
                        font, 0.48, WHITE, 1, cv2.LINE_AA)

    # EAR
    ear_col = YELLOW if ear < 0.22 else WHITE
    cv2.putText(frame, f"EAR {ear:.3f}", (16, H - panel_h + 46),
                font, 0.48, ear_col, 1, cv2.LINE_AA)

    # Cooldown indicator
    if alerts.in_cooldown():
        cv2.putText(frame, "[cooldown]", (W - 100, H - panel_h + 22),
                    font, 0.38, GRAY, 1, cv2.LINE_AA)

    # Alert flash
    if alerts.last_event and (time.time() - alerts.last_event.timestamp) < 1.5:
        msg = alerts.last_event.message
        tw  = cv2.getTextSize(msg, font, 0.7, 2)[0][0]
        cv2.putText(frame, msg, ((W - tw) // 2, H // 2),
                    font, 0.7, RED, 2, cv2.LINE_AA)

    # Centre crosshair
    cx, cy = W // 2, H // 2
    cv2.line(frame, (cx - 12, cy), (cx + 12, cy), GRAY, 1)
    cv2.line(frame, (cx, cy - 12), (cx, cy + 12), GRAY, 1)

    return frame


def main(camera_index: int = 0):
    print(f"[Falcon] Opening camera {camera_index}...")
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("[Falcon] ERROR: Cannot open camera.")
        return

    print("[Falcon] Running — press Q to quit, S to save frame")
    print("[Falcon] Alert fires after 1.5 s sustained distraction | 4 s cooldown")

    detector = DistractionDetector()
    alerts   = AlertManager(sustain_sec=1.5, cooldown_sec=4.0, beep=True)
    logger   = SessionLogger(output_dir="logs")

    snap_dir = Path("snapshots")
    snap_dir.mkdir(exist_ok=True)

    fps      = 0.0
    t_prev   = time.time()
    frame_n  = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_n += 1
            now = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(now - t_prev, 1e-6))
            t_prev = now

            label, conf, pose, ear = detector.predict(frame)
            event = alerts.update(label, timestamp=now)
            logger.log(label, conf, pose, ear, alert_fired=(event is not None))

            frame = overlay(frame, label, conf, pose, ear, alerts, fps)
            cv2.imshow("Falcon — Driver Monitor", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                p = snap_dir / f"snap_{int(now)}.jpg"
                cv2.imwrite(str(p), frame)
                print(f"[Falcon] Saved {p}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()
        summary = logger.close()
        if summary:
            print("\n── Session Summary ──────────────────────")
            print(f"  Duration   : {summary['duration_sec']}s")
            print(f"  Attentive  : {summary['attentive_pct']}%")
            print(f"  Alerts     : {summary['alert_count']}")
            print(f"  CSV log    : {summary['csv_path']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Falcon live distraction monitor")
    ap.add_argument("--camera", type=int, default=0)
    args = ap.parse_args()
    main(camera_index=args.camera)
