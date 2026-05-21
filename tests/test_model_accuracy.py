"""
Per-category model accuracy test with synthetic images
Generates 50+ images per class and reports per-class accuracy
"""
import requests
import numpy as np
from PIL import Image, ImageDraw
import io
import json
import time
from collections import defaultdict

API_URL = "http://localhost:8000/api/v1/detect/image"

def create_apple_leaf(w, h):
    """Create a green leaf-like background"""
    img = Image.new('RGB', (w, h), (34, 120, 50))
    draw = ImageDraw.Draw(img)
    for _ in range(200):
        x = np.random.randint(0, w)
        y = np.random.randint(0, h)
        g = np.random.randint(100, 180)
        img.putpixel((x, y), (np.random.randint(20, 60), g, np.random.randint(30, 70)))
    return img, draw

def add_noise(img, intensity=20):
    arr = np.array(img)
    noise = np.random.randint(-intensity, intensity, arr.shape)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def test_class(offset, label, count=15):
    results = []
    for i in range(count):
        w, h = np.random.randint(600, 1200), np.random.randint(400, 900)
        img, draw = create_apple_leaf(w, h)

        cx, cy = w // 2 + np.random.randint(-w//4, w//4), h // 2 + np.random.randint(-h//4, h//4)
        r = np.random.randint(30, 120)

        if label == "apple_scab":
            for _ in range(np.random.randint(3, 10)):
                x = cx + np.random.randint(-r, r)
                y = cy + np.random.randint(-r, r)
                s = np.random.randint(10, 30)
                draw.ellipse([x-s, y-s, x+s, y+s], fill=(40, 60, 30))
        elif label == "black_rot":
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(60, 40, 40))
            draw.ellipse([cx-r//2, cy-r//2, cx+r//2, cy+r//2], fill=(120, 100, 90))
        elif label == "cedar_apple_rust":
            for _ in range(np.random.randint(5, 15)):
                x = cx + np.random.randint(-r, r)
                y = cy + np.random.randint(-r, r)
                s = np.random.randint(8, 25)
                draw.ellipse([x-s, y-s, x+s, y+s], fill=(220, 150, 30))
        elif label == "powdery_mildew":
            for _ in range(np.random.randint(10, 30)):
                x = cx + np.random.randint(-r, r)
                y = cy + np.random.randint(-r, r)
                s = np.random.randint(5, 20)
                draw.ellipse([x-s, y-s, x+s, y+s], fill=(200, 210, 200))
        elif label == "healthy_apple":
            draw.ellipse([cx-r//2, cy-r//2, cx+r//2, cy+r//2], fill=(34, 130, 50))
        elif label == "other":
            for _ in range(np.random.randint(5, 20)):
                x = np.random.randint(0, w)
                y = np.random.randint(0, h)
                s = np.random.randint(5, 30)
                c = tuple(np.random.randint(80, 200, 3).tolist())
                draw.rectangle([x-s, y-s, x+s, y+s], fill=c)

        img = add_noise(img, np.random.randint(10, 30))

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=np.random.randint(70, 95))
        buf.seek(0)

        try:
            resp = requests.post(f"{API_URL}?conf=0.15", files={"file": ("test.jpg", buf, "image/jpeg")}, timeout=30)
            data = resp.json()
            detected = [d["class_name"] for d in data.get("detections", [])]
            top = detected[0] if detected else "none"
            matches = [d for d in detected if d == label]
            results.append({
                "label": label,
                "top": top,
                "matches": len(matches),
                "detected": len(detected),
                "conf": data["detections"][0]["confidence"] if data.get("detections") else 0
            })
        except Exception as e:
            results.append({"label": label, "error": str(e)})

        time.sleep(0.1)
    return results

print("=" * 70)
print("MODEL ACCURACY TEST - Per-Category Performance")
print("Generating 15+ new synthetic images per class (90+ total)")
print("=" * 70)

classes = ["apple_scab", "black_rot", "cedar_apple_rust", "powdery_mildew", "healthy_apple", "other"]
all_results = defaultdict(list)

for cls in classes:
    print(f"\n>>> Testing: {cls}")
    results = test_class(classes.index(cls), cls, count=15)
    all_results[cls] = results

    correct = sum(1 for r in results if r.get("matches", 0) > 0)
    total = sum(1 for r in results if "error" not in r)
    errors = sum(1 for r in results if "error" in r)
    avg_conf = np.mean([r["conf"] for r in results if r.get("conf", 0) > 0]) if any(r.get("conf", 0) > 0 for r in results) else 0

    print(f"  Accuracy: {correct}/{total} = {correct/total*100:.1f}%" if total > 0 else "  No valid results")
    print(f"  Errors: {errors}")
    if avg_conf > 0:
        print(f"  Avg Confidence: {avg_conf*100:.1f}%")

print("\n" + "=" * 70)
print("SUMMARY:")
print("=" * 70)
overall_correct = 0
overall_total = 0
for cls in classes:
    results = all_results[cls]
    correct = sum(1 for r in results if r.get("matches", 0) > 0)
    total = sum(1 for r in results if "error" not in r)
    overall_correct += correct
    overall_total += total
    pct = correct / total * 100 if total > 0 else 0
    print(f"  {cls}: {correct}/{total} = {pct:.1f}%")

pct = overall_correct / overall_total * 100 if overall_total > 0 else 0
print(f"\n  OVERALL: {overall_correct}/{overall_total} = {pct:.1f}%")
print("=" * 70)

with open("accuracy_results.json", "w") as f:
    json.dump(dict(all_results), f, indent=2)
print("\nResults saved to accuracy_results.json")
