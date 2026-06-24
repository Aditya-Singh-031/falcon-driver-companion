from pydantic import BaseModel, Field
from typing import Optional

class InferenceRequest(BaseModel):
    frame: str = Field(..., description="Base64 encoded JPEG string")

class InferenceResponse(BaseModel):
    drowsiness: str
    drowsiness_confidence: float
    distraction: str
    distraction_confidence: float
    driver_state: str
    alert_level: int
    timestamp: str
    error: Optional[str] = None