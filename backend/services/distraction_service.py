import numpy as np
import mediapipe as mp
import logging

logger = logging.getLogger(__name__)

class DistractionService:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = None
        self.is_loaded = False
        self.load_model()

    def load_model(self):
        try:
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.is_loaded = True
            logger.info("Distraction model (MediaPipe) loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Distraction model: {e}")

    def predict(self, image_np: np.ndarray):
        if not self.is_loaded:
            return {"distraction": "unknown", "distraction_confidence": 0.0, "error": "model not loaded"}

        try:
            results = self.face_mesh.process(image_np)
            
            if not results.multi_face_landmarks:
                return {"distraction": "unknown", "distraction_confidence": 0.0, "error": "no face detected"}
            
            face_landmarks = results.multi_face_landmarks[0]
            
            # Using key landmarks to estimate head pose heuristics
            nose_tip = face_landmarks.landmark[33]
            left_side = face_landmarks.landmark[234]
            right_side = face_landmarks.landmark[454]
            chin = face_landmarks.landmark[152]
            
            nose_x = nose_tip.x
            left_x = left_side.x
            right_x = right_side.x
            
            distraction = "attentive"
            confidence = 0.85
            
            # Simplified proxy for head rotation bounding
            if nose_x < left_x + 0.1:
                distraction = "distracted_left"
                confidence = 0.90
            elif nose_x > right_x - 0.1:
                distraction = "distracted_right"
                confidence = 0.90
            elif nose_tip.y > chin.y - 0.1:
                distraction = "distracted_down"
                confidence = 0.88
                
            return {"distraction": distraction, "distraction_confidence": confidence}

        except Exception as e:
            logger.error(f"Error during distraction inference: {e}")
            return {"distraction": "error", "distraction_confidence": 0.0, "error": str(e)}

distraction_service = DistractionService()