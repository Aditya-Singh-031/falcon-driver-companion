"""
Falcon — Live Distraction Detection Test
Runs the DistractionDetector on your webcam with a real-time overlay.

Controls:
  Q  — quit
  S  — save current frame as distraction_sample.jpg

Usage:
  python src/models/test_distraction_live.py
  python src/models/test_distraction_live.py --camera 1   # external webcam
"""

import argparse
import time
from collections import deque

import cv2
import numpy as np

from distraction_detector import DistractionDetector


# ─── Colour palette per label ──────────────────────────────────────────────────
LABEL_COLORS = {
    "attentive":        (0,   200,  80),   # green
    "distracted_left":  (0,   80,  220),   # orange-red  (BGR)
    "distracted_right": (0,   80,  220),
    "distracted_down":  (0,   100, 230),
    "distracted_up":    (180, 60,  220),
    "no_face":          (120, 120, 120),   # grey
}

LABEL_TEXT = {
    "attentive":        "✔  ATTENTIVE",
    "distracted_left":  "⚠  DISTRACTED LEFT",
    "distracted_right": "⚠  DISTRACTED RIGHT",
    "distracted_down":  "⚠  DISTRACTED DOWN",
    "distracted_up":    "⚠  DISTRACTED UP",
    "no_face":          "—  NO FACE",
}


def draw_overlay(
    frame: np.ndarray,
    label: str,
    confidence: float,
    yaw: float,
    pitch: float,
    roll: float,
    fps: float,
) -> np.ndarray:
    h, w = frame.shape[:2]
    color = LABEL_COLORS.get(label, (200, 200, 200))

    # ── Top banner ────────────────────────────────────────────────────────
    banner_h = 70
    overlay  = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, banner_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # Label
    text = LABEL_TEXT.get(label, label.upper())
    cv2.putText(frame, text, (16, 42),
                cv2.FONT_HERSHEY_DUPLEX, 1.1, color, 2, cv2.LINE_AA)

    # Confidence bar
    bar_x, bar_y, bar_w, bar_h = 16, 54, 200, 8
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
    cv2.rectangle(frame, (bar_x, bar_y),
                  (bar_x + int(bar_w * confidence), bar_y + bar_h), color, -1)

    # ── Bottom info panel ─────────────────────────────────────────────────
    panel_h = 80
    overlay2 = frame.copy()
    cv2.rectangle(overlay2, (0, h - panel_h), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay2, 0.7, frame, 0.3, 0, frame)

    info_lines = [
        f"Yaw: {yaw:+.1f}°   Pitch: {pitch:+.1f}°   Roll: {roll:+.1f}°",
        f"Confidence: {confidence:.2f}    FPS: {fps:.1f}",
    ]
    for i, line in enumerate(info_lines):
        cv2.putText(frame, line, (16, h - panel_h + 22 + i * 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

    # ── Threshold guide lines (yaw axis visualisation) ────────────────────
    cx = w // 2
    cv2.line(frame, (cx, banner_h), (cx, h - panel_h), (60, 60, 60), 1)

    return frame


def draw_axes(frame, rvec, tvec, cam_matrix, dist_coeffs, length=50):
    """Draw 3D coordinate axes on the nose tip for pose visualisation."""
    axis_pts = np.float32([[length, 0, 0], [0, length, 0], [0, 0, length], [0, 0, 0]])
    img_pts, _ = cv2.projectPoints(axis_pts, rvec, tvec, cam_matrix, dist_coeffs)
    img_pts = img_pts.astype(int)
    origin = tuple(img_pts[3].ravel())
    cv2.arrowedLine(frame, origin, tuple(img_pts[0].ravel()), (0,   0,   255), 2, tipLength=0.3)  # X red
    cv2.arrowedLine(frame, origin, tuple(img_pts[1].ravel()), (0,   255, 0  ), 2, tipLength=0.3)  # Y green
    cv2.arrowedLine(frame, origin, tuple(img_pts[2].ravel()), (255, 0,   0  ), 2, tipLength=0.3)  # Z blue


def main(camera_index: int = 0):
    print(f"[Falcon] Opening camera {camera_index}...")
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)  # CAP_DSHOW = fast on Windows
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera {camera_index}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    detector  = DistractionDetector()
    fps_times: deque = deque(maxlen=30)

    print("[Falcon] Running — press Q to quit, S to save frame")

    with detector:
        while True:
            t0 = time.perf_counter()

            ret, frame = cap.read()
            if not ret:
                print("[WARN] Empty frame, skipping")
                continue

            label, confidence, pose = detector.predict(frame)

            yaw   = pose.yaw   if pose else 0.0
            pitch = pose.pitch if pose else 0.0
            roll  = pose.roll  if pose else 0.0

            # FPS
            fps_times.append(time.perf_counter() - t0)
            fps = 1.0 / (sum(fps_times) / len(fps_times)) if fps_times else 0.0

            frame = draw_overlay(frame, label, confidence, yaw, pitch, roll, fps)

            cv2.imshow("Falcon — Distraction Detector", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                cv2.imwrite("distraction_sample.jpg", frame)
                print("[Falcon] Frame saved → distraction_sample.jpg")

    cap.release()
    cv2.destroyAllWindows()
    print("[Falcon] Closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Falcon Live Distraction Test")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    args = parser.parse_args()
    main(camera_index=args.camera)
