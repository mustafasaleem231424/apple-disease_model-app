"""
Core Detection Engine - Production grade, ONNX only
"""
import asyncio
import time
import numpy as np
from typing import List, Optional
from datetime import datetime, timezone

from app.config import settings
from app.models.base import DetectionModel, Detection
from app.logging_config import get_logger
from app.utils.annotations import draw_detections_on_image, encode_image, validate_image

logger = get_logger("inference.engine")

class DetectionEngine:
    def __init__(self):
        self.model: Optional[DetectionModel] = None
        self.history: List[dict] = []
        self.initialized = False
    
    async def initialize(self):
        if settings.MODEL_TYPE != "onnx":
            raise RuntimeError(f"Unsupported model type: {settings.MODEL_TYPE}. Only 'onnx' is supported in production.")
        
        from app.models.onnx_model import ONNXModel
        self.model = ONNXModel()
        await self.model.load(settings.MODEL_PATH)
        await self.model.warmup()
        
        self.initialized = True
        logger.info(f"Detection engine initialized with ONNX model ({settings.MODEL_TYPE})")

    async def predict_image(self, image: np.ndarray) -> List[Detection]:
        if not self.initialized or not self.model:
            raise RuntimeError("Detection engine not initialized")
        
        if not validate_image(image):
            raise ValueError(f"Invalid image: shape={image.shape if image is not None else 'None'}")
        
        start = time.time()
        detections = await self.model.predict(image)
        elapsed = time.time() - start

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detections": [d.to_dict() for d in detections],
            "inference_time_ms": round(elapsed * 1000, 2),
            "image_size": list(image.shape[:2])
        }
        self._add_to_history(record)

        return detections

    async def predict_frame(self, frame: np.ndarray) -> tuple:
        if not self.initialized or not self.model:
            raise RuntimeError("Detection engine not initialized")
        
        detections = await self.model.predict(frame)
        annotated = draw_detections_on_image(frame.copy(), detections)
        return detections, annotated

    def get_history(self) -> List[dict]:
        return self.history

    def clear_history(self):
        self.history = []
        logger.info("Detection history cleared")

    async def cleanup(self):
        self.model = None
        self.history = []
        self.initialized = False
        logger.info("Detection engine cleaned up")
    
    def _add_to_history(self, record: dict):
        self.history.append(record)
        if len(self.history) > settings.MAX_HISTORY:
            self.history = self.history[-settings.MAX_HISTORY:]

detection_engine = DetectionEngine()
