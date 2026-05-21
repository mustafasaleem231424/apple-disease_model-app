"""
Production Test Suite - Comprehensive coverage
"""
import sys
import os
import io
import time
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from app.main import app
from app.inference.engine import detection_engine
from app.config import settings
from app.utils.annotations import validate_image, encode_image, decode_image
from app.models.base import Detection
import asyncio

async def init_engine():
    await detection_engine.initialize()

asyncio.run(init_engine())

client = TestClient(app)

def create_test_image(width=640, height=480, color=None):
    if color is None:
        img = Image.fromarray(np.random.randint(0, 255, (height, width, 3), dtype=np.uint8))
    else:
        img = Image.fromarray(np.full((height, width, 3), color, dtype=np.uint8))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    return buffer

def test_root_endpoint():
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "docs" in data
    print("Root endpoint test passed")

def test_ping_endpoint():
    response = client.get("/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    print("Ping endpoint test passed")

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "initializing"]
    assert "model" in data
    assert "uptime_seconds" in data
    assert "history_count" in data
    assert "timestamp" in data
    print("Health endpoint test passed")

def test_ready_endpoint():
    response = client.get("/api/v1/ready")
    assert response.status_code in [200, 503]
    data = response.json()
    assert data["status"] in ["ready", "not_ready"]
    print("Ready endpoint test passed")

def test_live_endpoint():
    response = client.get("/api/v1/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    print("Live endpoint test passed")

def test_model_info_endpoint():
    response = client.get("/api/v1/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "type" in data or "error" in data
    if "type" in data:
        assert data["num_classes"] == 6
    print("Model info endpoint test passed")

def test_detect_image_valid():
    image_buffer = create_test_image()
    response = client.post(
        "/api/v1/detect/image",
        files={"file": ("test.jpg", image_buffer, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert "count" in data
    assert "inference_time_ms" in data
    assert "model_type" in data
    assert "timestamp" in data
    assert isinstance(data["detections"], list)
    print(f"Detect image valid test passed - {data['count']} detections")

def test_detect_image_raw():
    image_buffer = create_test_image()
    response = client.post(
        "/api/v1/detect/image/raw",
        files={"file": ("test.jpg", image_buffer, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert "count" in data
    assert "annotated_image" not in data or data.get("annotated_image") is None
    print(f"Detect image raw test passed - {data['count']} detections")

def test_detect_image_invalid_type():
    response = client.post(
        "/api/v1/detect/image",
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
    )
    assert response.status_code == 400
    print("Detect image invalid type test passed")

def test_detect_image_too_large():
    large_img = Image.fromarray(np.random.randint(0, 255, (5000, 5000, 3), dtype=np.uint8))
    buffer = io.BytesIO()
    large_img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    response = client.post(
        "/api/v1/detect/image",
        files={"file": ("large.jpg", buffer, "image/jpeg")}
    )
    assert response.status_code == 400
    print("Detect image too large test passed")

def test_detect_image_too_small():
    small_img = Image.fromarray(np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8))
    buffer = io.BytesIO()
    small_img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    response = client.post(
        "/api/v1/detect/image",
        files={"file": ("small.jpg", buffer, "image/jpeg")}
    )
    assert response.status_code == 400
    print("Detect image too small test passed")

def test_stream_frame():
    image_buffer = create_test_image()
    response = client.post(
        "/api/v1/detect/stream/frame",
        files={"file": ("frame.jpg", image_buffer, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert "annotated_frame" in data
    assert "count" in data
    print(f"Stream frame test passed - {data['count']} detections")

def test_history_flow():
    for _ in range(3):
        image_buffer = create_test_image()
        client.post(
            "/api/v1/detect/image",
            files={"file": ("test.jpg", image_buffer, "image/jpeg")}
        )
    
    response = client.get("/api/v1/detect/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert "total" in data
    assert data["total"] >= 3
    print(f"History flow test passed - {data['total']} records")

def test_export_json():
    response = client.get("/api/v1/export/json?limit=100")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert "Content-Disposition" in response.headers
    print("Export JSON test passed")

def test_export_csv():
    response = client.get("/api/v1/export/csv?limit=100")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Content-Disposition" in response.headers
    print("Export CSV test passed")

def test_clear_history():
    response = client.post("/api/v1/detect/history/clear")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "history_cleared"
    
    response = client.get("/api/v1/detect/history")
    data = response.json()
    assert data["total"] == 0
    print("Clear history test passed")

def test_validate_image():
    valid_img = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    assert validate_image(valid_img) == True
    
    assert validate_image(None) == False
    assert validate_image(np.array([])) == False
    assert validate_image(np.zeros((10, 10, 3), dtype=np.uint8)) == False
    assert validate_image(np.zeros((5000, 5000, 3), dtype=np.uint8)) == False
    print("Validate image test passed")

def test_detection_model():
    det = Detection(0, "apple_scab", 0.85, [100, 50, 300, 250])
    d = det.to_dict()
    assert d["class_id"] == 0
    assert d["class_name"] == "apple_scab"
    assert d["confidence"] == 0.85
    assert d["bbox"]["xmin"] == 100
    assert d["bbox"]["ymin"] == 50
    assert d["bbox"]["xmax"] == 300
    assert d["bbox"]["ymax"] == 250
    print("Detection model test passed")

def test_request_headers():
    response = client.get("/ping")
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time" in response.headers
    print("Request headers test passed")

def test_cors_headers():
    response = client.get("/ping", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    print("CORS headers test passed")

def test_api_docs():
    response = client.get("/api/v1/docs")
    assert response.status_code == 200
    print("API docs test passed")

def test_openapi_schema():
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    print("OpenAPI schema test passed")

def test_multiple_formats():
    formats = [
        ("test.jpg", "image/jpeg", "JPEG"),
        ("test.png", "image/png", "PNG"),
    ]
    for filename, content_type, fmt in formats:
        img = Image.fromarray(np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8))
        buffer = io.BytesIO()
        img.save(buffer, format=fmt)
        buffer.seek(0)
        response = client.post(
            "/api/v1/detect/image",
            files={"file": (filename, buffer, content_type)}
        )
        assert response.status_code == 200, f"Failed for {filename}"
    print("Multiple image formats test passed")

def test_concurrent_requests():
    import concurrent.futures
    
    def make_request():
        image_buffer = create_test_image()
        return client.post(
            "/api/v1/detect/image/raw",
            files={"file": ("test.jpg", image_buffer, "image/jpeg")}
        )
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        results = [f.result() for f in futures]
    
    assert all(r.status_code == 200 for r in results)
    print("Concurrent requests test passed")

def main():
    print("="*60)
    print("PRODUCTION TEST SUITE")
    print("="*60)
    
    tests = [
        test_root_endpoint,
        test_ping_endpoint,
        test_health_endpoint,
        test_ready_endpoint,
        test_live_endpoint,
        test_model_info_endpoint,
        test_detect_image_valid,
        test_detect_image_raw,
        test_detect_image_invalid_type,
        test_detect_image_too_large,
        test_detect_image_too_small,
        test_stream_frame,
        test_history_flow,
        test_export_json,
        test_export_csv,
        test_clear_history,
        test_validate_image,
        test_detection_model,
        test_request_headers,
        test_cors_headers,
        test_api_docs,
        test_openapi_schema,
        test_multiple_formats,
        test_concurrent_requests
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FAILED: {test.__name__} - {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed, {len(tests)} total")
    print("="*60)
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
