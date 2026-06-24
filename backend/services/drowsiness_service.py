import os
import torch
import logging
from torchvision import models, transforms
from PIL import Image
from core.config import settings

logger = logging.getLogger(__name__)

class DrowsinessService:
    def __init__(self):
        self.device = torch.device(settings.DEVICE)
        self.model = None
        self.is_loaded = False
        
        # Preprocessing matching the training pipeline
        self.transform = transforms.Compose([
            transforms.Resize(224),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self.load_model()

    def load_model(self):
        if not os.path.exists(settings.DROWSINESS_MODEL_PATH):
            logger.warning(f"Drowsiness model missing at {settings.DROWSINESS_MODEL_PATH}")
            return

        try:
            self.model = models.efficientnet_b0(weights=None)
            num_ftrs = self.model.classifier[1].in_features
            
            # Binary classification head: index 0 (non_drowsy), index 1 (drowsy)
            self.model.classifier[1] = torch.nn.Linear(num_ftrs, 2)
            
            state_dict = torch.load(settings.DROWSINESS_MODEL_PATH, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            logger.info("Drowsiness model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Drowsiness model: {e}")

    def predict(self, pil_image: Image.Image):
        if not self.is_loaded:
            return {"drowsiness": "unknown", "drowsiness_confidence": 0.0, "error": "model not loaded"}
        
        try:
            input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
                
                drowsy_prob = probabilities[1].item()
                
                if drowsy_prob >= settings.DROWSINESS_THRESHOLD:
                    return {"drowsiness": "drowsy", "drowsiness_confidence": drowsy_prob}
                else:
                    return {"drowsiness": "non_drowsy", "drowsiness_confidence": 1.0 - drowsy_prob}
        except Exception as e:
            logger.error(f"Error during drowsiness inference: {e}")
            return {"drowsiness": "error", "drowsiness_confidence": 0.0, "error": str(e)}

drowsiness_service = DrowsinessService()