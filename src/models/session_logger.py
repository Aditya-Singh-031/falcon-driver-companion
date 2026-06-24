"""
Falcon — Session Logger
Writes per-frame events to a timestamped CSV and a JSON session summary.

Usage:
    from src.models.session_logger import SessionLogger
    logger = SessionLogger(output_dir="logs")
    logger.log(label, confidence, pose, ear, alert_fired)
    logger.close()   # writes summary JSON
"""

import csv
import json
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.distraction_detector import HeadPose


class SessionLogger:
    """
    Logs every frame to CSV and produces a session summary JSON on close.
    Output files:
        logs/session_YYYYMMDD_HHMMSS.csv
        logs/session_YYYYMMDD_HHMMSS_summary.json
    """

    FIELDNAMES = [
        "timestamp", "elapsed_s", "label", "confidence",
        "yaw", "pitch", "roll", "ear", "alert_fired",
    ]

    def __init__(self, output_dir: str = "logs"):
        self.start_time = time.time()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        self.csv_path     = out / f"session_{self.session_id}.csv"
        self.summary_path = out / f"session_{self.session_id}_summary.json"

        self._file   = open(self.csv_path, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self.FIELDNAMES)
        self._writer.writeheader()

        # aggregation
        self._label_counts: dict = defaultdict(int)
        self._alert_count   = 0
        self._frame_count   = 0
        self._closed        = False

        print(f"[Logger] Session {self.session_id} → {self.csv_path}")

    def log(
        self,
        label:       str,
        confidence:  float,
        pose:        Optional[HeadPose],
        ear:         float,
        alert_fired: bool = False,
    ):
        if self._closed:
            return

        now     = time.time()
        elapsed = round(now - self.start_time, 3)

        self._writer.writerow({
            "timestamp":   round(now, 3),
            "elapsed_s":   elapsed,
            "label":       label,
            "confidence":  round(confidence, 3),
            "yaw":         round(pose.yaw,   2) if pose else "",
            "pitch":       round(pose.pitch, 2) if pose else "",
            "roll":        round(pose.roll,  2) if pose else "",
            "ear":         round(ear, 3),
            "alert_fired": int(alert_fired),
        })

        self._label_counts[label] += 1
        self._frame_count         += 1
        if alert_fired:
            self._alert_count += 1

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._file.close()

        duration = time.time() - self.start_time
        total    = max(self._frame_count, 1)

        summary = {
            "session_id":       self.session_id,
            "duration_sec":     round(duration, 1),
            "total_frames":     total,
            "alert_count":      self._alert_count,
            "label_counts":     dict(self._label_counts),
            "label_pct": {
                k: round(v / total * 100, 1)
                for k, v in self._label_counts.items()
            },
            "attentive_pct":    round(
                self._label_counts.get("attentive", 0) / total * 100, 1
            ),
            "csv_path":         str(self.csv_path),
        }

        with open(self.summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"[Logger] Session closed. {duration:.1f}s | {total} frames | {self._alert_count} alerts")
        print(f"[Logger] Summary → {self.summary_path}")
        return summary

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
