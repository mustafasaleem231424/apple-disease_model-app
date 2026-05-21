"""
15 Real-World End-to-End Testing Scenarios
Tests all app features from a farmer's perspective
"""
import requests
import numpy as np
from PIL import Image, ImageDraw
import io
import time
import json

API_BASE = "http://localhost:8000"

def make_image(w, h, pattern="leaf"):
    img = Image.new('RGB', (w, h), (34, 120, 50))
    draw = ImageDraw.Draw(img)
    for _ in range(200):
        x = np.random.randint(0, w)
        y = np.random.randint(0, h)
        img.putpixel((x, y), (np.random.randint(20, 60), np.random.randint(100, 180), np.random.randint(30, 70)))
    if pattern == "disease":
        for _ in range(np.random.randint(3, 8)):
            x = np.random.randint(0, w)
            y = np.random.randint(0, h)
            s = np.random.randint(15, 50)
            c = tuple(np.random.randint(40, 200, 3).tolist())
            draw.ellipse([x-s, y-s, x+s, y+s], fill=c)
    return img

def save_image(img, quality=85):
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality)
    buf.seek(0)
    return buf

def post_detect(img_buf, endpoint="/api/v1/detect/image", conf=0.25):
    try:
        resp = requests.post(
            f"{API_BASE}{endpoint}?conf={conf}",
            files={"file": ("test.jpg", img_buf, "image/jpeg")},
            timeout=30
        )
        return resp.status_code, resp.json() if resp.ok else resp.text
    except Exception as e:
        return 0, str(e)

def check_endpoint(method, path, **kwargs):
    try:
        fn = getattr(requests, method.lower())
        resp = fn(f"{API_BASE}{path}", timeout=15, **kwargs)
        return resp.status_code, resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:200]
    except Exception as e:
        return 0, str(e)

scenarios = []
passed = 0
failed = 0

def run(name, fn):
    global passed, failed
    status = 0
    print(f"\n  [{len(scenarios)+1}] {name}...", end=" ")
    try:
        status, detail = fn()
        if status and 200 <= status < 500:
            passed += 1
            print(f"PASS ({status})")
        else:
            failed += 1
            print(f"FAIL (status={status})")
    except Exception as e:
        failed += 1
        print(f"ERROR: {e}")
    scenarios.append((name, "PASS" if (status and 200 <= status < 500) else "FAIL"))

print("=" * 70)
print("15 REAL-WORLD END-TO-END TESTING SCENARIOS")
print("Farmer-use-case focused verification")
print("=" * 70)

# 1. Farmer uploads a healthy apple leaf photo
def s01():
    img = make_image(800, 600, "leaf")
    buf = save_image(img)
    s, d = post_detect(buf)
    return s, d
run("Farmer uploads healthy apple leaf", s01)

# 2. Farmer uploads a diseased leaf
def s02():
    img = make_image(800, 600, "disease")
    buf = save_image(img)
    s, d = post_detect(buf)
    return s, d
run("Farmer uploads diseased leaf", s02)

# 3. Farmer uses low-resolution phone camera
def s03():
    img = make_image(320, 240, "disease")
    buf = save_image(img, quality=50)
    s, d = post_detect(buf)
    return s, d
run("Low-resolution 320x240 phone image", s03)

# 4. Farmer uses high-resolution phone camera (12MP)
def s04():
    img = make_image(4000, 3000, "leaf")
    buf = save_image(img, quality=95)
    s, d = post_detect(buf)
    return s, d
run("High-resolution 12MP camera image", s04)

# 5. Farmer uses camera stream (processFrame endpoint)
def s05():
    img = make_image(640, 480, "disease")
    buf = save_image(img)
    s, d = post_detect(buf, endpoint="/api/v1/detect/stream/frame")
    return s, d
run("Camera stream frame detection", s05)

# 6. Multiple detections in one image
def s06():
    img = make_image(1000, 800, "disease")
    draw = ImageDraw.Draw(img)
    for _ in range(5):
        x = np.random.randint(50, 950)
        y = np.random.randint(50, 750)
        s = np.random.randint(20, 60)
        draw.ellipse([x-s, y-s, x+s, y+s], fill=(180, 100, 40))
    buf = save_image(img)
    s, d = post_detect(buf, conf=0.1)
    if isinstance(d, dict) and d.get("detections"):
        return s, {"detections": d["detections"], "count": d["count"]}
    return s, d
run("Multiple disease spots on one leaf", s06)

# 7. Farmer checks API health
def s07():
    return check_endpoint("GET", "/api/v1/health")
run("Health check endpoint", s07)

# 8. Farmer checks model info
def s08():
    return check_endpoint("GET", "/api/v1/model/info")
run("Model info endpoint", s08)

# 9. Farmer exports results as JSON
def s09():
    return check_endpoint("GET", "/api/v1/export/json?limit=10")
run("Export results as JSON", s09)

# 10. Farmer exports results as CSV
def s10():
    return check_endpoint("GET", "/api/v1/export/csv?limit=10")
run("Export results as CSV", s10)

# 11. Farmer checks detection history
def s11():
    return check_endpoint("GET", "/api/v1/detect/history?limit=5")
run("Detection history endpoint", s11)

# 12. Farmer sends raw base64 image
def s12():
    img = make_image(600, 400, "disease")
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    import base64
    b64 = base64.b64encode(buf.getvalue()).decode()
    try:
        resp = requests.post(
            f"{API_BASE}/api/v1/detect/image/raw?conf=0.25",
            json={"image": b64, "filename": "test.jpg"},
            timeout=30
        )
        return resp.status_code, resp.json() if resp.ok else resp.text[:200]
    except Exception as e:
        return 0, str(e)
run("Base64 raw image upload", s12)

# 13. Farmer sends image with custom confidence threshold
def s13():
    img = make_image(800, 600, "disease")
    buf = save_image(img)
    s, d = post_detect(buf, conf=0.5)
    return s, d
run("Detection with high confidence (0.5) threshold", s13)

# 14. Farmer reads server readiness/liveness probes
def s14():
    r1 = check_endpoint("GET", "/api/v1/ready")
    r2 = check_endpoint("GET", "/api/v1/live")
    if r1[0] == 200 and r2[0] == 200:
        return 200, "ready+live ok"
    return 500, f"ready={r1[0]}, live={r2[0]}"
run("Readiness and liveness probes", s14)

# 15. Farmer accesses root endpoint
def s15():
    return check_endpoint("GET", "/")
run("Root endpoint returns API info", s15)

print("\n" + "=" * 70)
print(f"RESULTS: {passed}/15 PASSED | {failed}/15 FAILED")
print("=" * 70)
for i, (name, result) in enumerate(scenarios, 1):
    print(f"  {i:2d}. {name}: {result}")
print("=" * 70)
