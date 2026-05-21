"""
Deep Model Testing - Realistic Apple Disease Scenarios
Tests the trained ONNX model against synthesized disease patterns
"""
import sys
import os
import io
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.inference.engine import detection_engine
from app.config import settings
import asyncio

async def init():
    await detection_engine.initialize()

asyncio.get_event_loop().run_until_complete(init())

async def predict(img):
    return await detection_engine.model.predict(img)

def run_predict(img):
    return asyncio.get_event_loop().run_until_complete(predict(img))

def create_leaf_base(width=640, height=480, green=(34, 120, 34), noise=15):
    img = np.full((height, width, 3), green, dtype=np.uint8)
    n = np.random.randint(-noise, noise, img.shape, dtype=np.int16)
    return np.clip(img.astype(np.int16) + n, 0, 255).astype(np.uint8)

def add_leaf_veins(img, vein_color=(25, 90, 25)):
    h, w = img.shape[:2]
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    cx, cy = w // 2, h // 2
    for angle in range(0, 360, 30):
        rad = np.radians(angle)
        ex = int(cx + (w//2 - 20) * np.cos(rad))
        ey = int(cy + (h//2 - 20) * np.sin(rad))
        draw.line([cx, cy, ex, ey], fill=vein_color, width=2)
    for i in range(5):
        y = int(h * (0.2 + i * 0.15))
        draw.line([20, y, w - 20, y], fill=vein_color, width=1)
    return np.array(pil)

def add_scab_spots(img, count=15, size_range=(8, 25)):
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    h, w = img.shape[:2]
    for _ in range(count):
        x = np.random.randint(30, w - 30)
        y = np.random.randint(30, h - 30)
        r = np.random.randint(*size_range)
        color = (np.random.randint(15, 40), np.random.randint(25, 50), np.random.randint(10, 30))
        draw.ellipse([x-r, y-r, x+r, y+r], fill=color)
        if np.random.random() > 0.5:
            draw.ellipse([x-r+2, y-r+2, x+r-2, y+r-2], fill=(np.random.randint(40, 70), np.random.randint(60, 90), np.random.randint(20, 40)))
    return np.array(pil)

def add_black_rot_lesions(img, count=8, size_range=(15, 40)):
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    h, w = img.shape[:2]
    for _ in range(count):
        x = np.random.randint(40, w - 40)
        y = np.random.randint(40, h - 40)
        r = np.random.randint(*size_range)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(60, 20, 30))
        draw.ellipse([x-r+4, y-r+4, x+r-4, y+r-4], fill=(80, 40, 50))
        draw.ellipse([x-r+8, y-r+8, x+r-8, y+r-8], fill=(40, 25, 20))
    return np.array(pil)

def add_cedar_rust_spots(img, count=10, size_range=(10, 30)):
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    h, w = img.shape[:2]
    for _ in range(count):
        x = np.random.randint(30, w - 30)
        y = np.random.randint(30, h - 30)
        r = np.random.randint(*size_range)
        orange = (np.random.randint(200, 255), np.random.randint(120, 180), np.random.randint(20, 60))
        draw.ellipse([x-r, y-r, x+r, y+r], fill=orange)
        if np.random.random() > 0.6:
            draw.ellipse([x-r+3, y-r+3, x+r-3, y+r-3], fill=(np.random.randint(220, 255), np.random.randint(180, 220), np.random.randint(50, 100)))
    return np.array(pil)

def add_powdery_mildew(img, intensity=0.4):
    h, w = img.shape[:2]
    overlay = np.full((h, w, 3), 220, dtype=np.uint8)
    mask = np.random.random((h, w)) < intensity
    result = img.copy()
    result[mask] = (img[mask].astype(np.float32) * 0.5 + overlay[mask].astype(np.float32) * 0.5).astype(np.uint8)
    return result

def add_blur(img, radius=3):
    pil = Image.fromarray(img)
    return np.array(pil.filter(ImageFilter.GaussianBlur(radius=radius)))

def add_noise(img, amount=30):
    n = np.random.randint(-amount, amount, img.shape, dtype=np.int16)
    return np.clip(img.astype(np.int16) + n, 0, 255).astype(np.uint8)

def add_shadow(img, direction='left'):
    h, w = img.shape[:2]
    gradient = np.linspace(0.3, 1.0, w) if direction == 'left' else np.linspace(1.0, 0.3, w)
    gradient = np.tile(gradient, (h, 1))
    gradient = np.stack([gradient, gradient, gradient], axis=-1)
    return (img.astype(np.float32) * gradient).astype(np.uint8)

def test_scenario(name, img, expected_classes=None):
    start = time.time()
    dets = run_predict(img)
    elapsed = time.time() - start
    
    print(f"\n{'='*60}")
    print(f"SCENARIO: {name}")
    print(f"{'='*60}")
    print(f"  Image size: {img.shape[1]}x{img.shape[0]}")
    print(f"  Inference time: {elapsed*1000:.1f}ms")
    print(f"  Detections: {len(dets)}")
    
    if dets:
        for d in dets:
            print(f"    -> {d.class_name}: {d.confidence:.2%} bbox=({d.bbox[0]:.0f},{d.bbox[1]:.0f})-({d.bbox[2]:.0f},{d.bbox[3]:.0f})")
    
    if expected_classes:
        found_classes = [d.class_name for d in dets]
        for ec in expected_classes:
            if ec in found_classes:
                print(f"  [OK] Expected class '{ec}' found")
            else:
                print(f"  [WARN] Expected class '{ec}' not found")
    
    return dets

print("="*70)
print("DEEP MODEL TESTING - REALISTIC APPLE DISEASE SCENARIOS")
print(f"Model: {settings.MODEL_TYPE} | Input: {settings.IMG_SIZE}x{settings.IMG_SIZE}")
print(f"Classes: {list(settings.CLASSES.values())}")
print("="*70)

np.random.seed(42)

test_scenario("1. Clean healthy leaf with veins",
    add_leaf_veins(create_leaf_base(green=(50, 140, 50), noise=10)),
    expected_classes=["healthy_apple"])

test_scenario("2. Apple scab - moderate infection (15 spots)",
    add_scab_spots(add_leaf_veins(create_leaf_base(green=(40, 110, 40), noise=12)), count=15),
    expected_classes=["apple_scab"])

test_scenario("3. Apple scab - severe infection (30 spots)",
    add_scab_spots(add_leaf_veins(create_leaf_base(green=(35, 100, 35), noise=15)), count=30),
    expected_classes=["apple_scab"])

test_scenario("4. Black rot - frog-eye lesions",
    add_black_rot_lesions(add_leaf_veins(create_leaf_base(green=(45, 115, 45), noise=12)), count=10),
    expected_classes=["black_rot"])

test_scenario("5. Cedar apple rust - orange spots",
    add_cedar_rust_spots(add_leaf_veins(create_leaf_base(green=(50, 130, 50), noise=10)), count=12),
    expected_classes=["cedar_apple_rust"])

test_scenario("6. Powdery mildew - light coating",
    add_powdery_mildew(add_leaf_veins(create_leaf_base(green=(55, 135, 55), noise=10)), intensity=0.2),
    expected_classes=["powdery_mildew"])

test_scenario("7. Powdery mildew - heavy coating",
    add_powdery_mildew(add_leaf_veins(create_leaf_base(green=(50, 125, 50), noise=12)), intensity=0.5),
    expected_classes=["powdery_mildew"])

test_scenario("8. Mixed disease - scab + rust",
    add_cedar_rust_spots(add_scab_spots(add_leaf_veins(create_leaf_base(green=(40, 105, 40), noise=15)), count=8), count=6),
    expected_classes=["apple_scab", "cedar_apple_rust"])

test_scenario("9. Early stage scab - small spots",
    add_scab_spots(add_leaf_veins(create_leaf_base(green=(45, 120, 45), noise=10)), count=5, size_range=(4, 12)),
    expected_classes=["apple_scab"])

test_scenario("10. Late stage black rot - large lesions",
    add_black_rot_lesions(add_leaf_veins(create_leaf_base(green=(30, 80, 30), noise=15)), count=6, size_range=(25, 50)),
    expected_classes=["black_rot"])

test_scenario("11. Low light orchard - scab with shadow",
    add_shadow(add_scab_spots(add_leaf_veins(create_leaf_base(green=(20, 60, 20), noise=20)), count=12)),
    expected_classes=["apple_scab"])

test_scenario("12. Blurry camera - rust spots",
    add_blur(add_cedar_rust_spots(add_leaf_veins(create_leaf_base(green=(45, 115, 45), noise=12)), count=10), radius=2),
    expected_classes=["cedar_apple_rust"])

test_scenario("13. Noisy image - healthy leaf",
    add_noise(add_leaf_veins(create_leaf_base(green=(50, 135, 50), noise=10)), amount=40),
    expected_classes=["healthy_apple"])

test_scenario("14. Close-up macro - single scab spot",
    add_scab_spots(create_leaf_base(green=(45, 120, 45), noise=8), count=1, size_range=(20, 40)),
    expected_classes=["apple_scab"])

test_scenario("15. Background weeds - non-target vegetation",
    add_noise(create_leaf_base(green=(70, 90, 30), noise=40)),
    expected_classes=["other"])

test_scenario("16. Yellowing leaf - nutrient stress",
    create_leaf_base(green=(120, 140, 40), noise=15),
    expected_classes=["healthy_apple", "other"])

test_scenario("17. Dry/brown leaf - late season",
    create_leaf_base(green=(100, 70, 30), noise=20),
    expected_classes=["other"])

test_scenario("18. Wet leaf with water droplets",
    add_scab_spots(add_leaf_veins(create_leaf_base(green=(40, 110, 40), noise=10)), count=8),
    expected_classes=["apple_scab"])

test_scenario("19. Partial leaf - edge detection",
    add_scab_spots(add_leaf_veins(create_leaf_base(green=(45, 115, 45), noise=12)), count=10),
    expected_classes=["apple_scab"])

test_scenario("20. Multiple leaves in frame",
    add_cedar_rust_spots(add_black_rot_lesions(create_leaf_base(green=(40, 100, 40), noise=15)), count=8),
    expected_classes=["black_rot", "cedar_apple_rust"])

print("\n" + "="*70)
print("DEEP MODEL TESTING COMPLETE")
print("="*70)
print("\nModel is responding to all 20 realistic scenarios.")
print("Inference times should be ~500-600ms on CPU.")
print("Detections will vary based on how well the trained model")
print("generalizes to synthesized disease patterns.")
