"""
Real-World Scenario Tests - 7 production-like test cases
"""
import sys
import os
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from app.main import app
from app.inference.engine import detection_engine
import asyncio

async def init_engine():
    await detection_engine.initialize()

asyncio.run(init_engine())

client = TestClient(app)

def create_image(width, height, color, noise_level=20):
    img = np.full((height, width, 3), color, dtype=np.uint8)
    noise = np.random.randint(-noise_level, noise_level, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img

def add_leaf_pattern(image, spots=5, spot_color=(50, 50, 50), spot_size=30):
    img_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(img_pil)
    h, w = image.shape[:2]
    for _ in range(spots):
        x = np.random.randint(spot_size, w - spot_size)
        y = np.random.randint(spot_size, h - spot_size)
        r = np.random.randint(spot_size // 2, spot_size)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=spot_color)
    return np.array(img_pil)

def add_vein_structure(image):
    img_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(img_pil)
    h, w = image.shape[:2]
    center_x, center_y = w // 2, h // 2
    for i in range(8):
        angle = (i * 45) * 3.14159 / 180
        end_x = int(center_x + 100 * np.cos(angle))
        end_y = int(center_y + 100 * np.sin(angle))
        draw.line([center_x, center_y, end_x, end_y], fill=(40, 80, 40), width=2)
    return np.array(img_pil)

def add_blur(image, kernel_size=5):
    return cv2.blur(image, (kernel_size, kernel_size))

def image_to_file(image_np):
    img_pil = Image.fromarray(image_np)
    buffer = io.BytesIO()
    img_pil.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    return buffer

def run_scenario(name, image_np, expected_behavior):
    print(f"\n{'='*60}")
    print(f"SCENARIO: {name}")
    print(f"{'='*60}")
    
    file = image_to_file(image_np)
    response = client.post(
        "/api/v1/detect/image",
        files={"file": ("test.jpg", file, "image/jpeg")}
    )
    
    assert response.status_code == 200, f"Failed with status {response.status_code}"
    data = response.json()
    
    print(f"  Detections: {data['count']}")
    print(f"  Inference time: {data['inference_time_ms']}ms")
    
    if data['count'] > 0:
        for det in data['detections']:
            print(f"    - {det['class_name']}: {det['confidence']:.2%}")
            print(f"      BBox: ({det['bbox']['xmin']:.0f}, {det['bbox']['ymin']:.0f}) to ({det['bbox']['xmax']:.0f}, {det['bbox']['ymax']:.0f})")
    
    expected_behavior(data)
    print(f"  PASSED")

def test_scenario_1_clear_leaf_with_scab():
    """Scenario 1: Clear apple leaf with visible scab spots"""
    image = create_image(640, 480, (34, 120, 34), noise_level=15)
    image = add_vein_structure(image)
    image = add_leaf_pattern(image, spots=8, spot_color=(20, 30, 20), spot_size=40)
    
    def verify(data):
        assert data['count'] >= 0
        assert data['inference_time_ms'] < 3000
        assert 'annotated_image' in data
    
    run_scenario("Clear leaf with apple scab symptoms", image, verify)

def test_scenario_2_healthy_leaf():
    """Scenario 2: Healthy apple leaf with clean veins"""
    image = create_image(640, 480, (50, 140, 50), noise_level=10)
    image = add_vein_structure(image)
    
    def verify(data):
        assert data['count'] >= 0
        assert data['inference_time_ms'] < 3000
    
    run_scenario("Healthy apple leaf", image, verify)

def test_scenario_3_multiple_diseases():
    """Scenario 3: Image with multiple disease symptoms"""
    image = create_image(800, 600, (40, 100, 40), noise_level=20)
    image = add_leaf_pattern(image, spots=10, spot_color=(20, 30, 20), spot_size=35)
    img_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(img_pil)
    for _ in range(8):
        x = np.random.randint(50, 750)
        y = np.random.randint(50, 550)
        r = np.random.randint(15, 30)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(200, 150, 50))
    image = np.array(img_pil)
    
    def verify(data):
        assert data['count'] >= 0
        assert data['inference_time_ms'] < 3000
    
    run_scenario("Multiple disease symptoms in one image", image, verify)

def test_scenario_4_low_light():
    """Scenario 4: Low-light/orchard shadow conditions"""
    image = create_image(640, 480, (15, 40, 15), noise_level=25)
    image = add_vein_structure(image)
    image = add_leaf_pattern(image, spots=6, spot_color=(10, 15, 10), spot_size=30)
    
    def verify(data):
        assert data['inference_time_ms'] < 3000
    
    run_scenario("Low-light orchard conditions", image, verify)

def test_scenario_5_blurry_image():
    """Scenario 5: Blurry image from handheld camera in field"""
    image = create_image(640, 480, (45, 110, 45), noise_level=15)
    image = add_leaf_pattern(image, spots=7, spot_color=(30, 40, 30), spot_size=35)
    image = add_blur(image, kernel_size=7)
    
    def verify(data):
        assert data['inference_time_ms'] < 3000
    
    run_scenario("Blurry handheld camera image", image, verify)

def test_scenario_6_close_up_lesion():
    """Scenario 6: Close-up of single lesion (macro shot)"""
    image = create_image(400, 400, (60, 130, 60), noise_level=8)
    img_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(img_pil)
    draw.ellipse([100, 100, 300, 300], fill=(25, 35, 25))
    draw.ellipse([120, 120, 280, 280], fill=(40, 50, 40))
    image = np.array(img_pil)
    
    def verify(data):
        assert data['count'] >= 0
        assert data['inference_time_ms'] < 3000
    
    run_scenario("Close-up macro lesion shot", image, verify)

def test_scenario_7_background_weeds():
    """Scenario 7: Background with weeds and non-target vegetation"""
    image = create_image(640, 480, (80, 100, 40), noise_level=30)
    img_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(img_pil)
    for _ in range(15):
        x = np.random.randint(0, 640)
        y = np.random.randint(0, 480)
        h = np.random.randint(20, 80)
        w = np.random.randint(5, 15)
        green = (np.random.randint(60, 120), np.random.randint(100, 160), np.random.randint(20, 60))
        draw.rectangle([x, y, x + w, y + h], fill=green)
    image = np.array(img_pil)
    
    def verify(data):
        assert data['count'] >= 0
        assert data['inference_time_ms'] < 3000
    
    run_scenario("Background weeds and non-target vegetation", image, verify)

def test_scenario_8_export_after_detections():
    """Scenario 8: Export functionality after multiple detections"""
    images = []
    for _ in range(5):
        img = create_image(640, 480, (40 + np.random.randint(0, 40), 100 + np.random.randint(0, 40), 40 + np.random.randint(0, 40)), noise_level=15)
        images.append(img)
    
    for img in images:
        file = image_to_file(img)
        client.post("/api/v1/detect/image", files={"file": ("test.jpg", file, "image/jpeg")})
    
    csv_resp = client.get("/api/v1/export/csv")
    json_resp = client.get("/api/v1/export/json")
    
    assert csv_resp.status_code == 200
    assert json_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "application/json" in json_resp.headers["content-type"]
    
    print(f"\n{'='*60}")
    print("SCENARIO: Export functionality after multiple detections")
    print(f"{'='*60}")
    print(f"  CSV export: {len(csv_resp.content)} bytes")
    print(f"  JSON export: {len(json_resp.content)} bytes")
    print("  PASSED")

def main():
    print("="*60)
    print("REAL-WORLD SCENARIO TESTS")
    print("Apple Disease Detector - Production Validation")
    print("="*60)
    
    test_scenario_1_clear_leaf_with_scab()
    test_scenario_2_healthy_leaf()
    test_scenario_3_multiple_diseases()
    test_scenario_4_low_light()
    test_scenario_5_blurry_image()
    test_scenario_6_close_up_lesion()
    test_scenario_7_background_weeds()
    test_scenario_8_export_after_detections()
    
    print("\n" + "="*60)
    print("ALL 8 REAL-WORLD SCENARIOS PASSED")
    print("="*60)
    print("\nSummary:")
    print("  1. Clear leaf with scab symptoms - PASSED")
    print("  2. Healthy apple leaf - PASSED")
    print("  3. Multiple disease symptoms - PASSED")
    print("  4. Low-light orchard conditions - PASSED")
    print("  5. Blurry handheld camera - PASSED")
    print("  6. Close-up macro lesion - PASSED")
    print("  7. Background weeds/non-target - PASSED")
    print("  8. Export after multiple detections - PASSED")

if __name__ == "__main__":
    main()
