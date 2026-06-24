"""
Falcon — Distraction Detector
MediaPipe Face Mesh + OpenCV solvePnP head pose estimation.

Outputs one of:
  attentive | distracted_left | distracted_right | distracted_down | distracted_up | no_face

Usage (standalone):
  from src.models.distraction_detector import DistractionDetector
  detector = DistractionDetector()
  label, confidence, angles = detector.predict(bgr_frame)
"""

import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass
from typing import Optional, Tuple


# ─── Thresholds (degrees) ──────────────────────────────────────────────────────
YAW_LEFT_THRESH   = -25   # negative yaw  → looking left
YAW_RIGHT_THRESH  =  25   # positive yaw  → looking right
PITCH_DOWN_THRESH =  20   # positive pitch → looking down
PITCH_UP_THRESH   = -20   # negative pitch → looking up


# ─── 3D Reference Face Model (canonical landmarks in mm) ──────────────────────
# 6 stable landmarks: nose tip, chin, left eye corner, right eye corner,
# left mouth corner, right mouth corner  — matches MediaPipe indices below
FACE_3D_MODEL = np.array([
    [0.0,   0.0,    0.0   ],   # Nose tip          (1)
    [0.0,  -330.0, -65.0  ],   # Chin              (152)
    [-225.0, 170.0, -135.0],   # Left eye corner   (33)
    [225.0,  170.0, -135.0],   # Right eye corner  (263)
    [-150.0,-150.0, -125.0],   # Left mouth corner (61)
    [150.0, -150.0, -125.0],   # Right mouth corner(291)
], dtype=np.float64)

# Corresponding MediaPipe FaceMesh landmark indices
LANDMARK_IDS = [1, 152, 33, 263, 61, 291]


@dataclass
class HeadPose:
    yaw:   float   # left(-) / right(+)
    pitch: float   # up(-) / down(+)
    roll:  float


class DistractionDetector:
    """
    Stateless frame-level distraction classifier using MediaPipe Face Mesh
    and PnP head pose estimation.
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence:  float = 0.5,
        refine_landmarks: bool = True,
    ):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    # ── Core predict ────────────────────────────────────────────────────────
    def predict(
        self, bgr_frame: np.ndarray
    ) -> Tuple[str, float, Optional[HeadPose]]:
        """
        Args:
            bgr_frame: OpenCV BGR uint8 image (any resolution)

        Returns:
            label       : str   — one of attentive / distracted_* / no_face
            confidence  : float — pseudo-confidence based on angle magnitude
            pose        : HeadPose or None
        """
        h, w = bgr_frame.shape[:2]
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return "no_face", 0.0, None

        landmarks = results.multi_face_landmarks[0].landmark

        # ── Extract 2D image points for the 6 reference landmarks ──────────
        img_points = np.array([
            [landmarks[i].x * w, landmarks[i].y * h]
            for i in LANDMARK_IDS
        ], dtype=np.float64)

        # ── Camera intrinsics (estimated from image size) ───────────────────
        focal  = w
        cx, cy = w / 2.0, h / 2.0
        cam_matrix = np.array([
            [focal,  0,     cx],
            [0,      focal, cy],
            [0,      0,     1 ],
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)  # assume no lens distortion

        # ── solvePnP → rotation vector ──────────────────────────────────────
        success, rvec, tvec = cv2.solvePnP(
            FACE_3D_MODEL, img_points, cam_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not success:
            return "no_face", 0.0, None

        # ── Rotation vector → Euler angles ──────────────────────────────────
        rmat, _ = cv2.Rodrigues(rvec)
        pose_mat = cv2.hconcat([rmat, tvec])
        _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(pose_mat)
        pitch = float(euler[0])
        yaw   = float(euler[1])
        roll  = float(euler[2])

        pose = HeadPose(yaw=yaw, pitch=pitch, roll=roll)

        # ── Classify ────────────────────────────────────────────────────────
        label, confidence = self._classify(yaw, pitch)
        return label, confidence, pose

    # ── Classification logic ────────────────────────────────────────────────
    @staticmethod
    def _classify(yaw: float, pitch: float) -> Tuple[str, float]:
        """
        Priority: yaw dominates; then pitch.
        Confidence = 1 - (remaining headroom to next threshold) normalised.
        """
        if yaw < YAW_LEFT_THRESH:
            excess = abs(yaw - YAW_LEFT_THRESH)
            conf   = min(0.5 + excess / 50.0, 0.99)
            return "distracted_left", round(conf, 3)

        if yaw > YAW_RIGHT_THRESH:
            excess = abs(yaw - YAW_RIGHT_THRESH)
            conf   = min(0.5 + excess / 50.0, 0.99)
            return "distracted_right", round(conf, 3)

        if pitch > PITCH_DOWN_THRESH:
            excess = abs(pitch - PITCH_DOWN_THRESH)
            conf   = min(0.5 + excess / 40.0, 0.99)
            return "distracted_down", round(conf, 3)

        if pitch < PITCH_UP_THRESH:
            excess = abs(pitch - PITCH_UP_THRESH)
            conf   = min(0.5 + excess / 40.0, 0.99)
            return "distracted_up", round(conf, 3)

        # Within safe zone — confidence proportional to distance from nearest boundary
        margin_yaw   = min(abs(yaw   - YAW_LEFT_THRESH),  abs(yaw   - YAW_RIGHT_THRESH))
        margin_pitch = min(abs(pitch - PITCH_DOWN_THRESH), abs(pitch - PITCH_UP_THRESH))
        margin       = min(margin_yaw, margin_pitch)
        conf         = min(0.5 + margin / 40.0, 0.99)
        return "attentive", round(conf, 3)

    def close(self):
        self.face_mesh.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
