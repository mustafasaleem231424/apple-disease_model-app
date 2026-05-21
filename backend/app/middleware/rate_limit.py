"""
Rate limiting middleware
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.logging_config import get_logger

logger = get_logger("middleware.rate_limit")

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60, burst: int = 10):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.burst = burst
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, Dict[str, int]]:
        now = time.time()
        window_start = now - self.window_seconds
        
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > window_start
        ]
        
        request_count = len(self.requests[client_ip])
        remaining = max(0, self.max_requests - request_count)
        reset_time = int(self.window_seconds - (now - self.requests[client_ip][0])) if self.requests[client_ip] else 0
        
        info = {
            "X-RateLimit-Limit": self.max_requests,
            "X-RateLimit-Remaining": remaining,
            "X-RateLimit-Reset": reset_time
        }
        
        if request_count >= self.max_requests:
            return False, info
        
        if request_count < self.burst:
            self.requests[client_ip].append(now)
            return True, info
        
        self.requests[client_ip].append(now)
        return True, info
    
    def cleanup(self):
        now = time.time()
        window_start = now - self.window_seconds
        for ip in list(self.requests.keys()):
            self.requests[ip] = [t for t in self.requests[ip] if t > window_start]
            if not self.requests[ip]:
                del self.requests[ip]

rate_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_PER_MINUTE,
    burst=settings.RATE_LIMIT_BURST
)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        
        if client_ip == "127.0.0.1" or client_ip == "localhost":
            response = await call_next(request)
            return response
        
        allowed, headers = rate_limiter.is_allowed(client_ip)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": headers.get("X-RateLimit-Reset", 60)
                },
                headers={
                    "Retry-After": str(headers.get("X-RateLimit-Reset", 60)),
                    "X-RateLimit-Limit": str(headers["X-RateLimit-Limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(headers["X-RateLimit-Reset"])
                }
            )
        
        response = await call_next(request)
        
        for key, value in headers.items():
            response.headers[key] = str(value)
        
        return response
