"""
Pydantic schemas for request/response validation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

class BoundingBox(BaseModel):
    xmin: float = Field(ge=0, description="Top-left X coordinate")
    ymin: float = Field(ge=0, description="Top-left Y coordinate")
    xmax: float = Field(ge=0, description="Bottom-right X coordinate")
    ymax: float = Field(ge=0, description="Bottom-right Y coordinate")
    
    @validator("xmax")
    def xmax_greater_than_xmin(cls, v, values):
        if "xmin" in values and v < values["xmin"]:
            raise ValueError("xmax must be greater than xmin")
        return v
    
    @validator("ymax")
    def ymax_greater_than_ymin(cls, v, values):
        if "ymin" in values and v < values["ymin"]:
            raise ValueError("ymax must be greater than ymin")
        return v

class DetectionResult(BaseModel):
    class_id: int = Field(ge=0, lt=6, description="Class ID (0-5)")
    class_name: str = Field(min_length=1, max_length=50, description="Class name")
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")
    bbox: BoundingBox = Field(description="Bounding box coordinates")
    
    class Config:
        json_schema_extra = {
            "example": {
                "class_id": 0,
                "class_name": "apple_scab",
                "confidence": 0.87,
                "bbox": {"xmin": 100, "ymin": 50, "xmax": 300, "ymax": 250}
            }
        }

class DetectionResponse(BaseModel):
    detections: List[DetectionResult] = Field(default_factory=list)
    count: int = Field(ge=0, description="Number of detections")
    inference_time_ms: float = Field(ge=0, description="Inference time in milliseconds")
    image_width: Optional[int] = Field(None, ge=0, description="Original image width")
    image_height: Optional[int] = Field(None, ge=0, description="Original image height")
    annotated_image: Optional[str] = Field(None, description="Base64 encoded annotated image")
    model_type: str = Field(description="Model type used for detection")
    timestamp: datetime = Field(description="Detection timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detections": [
                    {"class_id": 0, "class_name": "apple_scab", "confidence": 0.87, "bbox": {"xmin": 100, "ymin": 50, "xmax": 300, "ymax": 250}}
                ],
                "count": 1,
                "inference_time_ms": 45.2,
                "image_width": 640,
                "image_height": 480,
                "model_type": "mock",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

class HealthResponse(BaseModel):
    status: str = Field(description="Overall health status")
    model: Dict[str, Any] = Field(description="Model information")
    uptime_seconds: float = Field(ge=0, description="Server uptime in seconds")
    history_count: int = Field(ge=0, description="Number of stored detections")
    timestamp: datetime = Field(description="Current timestamp")

class ModelInfoResponse(BaseModel):
    type: str = Field(description="Model type")
    status: str = Field(description="Model load status")
    classes: List[str] = Field(description="Available classes")
    num_classes: int = Field(ge=1, description="Number of classes")
    input_size: int = Field(ge=1, description="Input image size")
    conf_threshold: float = Field(ge=0, le=1, description="Confidence threshold")
    iou_threshold: float = Field(ge=0, le=1, description="IoU threshold")
    device: str = Field(description="Compute device")
    version: str = Field(description="Application version")

class ErrorResponse(BaseModel):
    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(description="Error timestamp")

class HistoryItem(BaseModel):
    timestamp: datetime
    detections: List[DetectionResult]
    inference_time_ms: float
    image_size: Optional[List[int]] = None

class HistoryResponse(BaseModel):
    history: List[HistoryItem]
    total: int = Field(ge=0, description="Total number of records")

class StreamFrameResponse(BaseModel):
    detections: List[DetectionResult]
    annotated_frame: str = Field(description="Base64 encoded annotated frame")
    count: int = Field(ge=0, description="Number of detections")
    fps: Optional[float] = Field(None, ge=0, description="Current processing FPS")
    inference_time_ms: float = Field(ge=0, description="Inference time in milliseconds")

class LanguagePreference(BaseModel):
    lang: str = Field(pattern="^(en|hi)$", default="en", description="Language code (en/hi)")
