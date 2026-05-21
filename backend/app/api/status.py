"""
Health and Status API Endpoints
"""
import time
from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings
from app.inference.engine import detection_engine
from app.schemas import HealthResponse, ModelInfoResponse
from app.logging_config import get_logger

logger = get_logger("api.status")

router = APIRouter()

@router.get("/health")
async def health_check():
    model_info = detection_engine.model.get_info() if detection_engine.model and detection_engine.model.loaded else {"status": "not_loaded"}
    uptime = time.time() - getattr(detection_engine, "start_time", time.time())
    return {
        "status": "healthy" if detection_engine.initialized else "initializing",
        "model": model_info,
        "uptime_seconds": round(uptime, 2),
        "history_count": len(detection_engine.get_history()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/model/info")
async def model_info():
    if not detection_engine.model or not detection_engine.model.loaded:
        return JSONResponse(
            status_code=503,
            content={"error": "Model not loaded", "status": "not_ready"}
        )
    info = detection_engine.model.get_info()
    return {
        "type": info.get("type", "unknown"),
        "status": info.get("status", "unknown"),
        "classes": info.get("classes", []),
        "num_classes": info.get("num_classes", 0),
        "input_size": settings.IMG_SIZE,
        "conf_threshold": settings.CONF_THRESHOLD,
        "iou_threshold": settings.IOU_THRESHOLD,
        "device": settings.DEVICE,
        "version": settings.VERSION
    }

@router.get("/ready")
async def readiness_probe():
    if detection_engine.initialized and detection_engine.model:
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "not_ready"})

@router.get("/live")
async def liveness_probe():
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}
