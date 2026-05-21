"""
Apple Disease Detector - Production FastAPI Application
"""
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.logging_config import setup_logging, get_logger
from app.middleware import RateLimitMiddleware, RequestMiddleware
from app.api import detect, export, status
from app.inference.engine import detection_engine

logger = get_logger("main")

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist')
HAS_FRONTEND = os.path.isfile(os.path.join(FRONTEND_DIST, 'index.html'))

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Apple Disease Detector...")
    setup_logging()
    start_time = time.time()
    
    try:
        await detection_engine.initialize()
        logger.info(f"Model initialized in {time.time() - start_time:.2f}s")
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        raise
    
    app.state.start_time = start_time
    logger.info("Application started successfully")
    
    yield
    
    logger.info("Shutting down...")
    await detection_engine.cleanup()
    logger.info("Shutdown complete")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade automated apple disease detection pipeline for precision agriculture",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(RequestMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=["X-Request-ID", "X-Response-Time", "X-RateLimit-Remaining"]
)

app.include_router(detect.router, prefix=f"{settings.API_PREFIX}/detect", tags=["detection"])
app.include_router(export.router, prefix=f"{settings.API_PREFIX}/export", tags=["export"])
app.include_router(status.router, prefix=f"{settings.API_PREFIX}", tags=["status"])

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception: {exc}", exc_info=True, extra={"request_id": request_id})
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "request_id": request_id
        }
    )

@app.get("/api/info")
async def api_info():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": f"{settings.API_PREFIX}/docs",
        "frontend": HAS_FRONTEND
    }

@app.get("/ping")
async def ping():
    return {"status": "ok", "timestamp": time.time()}

if HAS_FRONTEND:
    logger.info(f"Serving frontend from: {FRONTEND_DIST}")
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    logger.warning("No frontend build found at frontend/dist/")
    @app.get("/")
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "running",
            "docs": f"{settings.API_PREFIX}/docs"
        }
