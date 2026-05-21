"""
WebRTC Stream Handler for Real-Time Video Detection
"""
import asyncio
import numpy as np
from typing import Optional

from app.inference.engine import detection_engine

class StreamProcessor:
    def __init__(self):
        self.active = False
        self.fps = 0
        self.frame_count = 0

    async def process_frame(self, frame: np.ndarray) -> np.ndarray:
        self.frame_count += 1
        detections, annotated = await detection_engine.predict_frame(frame)
        return annotated

    async def start(self):
        self.active = True
        self.frame_count = 0

    async def stop(self):
        self.active = False

stream_processor = StreamProcessor()
