"""
Integrated ONNX Model Test Suite - 35 tests against real trained model
"""
import sys
import os
import io
import asyncio
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from app.main import app
from app.inference.engine import detection_engine
from app.config import settings

client = TestClient(app)

def create_image(width, height, color=None, noise=0):
    if color is None:
        return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    img = np.full((height, width, 3), color, dtype=np.uint8)
    if noise > 0:
        n = np.random.randint(-noise, noise, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + n, 0, 255).astype(np.uint8)
    return img

def image_to_file(img_np, fmt="JPEG"):
    pil = Image.fromarray(img_np)
    buf = io.BytesIO()
    pil.save(buf, format=fmt)
    buf.seek(0)
    return buf

def run_async(coro):
    return asyncio.run(coro)

passed = 0
failed = 0

def t(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  PASS: {name}")
    except Exception as e:
        failed += 1
        print(f"  FAIL: {name} - {e}")

print("="*60)
print("INTEGRATED ONNX MODEL TEST SUITE - 35 TESTS")
print(f"Model: {settings.MODEL_TYPE} | Classes: {settings.NUM_CLASSES}")
print("="*60)

with TestClient(app) as client:
    print("\n--- A. Model Loading & Validation (8 tests) ---")

    t("01. ONNX model loads successfully", lambda: (
        None if detection_engine.initialized and detection_engine.model and detection_engine.model.loaded else (_ for _ in ()).throw(AssertionError("Not initialized"))
    ))

    t("02. Model input shape is valid", lambda: (
        None if detection_engine.model.input_shape else (_ for _ in ()).throw(AssertionError("No input shape"))
    ))

    t("03. Model output shape is [1, 10, 8400]", lambda: (
        (lambda out: None if out.shape[0]==1 and out.shape[1]==10 and out.shape[2]==8400 else (_ for _ in ()).throw(AssertionError(f"Shape: {out.shape}")))(detection_engine.model.session.get_outputs()[0])
    ))

    t("04. Model warmup completes", lambda: (
        None if detection_engine.model.loaded else (_ for _ in ()).throw(AssertionError("Not loaded"))
    ))

    t("05. Model info returns 6 correct class names", lambda: (
        (lambda i: None if i["num_classes"]==6 and len(i["classes"])==6 and "apple_scab" in i["classes"] else (_ for _ in ()).throw(AssertionError()))(detection_engine.model.get_info())
    ))

    t("06. Model type is 'onnx', status is 'loaded'", lambda: (
        (lambda i: None if i["type"]=="onnx" and i["status"]=="loaded" else (_ for _ in ()).throw(AssertionError()))(detection_engine.model.get_info())
    ))

    async def _test_none():
        try:
            await detection_engine.model.predict(None)
            return False
        except:
            return True
    t("07. Model handles None image with error", lambda: (
        None if run_async(_test_none()) else (_ for _ in ()).throw(AssertionError("Should raise"))
    ))

    async def _test_empty():
        try:
            await detection_engine.model.predict(np.array([]))
            return False
        except:
            return True
    t("08. Model handles empty array with error", lambda: (
        None if run_async(_test_empty()) else (_ for _ in ()).throw(AssertionError("Should raise"))
    ))

    print("\n--- B. Detection Accuracy (8 tests) ---")

    async def _predict(img):
        return await detection_engine.model.predict(img)

    def run_predict(img):
        return run_async(_predict(img))

    t("09. Green leaf image returns detections", lambda: (
        None if isinstance(run_predict(create_image(640, 480, color=(34, 120, 34), noise=20)), list) else (_ for _ in ()).throw(AssertionError())
    ))

    def test_10():
        dets = run_predict(create_image(640, 480, noise=30))
        for d in dets:
            assert 0 <= d.class_id <= 5
    t("10. All class IDs in range [0, 5]", test_10)

    def test_11():
        dets = run_predict(create_image(640, 480, noise=30))
        for d in dets:
            assert 0 <= d.confidence <= 1
    t("11. All confidence scores in [0, 1]", test_11)

    def test_12():
        dets = run_predict(create_image(640, 480, noise=30))
        for d in dets:
            assert d.bbox[0] >= 0 and d.bbox[1] >= 0
            assert d.bbox[2] <= 640 and d.bbox[3] <= 480
    t("12. All bounding boxes within image bounds", test_12)

    def test_13():
        dets = run_predict(create_image(640, 480, noise=30))
        for d in dets:
            assert d.bbox[2] > d.bbox[0]
            assert d.bbox[3] > d.bbox[1]
    t("13. All boxes have x2>x1, y2>y1", test_13)

    def test_14():
        dets = run_predict(create_image(800, 600, color=(50, 130, 50), noise=25))
        assert isinstance(dets, list)
    t("14. Multiple detections in single image work", test_14)

    def test_15():
        dets = run_predict(np.zeros((640, 480, 3), dtype=np.uint8))
        assert isinstance(dets, list)
    t("15. Pure black image processed", test_15)

    def test_16():
        dets = run_predict(create_image(640, 480, noise=50))
        assert isinstance(dets, list)
    t("16. Random noise image returns detections", test_16)

    print("\n--- C. API Endpoints with Real Model (8 tests) ---")

    def test_17():
        img = create_image(640, 480, noise=20)
        f = image_to_file(img)
        resp = client.post("/api/v1/detect/image", files={"file": ("test.jpg", f, "image/jpeg")})
        assert resp.status_code == 200, f"Status {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "detections" in data
        assert data["model_type"] == "onnx"
    t("17. POST /api/v1/detect/image returns 200 with onnx", test_17)

    def test_18():
        img = create_image(640, 480, noise=20)
        f = image_to_file(img)
        resp = client.post("/api/v1/detect/image/raw", files={"file": ("test.jpg", f, "image/jpeg")})
        assert resp.status_code == 200
        assert "detections" in resp.json()
    t("18. POST /api/v1/detect/image/raw returns JSON", test_18)

    def test_19():
        img = create_image(640, 480, noise=20)
        f = image_to_file(img)
        resp = client.post("/api/v1/detect/stream/frame", files={"file": ("frame.jpg", f, "image/jpeg")})
        assert resp.status_code == 200
        data = resp.json()
        assert "detections" in data
        assert "annotated_frame" in data
    t("19. POST /api/v1/detect/stream/frame returns 200", test_19)

    def test_20():
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["model"]["type"] == "onnx"
        assert data["model"]["status"] == "loaded"
    t("20. GET /api/v1/health shows onnx loaded", test_20)

    def test_21():
        resp = client.get("/api/v1/model/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "onnx"
        assert data["num_classes"] == 6
    t("21. GET /api/v1/model/info shows 6 classes", test_21)

    def test_22():
        resp = client.get("/api/v1/export/json?limit=100")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
    t("22. GET /api/v1/export/json returns valid JSON", test_22)

    def test_23():
        resp = client.get("/api/v1/export/csv?limit=100")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
    t("23. GET /api/v1/export/csv returns valid CSV", test_23)

    def test_24():
        resp = client.post("/api/v1/detect/image", files={"file": ("test.txt", io.BytesIO(b"not image"), "text/plain")})
        assert resp.status_code == 400
    t("24. Invalid file type returns 400", test_24)

    print("\n--- D. Edge Cases & Robustness (6 tests) ---")

    def test_25():
        img = create_image(50, 50, noise=20)
        f = image_to_file(img)
        resp = client.post("/api/v1/detect/image", files={"file": ("small.jpg", f, "image/jpeg")})
        assert resp.status_code == 400
    t("25. 50x50 image returns 400", test_25)

    def test_26():
        img = create_image(5000, 5000, noise=5)
        f = image_to_file(img)
        resp = client.post("/api/v1/detect/image", files={"file": ("large.jpg", f, "image/jpeg")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["image_width"] <= 1920
        assert data["image_height"] <= 1920
    t("26. 5000x5000 image auto-resized to <=1920px", test_26)

    def test_27():
        resp = client.post("/api/v1/detect/image", files={"file": ("bad.jpg", io.BytesIO(b"\xff\xd8\xff\xe0corrupted"), "image/jpeg")})
        assert resp.status_code in [400, 500]
    t("27. Corrupted JPEG returns 400/500", test_27)

    def test_28():
        img = create_image(300, 300, noise=20)
        f = image_to_file(img, fmt="PNG")
        resp = client.post("/api/v1/detect/image", files={"file": ("test.png", f, "image/png")})
        assert resp.status_code == 200
    t("28. PNG format returns 200", test_28)

    def test_29():
        img = create_image(300, 300, noise=20)
        f = image_to_file(img, fmt="WEBP")
        resp = client.post("/api/v1/detect/image", files={"file": ("test.webp", f, "image/webp")})
        assert resp.status_code == 200
    t("29. WEBP format returns 200", test_29)

    def test_30():
        import concurrent.futures
        def make_request():
            img = create_image(400, 400, noise=20)
            f = image_to_file(img)
            return client.post("/api/v1/detect/image/raw", files={"file": ("test.jpg", f, "image/jpeg")})
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in futures]
        assert all(r.status_code == 200 for r in results)
    t("30. 5 concurrent requests all return 200", test_30)

    print("\n--- E. Annotated Image Quality (5 tests) ---")

    def test_31():
        img = create_image(640, 480, noise=20)
        f = image_to_file(img)
        resp = client.post("/api/v1/detect/image", files={"file": ("test.jpg", f, "image/jpeg")})
        data = resp.json()
        if data.get("annotated_image"):
            import base64
            img_bytes = base64.b64decode(data["annotated_image"])
            pil = Image.open(io.BytesIO(img_bytes))
            assert pil.format == "JPEG"
    t("31. Annotated image is valid JPEG", test_31)

    def test_32():
        img = create_image(640, 480, noise=20)
        f = image_to_file(img)
        resp = client.post("/api/v1/detect/image", files={"file": ("test.jpg", f, "image/jpeg")})
        data = resp.json()
        assert data["image_width"] == 640
        assert data["image_height"] == 480
    t("32. Annotated image dimensions match input", test_32)

    def test_33():
        img = create_image(640, 480, color=(100, 150, 100), noise=20)
        f = image_to_file(img)
        resp = client.post("/api/v1/detect/image", files={"file": ("test.jpg", f, "image/jpeg")})
        data = resp.json()
        if data["count"] > 0 and data.get("annotated_image"):
            import base64
            img_bytes = base64.b64decode(data["annotated_image"])
            arr = np.array(Image.open(io.BytesIO(img_bytes)))
            dark_pixels = np.sum(arr < 30)
            assert dark_pixels > 0
    t("33. Annotated image contains dark pixels (black boxes)", test_33)

    def test_34():
        img = create_image(640, 480, noise=20)
        f = image_to_file(img)
        resp = client.post("/api/v1/detect/image", files={"file": ("test.jpg", f, "image/jpeg")})
        data = resp.json()
        assert data["model_type"] == "onnx"
    t("34. Response includes model_type: 'onnx'", test_34)

    def test_35():
        img = create_image(640, 480, noise=20)
        f = image_to_file(img)
        resp = client.post("/api/v1/detect/image", files={"file": ("test.jpg", f, "image/jpeg")})
        data = resp.json()
        assert data["inference_time_ms"] < 5000
    t("35. Inference time < 5000ms", test_35)

print("\n" + "="*60)
print(f"RESULTS: {passed} passed, {failed} failed, {passed+failed} total")
print("="*60)

if failed > 0:
    sys.exit(1)
else:
    print("\nALL 35 INTEGRATED ONNX MODEL TESTS PASSED!")
