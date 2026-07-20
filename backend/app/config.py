"""
Production Configuration - Environment-based settings
"""
import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Apple Disease Detector"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    BASE_DIR: Path = Path(__file__).parent.parent
    WEIGHTS_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "app" / "models" / "weights")
    
    MODEL_TYPE: str = os.getenv("MODEL_TYPE", "onnx")
    MODEL_PATH: Optional[str] = os.getenv("MODEL_PATH", None)
    
    DEVICE: str = os.getenv("DEVICE", "cpu")
    CONF_THRESHOLD: float = float(os.getenv("CONF_THRESHOLD", "0.10"))
    IOU_THRESHOLD: float = float(os.getenv("IOU_THRESHOLD", "0.45"))
    IMG_SIZE: int = int(os.getenv("IMG_SIZE", "640"))
    MAX_IMAGE_SIZE: int = int(os.getenv("MAX_IMAGE_SIZE", "4096"))
    MIN_IMAGE_SIZE: int = int(os.getenv("MIN_IMAGE_SIZE", "64"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "16"))
    
    CLASSES: dict = {
        0: "apple_scab",
        1: "black_rot",
        2: "cedar_apple_rust",
        3: "powdery_mildew",
        4: "healthy_apple",
        5: "other"
    }
    
    NUM_CLASSES: int = 6
    
    MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "5000"))
    HISTORY_TTL_SECONDS: int = int(os.getenv("HISTORY_TTL_SECONDS", "86400"))
    
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "600"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json" if os.getenv("PROD") else "text")
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    
    ENABLE_WEBSOCKET: bool = os.getenv("ENABLE_WEBSOCKET", "true").lower() == "true"
    WS_HEARTBEAT_INTERVAL: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
