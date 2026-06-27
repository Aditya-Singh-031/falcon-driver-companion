import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import inference
from services.drowsiness_service import drowsiness_service
from services.distraction_service import distraction_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Falcon API...")
    if not drowsiness_service.is_loaded:
        logger.warning("Drowsiness model is NOT loaded (waiting for weights).")
    if not distraction_service.is_loaded:
        logger.warning("Distraction model is NOT loaded.")
    yield
    logger.info("Shutting down Falcon API...")

app = FastAPI(title="Falcon Edge AI API", lifespan=lifespan)

# ── CORS ────────────────────────────────────────────────────────────────────────
# The Next.js frontend runs on :3000 (dev) and the Streamlit dashboard on :8501.
# All four origins (with both localhost / 127.0.0.1 variants) are allowed so that
# the browser's CORS preflight for POST /infer always succeeds.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],   # explicit — OPTIONS is required for preflight
    allow_headers=["*"],
)
# ───────────────────────────────────────────────────────────────────────────────

app.include_router(inference.router)

@app.get("/health")
def health_check():
    models_loaded = drowsiness_service.is_loaded and distraction_service.is_loaded
    return {
        "status": "ok" if models_loaded else "degraded",
        "models_loaded": models_loaded,
        "drowsiness_loaded": drowsiness_service.is_loaded,
        "distraction_loaded": distraction_service.is_loaded,
    }
