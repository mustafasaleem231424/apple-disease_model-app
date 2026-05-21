"""
Test API endpoints
"""
import asyncio
import sys
import os
import io
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from app.main import app
from app.inference.engine import detection_engine

async def init_engine():
    await detection_engine.initialize()

asyncio.run(init_engine())

client = TestClient(app)

def create_test_image():
    img = Image.fromarray(np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "Apple Disease Detector" in data["name"]
    print("Root endpoint test passed")

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data
    print("Health endpoint test passed")

def test_model_info():
    response = client.get("/api/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "type" in data or "error" in data
    if "type" in data:
        assert data["type"] == "mock"
        assert data["num_classes"] == 6
    print("Model info endpoint test passed")

def test_detect_image():
    image_buffer = create_test_image()
    response = client.post(
        "/api/detect/image",
        files={"file": ("test.jpg", image_buffer, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert "annotated_image" in data
    assert "count" in data
    assert isinstance(data["detections"], list)
    assert data["count"] == len(data["detections"])
    print(f"Detect image test passed - {data['count']} detections")

def test_detect_image_raw():
    image_buffer = create_test_image()
    response = client.post(
        "/api/detect/image/raw",
        files={"file": ("test.jpg", image_buffer, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert "count" in data
    print(f"Detect image raw test passed - {data['count']} detections")

def test_stream_start_stop():
    response = client.post("/api/detect/stream/start")
    assert response.status_code == 200
    assert response.json()["status"] == "stream_started"

    response = client.post("/api/detect/stream/stop")
    assert response.status_code == 200
    assert response.json()["status"] == "stream_stopped"
    print("Stream start/stop test passed")

def test_stream_frame():
    image_buffer = create_test_image()
    response = client.post(
        "/api/detect/stream/frame",
        files={"file": ("frame.jpg", image_buffer, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert "annotated_frame" in data
    print(f"Stream frame test passed - {data['count']} detections")

def test_history():
    image_buffer = create_test_image()
    client.post(
        "/api/detect/image",
        files={"file": ("test.jpg", image_buffer, "image/jpeg")}
    )

    response = client.get("/api/detect/history")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert len(data["history"]) > 0
    print(f"History test passed - {len(data['history'])} records")

def test_export_json():
    response = client.get("/api/export/json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    print("Export JSON test passed")

def test_export_csv():
    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    print("Export CSV test passed")

def test_clear_history():
    response = client.post("/api/detect/history/clear")
    assert response.status_code == 200
    assert response.json()["status"] == "history_cleared"

    response = client.get("/api/detect/history")
    data = response.json()
    assert len(data["history"]) == 0
    print("Clear history test passed")

def test_invalid_image():
    response = client.post(
        "/api/detect/image",
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
    )
    assert response.status_code == 400
    print("Invalid image test passed")

def main():
    print("Running API tests...\n")
    test_root()
    test_health()
    test_model_info()
    test_detect_image()
    test_detect_image_raw()
    test_stream_start_stop()
    test_stream_frame()
    test_history()
    test_export_json()
    test_export_csv()
    test_clear_history()
    test_invalid_image()
    print("\nAll API tests passed!")

if __name__ == "__main__":
    main()
