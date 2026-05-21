# Apple Disease Detector - Production

Production-grade automated apple disease detection pipeline using a trained YOLOv8 ONNX model for precision agriculture. Built for real-time field deployment with future NVIDIA Jetson integration for targeted pesticide spraying.

## Model

- **Architecture**: YOLOv8m (trained)
- **Format**: ONNX (98.8 MB)
- **Input**: 640x640 RGB images
- **Output**: 6 classes, 8400 anchors
- **Inference**: ~500-600ms on CPU
- **Classes**: apple_scab, black_rot, cedar_apple_rust, powdery_mildew, healthy_apple, other

## Features

- Real-time disease detection from images and live camera feed
- Trained YOLOv8m ONNX model (98.8 MB, 6 classes)
- Adjustable confidence threshold via API query parameter (`?conf=0.25`)
- Optional annotated image output (`?include_annotated=false` to save bandwidth)
- Multilingual interface (English + Hindi)
- Export detection history as CSV or JSON with summary
- PWA support for mobile installation (iOS/Android)
- Responsive mobile-first design with touch-optimized UI
- Image preview before detection
- Detection count badge and inference time display
- Confidence threshold slider in UI
- Rate limiting and request validation
- Structured logging and health checks
- Docker deployment with one-command setup
- Hardware plugin interface for Jetson Nano integration

## Quick Start

### Docker (Recommended)

```bash
# Clone and deploy
git clone <repo-url>
cd apple-disease-detector
cp backend/.env.example .env
./deploy/deploy.sh  # Linux/macOS
# OR
powershell -ExecutionPolicy Bypass -File deploy/deploy.ps1  # Windows
```

Access:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs

### Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Detected Diseases

| Class | Scientific Name | Symptoms |
|-------|----------------|----------|
| Apple Scab | Venturia inaequalis | Dark olive-green to black velvety spots |
| Black Rot | Botryosphaeria obtusa | Purple-ringed lesions, frog-eye patterns |
| Cedar Apple Rust | Gymnosporangium juniperivirginianae | Bright orange/yellow spots |
| Powdery Mildew | Podosphaera leucotricha | White-to-gray powdery fungal coating |
| Healthy Apple | - | Clean, unblemished foliage |
| Other | - | Background, weeds, non-target vegetation |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/health | Health check with model status |
| GET | /api/v1/ready | Readiness probe |
| GET | /api/v1/live | Liveness probe |
| GET | /api/v1/model/info | Model metadata |
| POST | /api/v1/detect/image | Upload image for detection (`?conf=0.25&include_annotated=true`) |
| POST | /api/v1/detect/image/raw | Upload image, JSON only (`?conf=0.25`) |
| POST | /api/v1/detect/stream/frame | Process video frame |
| GET | /api/v1/detect/history | Get detection history (`?limit=50`) |
| POST | /api/v1/detect/history/clear | Clear history |
| GET | /api/v1/export/json | Export as JSON (`?limit=1000`) |
| GET | /api/v1/export/csv | Export as CSV (`?limit=1000`) |

### Query Parameters

- `conf` (float, 0.0-1.0): Override confidence threshold for detection (default: 0.25)
- `include_annotated` (bool): Include base64 annotated image in response (default: true)
- `limit` (int): Number of history records to return (default: 50, max: 500)

## Configuration

All settings via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| MODEL_TYPE | mock | Model backend (mock/onnx) |
| MODEL_PATH | - | Path to ONNX model file |
| DEVICE | cpu | Compute device (cpu/cuda) |
| CONF_THRESHOLD | 0.25 | Minimum confidence |
| IOU_THRESHOLD | 0.45 | NMS IoU threshold |
| IMG_SIZE | 640 | Input image size |
| MAX_FILE_SIZE_MB | 16 | Max upload size |
| RATE_LIMIT_PER_MINUTE | 60 | API rate limit |
| LOG_LEVEL | INFO | Logging level |
| CORS_ORIGINS | * | Allowed origins |

## Model Configuration

The production ONNX model (`best.onnx`) is included at `backend/app/models/weights/model.onnx`.

To use a different model:
1. Replace `backend/app/models/weights/model.onnx` with your trained `.onnx` file
2. Ensure it has the same input/output format: `[1, 3, 640, 640]` → `[1, 10, 8400]`
3. Restart the backend

## Mobile Support

The frontend is a Progressive Web App (PWA):
- Install on iOS: Share -> Add to Home Screen
- Install on Android: Menu -> Install App
- Works offline after first load
- Camera access requires HTTPS in production

## Project Structure

```
apple-disease-detector/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── config.py               # Environment-based config
│   │   ├── logging_config.py       # Structured logging
│   │   ├── models/
│   │   │   ├── base.py             # Abstract model interface
│   │   │   ├── mock.py             # Mock model for testing
│   │   │   └── onnx_model.py       # ONNX production model
│   │   ├── inference/
│   │   │   └── engine.py           # Core detection engine
│   │   ├── api/
│   │   │   ├── detect.py           # Detection endpoints
│   │   │   ├── export.py           # Export endpoints
│   │   │   └── status.py           # Health/status endpoints
│   │   ├── middleware/
│   │   │   ├── rate_limit.py       # Rate limiting
│   │   │   └── request.py          # Request logging
│   │   ├── plugins/
│   │   │   └── hardware.py         # Jetson hardware plugin
│   │   ├── schemas/                # Pydantic validation
│   │   └── utils/
│   │       ├── annotations.py      # Image utilities
│   │       └── i18n.py             # Multilingual mappings
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/             # React components
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── services/               # API client
│   │   ├── utils/                  # Helper functions
│   │   ├── i18n/                   # Translations
│   │   └── styles/                 # Theme CSS
│   ├── public/
│   │   └── manifest.json           # PWA manifest
│   ├── package.json
│   ├── vite.config.js              # Vite + PWA config
│   ├── nginx.conf                  # Production nginx
│   └── Dockerfile
├── tests/
├── deploy/
│   ├── deploy.sh                   # Linux/macOS deploy
│   └── deploy.ps1                  # Windows deploy
├── .github/workflows/ci.yml        # CI/CD pipeline
├── docker-compose.yml
└── README.md
```

## Testing

```bash
# Integrated ONNX model tests (35 tests)
python tests/test_integrated_model.py

# Production API tests (24 tests)
python tests/test_production.py

# Real-world scenario tests (8 tests)
python tests/test_real_world_scenarios.py

# Deep model testing with realistic disease patterns (20 scenarios)
python tests/test_deep_model.py

# Total: 87 tests
```

## Hardware Integration

The `HardwarePlugin` interface in `backend/app/plugins/hardware.py` provides the abstraction for Jetson Nano integration:

```python
class HardwarePlugin(ABC):
    async def initialize(self) -> bool: ...
    async def process_detections(self, detections, frame) -> dict: ...
    async def shutdown(self) -> None: ...
    def get_status(self) -> dict: ...
```

Implement this interface for your specific hardware setup.

## License

MIT
