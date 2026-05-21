"""
Detection API Endpoints - Production grade with validation
"""
import io
import time
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse

from app.inference.engine import detection_engine
from app.config import settings
from app.logging_config import get_logger
from app.utils.annotations import encode_image, validate_image, draw_detections_on_image
from app.schemas import DetectionResponse, StreamFrameResponse

logger = get_logger("api.detect")

router = APIRouter()

MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

def _load_image(contents: bytes):
    from PIL import Image
    import numpy as np
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    return np.array(image)

def _validate_upload(file: UploadFile, contents: bytes):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max: {settings.MAX_FILE_SIZE_MB}MB")

@router.post("/image", response_model=DetectionResponse)
async def detect_image(
    file: UploadFile = File(...),
    conf: float = Query(default=None, ge=0.0, le=1.0, description="Override confidence threshold"),
    include_annotated: bool = Query(default=True, description="Include annotated image in response")
):
    contents = await file.read()
    _validate_upload(file, contents)
    
    try:
        image_np = _load_image(contents)
        
        if not validate_image(image_np):
            raise HTTPException(status_code=400, detail="Invalid image dimensions")
        
        original_conf = None
        if conf is not None:
            original_conf = settings.CONF_THRESHOLD
            settings.CONF_THRESHOLD = conf
        
        try:
            start = time.time()
            detections = await detection_engine.predict_image(image_np)
            elapsed = time.time() - start
        finally:
            if original_conf is not None:
                settings.CONF_THRESHOLD = original_conf
        
        annotated_b64 = None
        if include_annotated and detections:
            annotated_np = draw_detections_on_image(image_np.copy(), detections)
            annotated_b64 = encode_image(annotated_np)
        
        return DetectionResponse(
            detections=[d.to_dict() for d in detections],
            count=len(detections),
            inference_time_ms=round(elapsed * 1000, 2),
            image_width=image_np.shape[1],
            image_height=image_np.shape[0],
            annotated_image=annotated_b64,
            model_type=settings.MODEL_TYPE,
            timestamp=datetime.now(timezone.utc)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@router.post("/image/raw", response_model=DetectionResponse)
async def detect_image_raw(
    file: UploadFile = File(...),
    conf: float = Query(default=None, ge=0.0, le=1.0, description="Override confidence threshold")
):
    contents = await file.read()
    _validate_upload(file, contents)
    
    try:
        image_np = _load_image(contents)
        
        if not validate_image(image_np):
            raise HTTPException(status_code=400, detail="Invalid image dimensions")
        
        original_conf = None
        if conf is not None:
            original_conf = settings.CONF_THRESHOLD
            settings.CONF_THRESHOLD = conf
        
        try:
            detections = await detection_engine.predict_image(image_np)
        finally:
            if original_conf is not None:
                settings.CONF_THRESHOLD = original_conf
        
        return DetectionResponse(
            detections=[d.to_dict() for d in detections],
            count=len(detections),
            inference_time_ms=detection_engine.history[-1]["inference_time_ms"] if detection_engine.history else 0,
            image_width=image_np.shape[1],
            image_height=image_np.shape[0],
            model_type=settings.MODEL_TYPE,
            timestamp=datetime.now(timezone.utc)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@router.post("/stream/frame", response_model=StreamFrameResponse)
async def process_stream_frame(
    file: UploadFile = File(...),
    conf: float = Query(default=None, ge=0.0, le=1.0, description="Override confidence threshold")
):
    contents = await file.read()
    _validate_upload(file, contents)
    
    try:
        image = _load_image(contents)
        
        if not validate_image(image):
            raise HTTPException(status_code=400, detail="Invalid frame dimensions")
        
        original_conf = None
        if conf is not None:
            original_conf = settings.CONF_THRESHOLD
            settings.CONF_THRESHOLD = conf
        
        try:
            start = time.time()
            detections, annotated = await detection_engine.predict_frame(image)
            elapsed = time.time() - start
        finally:
            if original_conf is not None:
                settings.CONF_THRESHOLD = original_conf
        
        annotated_b64 = encode_image(annotated)
        
        return StreamFrameResponse(
            detections=[d.to_dict() for d in detections],
            annotated_frame=annotated_b64,
            count=len(detections),
            inference_time_ms=round(elapsed * 1000, 2)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Frame processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Frame processing failed: {str(e)}")

@router.get("/history")
async def get_history(limit: int = Query(default=50, ge=1, le=500)):
    history = detection_engine.get_history()
    return {"history": history[-limit:], "total": len(history)}

@router.post("/history/clear")
async def clear_history():
    detection_engine.clear_history()
    return {"status": "history_cleared", "timestamp": datetime.now(timezone.utc).isoformat()}
