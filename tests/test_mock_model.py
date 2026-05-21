"""
Test mock model detection output
"""
import asyncio
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.models.mock import MockModel
from app.config import settings

async def test_mock_model():
    model = MockModel()
    await model.load()

    test_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    detections = await model.predict(test_image)

    assert isinstance(detections, list), "Detections should be a list"

    for det in detections:
        assert det.class_id >= 0 and det.class_id < settings.NUM_CLASSES
        assert det.class_name in settings.CLASSES.values()
        assert 0 <= det.confidence <= 1
        assert len(det.bbox) == 4
        assert det.bbox[0] < det.bbox[2]
        assert det.bbox[1] < det.bbox[3]

    det_dict = detections[0].to_dict() if detections else {}
    if det_dict:
        assert "class_id" in det_dict
        assert "class_name" in det_dict
        assert "confidence" in det_dict
        assert "bbox" in det_dict

    info = model.get_info()
    assert info["type"] == "mock"
    assert info["status"] == "loaded"
    assert info["num_classes"] == settings.NUM_CLASSES

    print("Mock model tests passed")

async def test_empty_image():
    model = MockModel()
    await model.load()

    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    detections = await model.predict(test_image)
    assert isinstance(detections, list)
    print("Empty image test passed")

async def test_large_image():
    model = MockModel()
    await model.load()

    test_image = np.random.randint(0, 255, (1920, 1080, 3), dtype=np.uint8)
    detections = await model.predict(test_image)

    for det in detections:
        assert det.bbox[2] <= 1080
        assert det.bbox[3] <= 1920

    print("Large image test passed")

async def test_consistency():
    model = MockModel()
    await model.load()

    np.random.seed(42)
    test_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)

    results = []
    for _ in range(5):
        detections = await model.predict(test_image)
        results.append(len(detections))

    assert all(0 <= r <= 4 for r in results), "Detection count should be 0-4"
    print("Consistency test passed")

async def test_class_distribution():
    model = MockModel()
    await model.load()

    class_counts = {name: 0 for name in settings.CLASSES.values()}

    for _ in range(100):
        test_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        detections = await model.predict(test_image)
        for det in detections:
            class_counts[det.class_name] += 1

    total = sum(class_counts.values())
    assert total > 0, "Should have some detections across 100 runs"

    for name, count in class_counts.items():
        assert count >= 0, f"{name} should have non-negative count"

    print(f"Class distribution test passed - total detections: {total}")
    print(f"Distribution: {class_counts}")

async def main():
    print("Running mock model tests...\n")
    await test_mock_model()
    await test_empty_image()
    await test_large_image()
    await test_consistency()
    await test_class_distribution()
    print("\nAll mock model tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
