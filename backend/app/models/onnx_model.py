"""
ONNX YOLOv8 Detection Model - Production
Load trained .onnx weights for production inference
"""
import asyncio
import numpy as np
from typing import List, Optional
import os

from app.models.base import DetectionModel, Detection
from app.config import settings
from app.logging_config import get_logger

logger = get_logger("models.onnx")

class ONNXModel(DetectionModel):
    def __init__(self):
        self.session = None
        self.loaded = False
        self.class_names = list(settings.CLASSES.values())
        self.input_name = None
        self.output_names = []
        self.input_shape = None

    async def load(self, weights_path: Optional[str] = None) -> None:
        try:
            import onnxruntime as ort
        except ImportError:
            logger.error("onnxruntime not installed. Install with: pip install onnxruntime")
            raise RuntimeError("ONNX runtime not available")

        path = weights_path or str(settings.WEIGHTS_DIR / "model.onnx")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"ONNX model not found at: {path}")
        
        logger.info(f"Loading ONNX model from: {path}")
        logger.info(f"Model file size: {os.path.getsize(path) / (1024*1024):.1f} MB")
        
        providers = ["CPUExecutionProvider"]
        if settings.DEVICE == "cuda":
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        
        try:
            self.session = ort.InferenceSession(path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [o.name for o in self.session.get_outputs()]
            self.input_shape = self.session.get_inputs()[0].shape
            
            input_info = self.session.get_inputs()[0]
            output_info = self.session.get_outputs()[0]
            logger.info(f"Input: {input_info.name} shape={input_info.shape}")
            logger.info(f"Output: {output_info.name} shape={output_info.shape}")
            logger.info(f"Providers: {self.session.get_providers()}")
            
            self.loaded = True
            logger.info("ONNX model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")
            raise

    async def predict(self, image: np.ndarray) -> List[Detection]:
        if not self.loaded or not self.session:
            raise RuntimeError("ONNX model not loaded")

        h_orig, w_orig = image.shape[:2]
        img = self._preprocess(image)
        outputs = self.session.run(self.output_names, {self.input_name: img})
        detections = self._postprocess(outputs[0], w_orig, h_orig)
        return detections

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        import cv2
        
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        
        h, w = img.shape[:2]
        size = settings.IMG_SIZE
        scale = min(size / h, size / w)
        new_h, new_w = int(h * scale), int(w * scale)
        
        resized = cv2.resize(img, (new_w, new_h))
        
        padded = np.zeros((size, size, 3), dtype=np.float32)
        pad_top = (size - new_h) // 2
        pad_left = (size - new_w) // 2
        padded[pad_top:pad_top+new_h, pad_left:pad_left+new_w] = resized
        
        batch = np.transpose(padded, (2, 0, 1))
        batch = np.expand_dims(batch, axis=0)
        return batch

    def _postprocess(self, output: np.ndarray, w_orig: int, h_orig: int) -> List[Detection]:
        detections = []
        
        if output.ndim == 3:
            output = output[0]
        
        num_predictions = output.shape[1]
        size = settings.IMG_SIZE
        
        scale = min(size / w_orig, size / h_orig)
        new_w, new_w_actual = int(w_orig * scale), int(w_orig * scale)
        new_h = int(h_orig * scale)
        pad_x = (size - new_w_actual) // 2
        pad_y = (size - new_h) // 2
        
        for i in range(num_predictions):
            scores = output[4:, i]
            class_id = np.argmax(scores)
            confidence = float(scores[class_id])
            
            if confidence < settings.CONF_THRESHOLD:
                continue
            
            cx = float(output[0, i])
            cy = float(output[1, i])
            bw = float(output[2, i])
            bh = float(output[3, i])
            
            x1 = ((cx - bw / 2) - pad_x) / scale
            y1 = ((cy - bh / 2) - pad_y) / scale
            x2 = ((cx + bw / 2) - pad_x) / scale
            y2 = ((cy + bh / 2) - pad_y) / scale
            
            x1 = max(0, min(x1, w_orig))
            y1 = max(0, min(y1, h_orig))
            x2 = max(0, min(x2, w_orig))
            y2 = max(0, min(y2, h_orig))
            
            detections.append(Detection(
                class_id=int(class_id),
                class_name=self.class_names[class_id],
                confidence=confidence,
                bbox=[x1, y1, x2, y2]
            ))
        
        detections = self._nms(detections, settings.IOU_THRESHOLD)
        return detections

    def _nms(self, detections: List[Detection], iou_threshold: float) -> List[Detection]:
        detections.sort(key=lambda d: d.confidence, reverse=True)
        keep = []
        
        for det in detections:
            should_keep = True
            for kept in keep:
                if det.class_id != kept.class_id:
                    continue
                if self._iou(det.bbox, kept.bbox) > iou_threshold:
                    should_keep = False
                    break
            if should_keep:
                keep.append(det)
        
        return keep

    def _iou(self, box1: List[float], box2: List[float]) -> float:
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        inter_area = max(0, x2 - x1) * max(0, y2 - y1)
        if inter_area == 0:
            return 0.0
        
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0

    def get_info(self) -> dict:
        return {
            "type": "onnx",
            "status": "loaded" if self.loaded else "not_loaded",
            "classes": self.class_names,
            "num_classes": settings.NUM_CLASSES,
            "input_size": settings.IMG_SIZE,
            "conf_threshold": settings.CONF_THRESHOLD,
            "iou_threshold": settings.IOU_THRESHOLD,
            "device": settings.DEVICE,
            "providers": self.session.get_providers() if self.session else [],
            "version": settings.VERSION,
            "input_name": self.input_name,
            "output_names": self.output_names
        }
