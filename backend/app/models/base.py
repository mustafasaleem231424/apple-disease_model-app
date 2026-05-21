"""
Abstract Detection Model Interface
Swap models by implementing this interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

from app.config import settings
from app.logging_config import get_logger

logger = get_logger("models.base")

class Detection:
    def __init__(self, class_id: int, class_name: str, confidence: float, bbox: List[float]):
        self.class_id = class_id
        self.class_name = class_name
        self.confidence = confidence
        self.xmin, self.ymin, self.xmax, self.ymax = bbox
        self.bbox = bbox
    
    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(float(self.confidence), 4),
            "bbox": {
                "xmin": round(float(self.xmin), 2),
                "ymin": round(float(self.ymin), 2),
                "xmax": round(float(self.xmax), 2),
                "ymax": round(float(self.ymax), 2)
            }
        }
    
    def __repr__(self):
        return f"Detection({self.class_name}, {self.confidence:.2%})"

class DetectionModel(ABC):
    @abstractmethod
    async def load(self, weights_path: Optional[str] = None) -> None:
        pass

    @abstractmethod
    async def predict(self, image: np.ndarray) -> List[Detection]:
        pass

    @abstractmethod
    def get_info(self) -> dict:
        pass
    
    async def warmup(self, image_size: tuple = (640, 640)) -> None:
        warmup_img = np.zeros((image_size[0], image_size[1], 3), dtype=np.uint8)
        await self.predict(warmup_img)
        logger.info("Model warmup complete")
