from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Falcon Backend", version="0.1.0")


class DriverState(BaseModel):
    attention_level: float  # 0.0–1.0
    drowsiness_level: float  # 0.0–1.0
    cognitive_load: float  # 0.0–1.0
    notifications_mode: str  # "allow" | "delay" | "batch"


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "falcon-backend"}


@app.get("/driver-state/mock", response_model=DriverState)
def get_mock_driver_state():
    """
    Temporary mock endpoint for the dashboard.
    Later this will be driven by the real CV/audio models.
    """
    return DriverState(
        attention_level=0.82,
        drowsiness_level=0.12,
        cognitive_load=0.35,
        notifications_mode="allow",
    )