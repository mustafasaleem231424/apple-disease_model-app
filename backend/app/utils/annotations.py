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

def optimize_image_for_inference(image_np: np.ndarray, max_dim: int = 1920) -> np.ndarray:
    import cv2
    h, w = image_np.shape[:2]
    if h > max_dim or w > max_dim:
        scale = max_dim / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(image_np, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return image_np

def draw_detections_on_image(image: np.ndarray, detections: List[Detection]) -> np.ndarray:
    import cv2

    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det.bbox]
        w = x2 - x1
        h = y2 - y1

        # 1. Main bounding rectangle
        cv2.rectangle(image, (x1, y1), (x2, y2), BOX_COLOR, BOX_THICKNESS)

        # 2. Corner brackets for precision focus lock
        corner_len = max(8, min(20, int(min(w, h) * 0.2)))
        corner_thick = BOX_THICKNESS + 1
        
        # Top-Left
        cv2.line(image, (x1, y1), (x1 + corner_len, y1), BOX_COLOR, corner_thick)
        cv2.line(image, (x1, y1), (x1, y1 + corner_len), BOX_COLOR, corner_thick)
        
        # Top-Right
        cv2.line(image, (x2 - corner_len, y1), (x2, y1), BOX_COLOR, corner_thick)
        cv2.line(image, (x2, y1), (x2, y1 + corner_len), BOX_COLOR, corner_thick)

        # Bottom-Left
        cv2.line(image, (x1, y2 - corner_len), (x1, y2), BOX_COLOR, corner_thick)
        cv2.line(image, (x1, y2), (x1 + corner_len, y2), BOX_COLOR, corner_thick)

        # Bottom-Right
        cv2.line(image, (x2 - corner_len, y2), (x2, y2), BOX_COLOR, corner_thick)
        cv2.line(image, (x2, y2 - corner_len), (x2, y2), BOX_COLOR, corner_thick)

        # 3. Label tag
        label = f"{det.class_name.replace('_', ' ').upper()}: {int(det.confidence * 100)}%"
        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, LABEL_FONT_SCALE, LABEL_FONT_THICKNESS)
        
        label_y1 = max(y1, th + 6)
        label_y2 = label_y1 - th - 6
        
        cv2.rectangle(image, (x1, label_y2), (x1 + tw + 8, label_y1), LABEL_BG_COLOR, -1)
        cv2.putText(image, label, (x1 + 4, label_y1 - 3), cv2.FONT_HERSHEY_SIMPLEX, LABEL_FONT_SCALE, LABEL_TEXT_COLOR, LABEL_FONT_THICKNESS, cv2.LINE_AA)

    return image
