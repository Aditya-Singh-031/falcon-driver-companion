"""
Falcon — Distraction Detector
MediaPipe Face Mesh + OpenCV solvePnP head pose estimation.
Also computes Eye Aspect Ratio (EAR) for drowsiness detection.

Outputs one of:
  attentive | distracted_left | distracted_right | distracted_down | distracted_up | no_face

Usage (standalone):
  from src.models.distraction_detector import DistractionDetector
  detector = DistractionDetector()
  label, confidence, angles, ear = detector.predict(bgr_frame)
"""

import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass
from typing import Optional, Tuple


# ─── Thresholds (degrees) ──────────────────────────────────────────────────────
YAW_LEFT_THRESH   = -25
YAW_RIGHT_THRESH  =  25
PITCH_DOWN_THRESH =  20
PITCH_UP_THRESH   = -20

# ─── EAR thresholds ──────────────────────────────────────────────────────────
EAR_THRESH        = 0.22   # below this → eye is closed
EAR_CONSEC_FRAMES = 3      # frames before marking as drowsy

# ─── 3D Reference Face Model ──────────────────────────────────────────────────
FACE_3D_MODEL = np.array([
    [0.0,   0.0,    0.0   ],
    [0.0,  -330.0, -65.0  ],
    [-225.0, 170.0, -135.0],
    [225.0,  170.0, -135.0],
    [-150.0,-150.0, -125.0],
    [150.0, -150.0, -125.0],
], dtype=np.float64)

LANDMARK_IDS = [1, 152, 33, 263, 61, 291]

# MediaPipe FaceMesh indices for EAR (left eye, right eye)
# P1..P6 for each eye following the 6-point EAR formula
LEFT_EYE_IDS  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_IDS = [33,  160, 158, 133, 153, 144]


@dataclass
class HeadPose:
    yaw:   float
    pitch: float
    roll:  float


def _ear(eye_pts: np.ndarray) -> float:
    """Eye Aspect Ratio from 6 landmark points."""
    A = np.linalg.norm(eye_pts[1] - eye_pts[5])
    B = np.linalg.norm(eye_pts[2] - eye_pts[4])
    C = np.linalg.norm(eye_pts[0] - eye_pts[3])
    return (A + B) / (2.0 * C + 1e-6)


class DistractionDetector:
    """
    Frame-level distraction + drowsiness classifier.
    predict() returns (label, confidence, HeadPose|None, ear_value)
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
        self._ear_frames = 0  # consecutive closed-eye frame counter

    def predict(
        self, bgr_frame: np.ndarray
    ) -> Tuple[str, float, Optional[HeadPose], float]:
        """
        Returns:
            label       : str
            confidence  : float
            pose        : HeadPose or None
            ear         : float (mean eye aspect ratio; 0.0 if no face)
        """
        h, w = bgr_frame.shape[:2]
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return "no_face", 0.0, None, 0.0

        landmarks = results.multi_face_landmarks[0].landmark

        # ── EAR ────────────────────────────────────────────────────────────
        def pts(ids):
            return np.array([[landmarks[i].x * w, landmarks[i].y * h] for i in ids])

        ear = ((_ear(pts(LEFT_EYE_IDS)) + _ear(pts(RIGHT_EYE_IDS))) / 2.0)

        if ear < EAR_THRESH:
            self._ear_frames += 1
        else:
            self._ear_frames = 0

        if self._ear_frames >= EAR_CONSEC_FRAMES:
            return "drowsy", min(0.5 + self._ear_frames / 30.0, 0.99), None, round(ear, 3)

        # ── Head pose ──────────────────────────────────────────────────────
        img_points = np.array(
            [[landmarks[i].x * w, landmarks[i].y * h] for i in LANDMARK_IDS],
            dtype=np.float64,
        )

        focal = w
        cx, cy = w / 2.0, h / 2.0
        cam_matrix = np.array([[focal, 0, cx], [0, focal, cy], [0, 0, 1]], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)

        success, rvec, tvec = cv2.solvePnP(
            FACE_3D_MODEL, img_points, cam_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not success:
            return "no_face", 0.0, None, round(ear, 3)

        rmat, _ = cv2.Rodrigues(rvec)
        pose_mat = cv2.hconcat([rmat, tvec])
        _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(pose_mat)

        pitch = float(euler[0][0])
        yaw   = float(euler[1][0])
        roll  = float(euler[2][0])

        pose = HeadPose(yaw=yaw, pitch=pitch, roll=roll)
        label, confidence = self._classify(yaw, pitch)
        return label, confidence, pose, round(ear, 3)

    @staticmethod
    def _classify(yaw: float, pitch: float) -> Tuple[str, float]:
        if yaw < YAW_LEFT_THRESH:
            conf = min(0.5 + abs(yaw - YAW_LEFT_THRESH) / 50.0, 0.99)
            return "distracted_left", round(conf, 3)
        if yaw > YAW_RIGHT_THRESH:
            conf = min(0.5 + abs(yaw - YAW_RIGHT_THRESH) / 50.0, 0.99)
            return "distracted_right", round(conf, 3)
        if pitch > PITCH_DOWN_THRESH:
            conf = min(0.5 + abs(pitch - PITCH_DOWN_THRESH) / 40.0, 0.99)
            return "distracted_down", round(conf, 3)
        if pitch < PITCH_UP_THRESH:
            conf = min(0.5 + abs(pitch - PITCH_UP_THRESH) / 40.0, 0.99)
            return "distracted_up", round(conf, 3)
        margin = min(
            min(abs(yaw - YAW_LEFT_THRESH), abs(yaw - YAW_RIGHT_THRESH)),
            min(abs(pitch - PITCH_DOWN_THRESH), abs(pitch - PITCH_UP_THRESH)),
        )
        return "attentive", round(min(0.5 + margin / 40.0, 0.99), 3)

    def close(self):
        self.face_mesh.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
