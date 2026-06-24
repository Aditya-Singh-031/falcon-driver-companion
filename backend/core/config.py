from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MODEL_DIR: str = "models/"
    DROWSINESS_MODEL_PATH: str = "../models/drowsiness_best.pt"
    DROWSINESS_THRESHOLD: float = 0.5
    DISTRACTION_THRESHOLD: float = 0.5
    DEVICE: str = "cpu"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()