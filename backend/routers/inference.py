import base64
import io
import concurrent.futures
from datetime import datetime, timezone
from collections import deque
import numpy as np
from PIL import Image
from fastapi import APIRouter, HTTPException

from schemas.driver_state import InferenceRequest, InferenceResponse
from services.drowsiness_service import drowsiness_service
from services.distraction_service import distraction_service

router = APIRouter()
history_deque = deque(maxlen=100)

def decode_base64_image(base64_str: str) -> tuple[Image.Image, np.ndarray]:
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        img_data = base64.b64decode(base64_str)
        img_pil = Image.open(io.BytesIO(img_data)).convert('RGB')
        img_np = np.array(img_pil)
        return img_pil, img_np
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {e}")

def compute_state_and_alert(drowsiness: str, distraction: str):
    is_drowsy = (drowsiness == "drowsy")
    is_distracted = (distraction not in ["attentive", "unknown", "error"])
    
    if is_drowsy and is_distracted:
        return "critical", 2
    elif is_drowsy:
        return "drowsy", 1
    elif is_distracted:
        return "distracted", 1
        
    if drowsiness in ["error", "unknown"] and distraction in ["error", "unknown"]:
        return "unknown", 0
        
    return "safe", 0

@router.post("/infer", response_model=InferenceResponse)
def infer_frame(request: InferenceRequest):
    img_pil, img_np = decode_base64_image(request.frame)
    
    # Run inferences in parallel to hit the ~10 fps target
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        drowsiness_future = executor.submit(drowsiness_service.predict, img_pil)
        distraction_future = executor.submit(distraction_service.predict, img_np)
        
        drowsiness_result = drowsiness_future.result()
        distraction_result = distraction_future.result()
        
    drowsiness = drowsiness_result.get("drowsiness", "error")
    drowsiness_conf = drowsiness_result.get("drowsiness_confidence", 0.0)
    
    distraction = distraction_result.get("distraction", "error")
    distraction_conf = distraction_result.get("distraction_confidence", 0.0)
    
    driver_state, alert_level = compute_state_and_alert(drowsiness, distraction)
    
    error_msg = None
    if "error" in drowsiness_result or "error" in distraction_result:
        errors = [r["error"] for r in (drowsiness_result, distraction_result) if "error" in r]
        error_msg = " | ".join(errors)

    response = InferenceResponse(
        drowsiness=drowsiness,
        drowsiness_confidence=drowsiness_conf,
        distraction=distraction,
        distraction_confidence=distraction_conf,
        driver_state=driver_state,
        alert_level=alert_level,
        timestamp=datetime.now(timezone.utc).isoformat(),
        error=error_msg
    )
    
    history_deque.append(response.model_dump())
    return response

@router.get("/state/history")
def get_history():
    return {"history": list(history_deque)}