"""
Image encoding/decoding and annotation utilities - Production
Black bounding boxes with white text labels
"""
import io
import base64
import numpy as np
from PIL import Image
from typing import List

from app.config import settings
from app.models.base import Detection
from app.logging_config import get_logger

logger = get_logger("utils.annotations")

BOX_COLOR = (26, 26, 26)
BOX_THICKNESS = 3
LABEL_BG_COLOR = (26, 26, 26)
LABEL_TEXT_COLOR = (255, 255, 255)
LABEL_FONT_SCALE = 0.5
LABEL_FONT_THICKNESS = 1

def encode_image(image_np: np.ndarray) -> str:
    image_pil = Image.fromarray(image_np)
    buffer = io.BytesIO()
    image_pil.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")

def decode_image(image_b64: str) -> np.ndarray:
    image_bytes = base64.b64decode(image_b64)
    image_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(image_pil)

def validate_image(image_np: np.ndarray) -> bool:
    if image_np is None:
        return False
    if image_np.size == 0:
        return False
    if len(image_np.shape) < 2:
        return False
    h, w = image_np.shape[:2]
    if h < settings.MIN_IMAGE_SIZE or w < settings.MIN_IMAGE_SIZE:
        return False
    if h > settings.MAX_IMAGE_SIZE or w > settings.MAX_IMAGE_SIZE:
        return False
    return True

def draw_detections_on_image(image: np.ndarray, detections: List[Detection]) -> np.ndarray:
    import cv2

    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det.bbox]

        cv2.rectangle(image, (x1, y1), (x2, y2), BOX_COLOR, BOX_THICKNESS)

        label = f"{det.class_name.replace('_', ' ')}: {det.confidence:.2f}"
        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, LABEL_FONT_SCALE, LABEL_FONT_THICKNESS)
        
        label_y1 = max(y1, th + 4)
        label_y2 = label_y1 - th - 4
        
        cv2.rectangle(image, (x1, label_y2), (x1 + tw + 6, label_y1 + 2), LABEL_BG_COLOR, -1)
        cv2.putText(image, label, (x1 + 3, label_y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, LABEL_FONT_SCALE, LABEL_TEXT_COLOR, LABEL_FONT_THICKNESS)

    return image
