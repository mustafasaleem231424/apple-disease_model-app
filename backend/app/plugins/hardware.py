"""
Hardware Plugin Interface - Abstract base for future Jetson integration
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import numpy as np

from app.models.base import Detection
from app.logging_config import get_logger

logger = get_logger("plugins.hardware")

class HardwarePlugin(ABC):
    @abstractmethod
    async def initialize(self) -> bool:
        pass

    @abstractmethod
    async def process_detections(self, detections: List[Detection], frame: np.ndarray) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        pass

class JetsonSprayPlugin(HardwarePlugin):
    def __init__(self):
        self.initialized = False
        self.spray_active = False
    
    async def initialize(self) -> bool:
        logger.info("Jetson Spray Plugin initialized (stub)")
        self.initialized = True
        return True

    async def process_detections(self, detections: List[Detection], frame: np.ndarray) -> Dict[str, Any]:
        spray_zones = []
        for det in detections:
            if det.class_name not in ["healthy_apple", "other"]:
                spray_zones.append({
                    "class": det.class_name,
                    "bbox": det.bbox,
                    "confidence": det.confidence,
                    "action": "spray"
                })
        
        self.spray_active = len(spray_zones) > 0
        
        return {
            "spray_zones": spray_zones,
            "total_zones": len(spray_zones),
            "action": "spray" if spray_zones else "idle",
            "timestamp": np.datetime64('now').isoformat()
        }

    async def shutdown(self) -> None:
        self.spray_active = False
        self.initialized = False
        logger.info("Jetson Spray Plugin shutdown")
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "type": "jetson_spray",
            "initialized": self.initialized,
            "spray_active": self.spray_active
        }

hardware_plugin: Optional[HardwarePlugin] = None

async def load_plugin(plugin_type: str = "jetson") -> HardwarePlugin:
    global hardware_plugin
    if plugin_type == "jetson":
        hardware_plugin = JetsonSprayPlugin()
    await hardware_plugin.initialize()
    return hardware_plugin
