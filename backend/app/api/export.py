"""
Export API Endpoints - CSV and JSON export of detection history
"""
import json
import csv
import io
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.inference.engine import detection_engine
from app.logging_config import get_logger

logger = get_logger("api.export")

router = APIRouter()

@router.get("/json")
async def export_json(limit: int = Query(default=1000, ge=1, le=10000)):
    history = detection_engine.get_history()[-limit:]
    data = json.dumps(history, indent=2, default=str)
    filename = f"detections_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    return StreamingResponse(
        io.StringIO(data),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/csv")
async def export_csv(limit: int = Query(default=1000, ge=1, le=10000)):
    history = detection_engine.get_history()[-limit:]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "class_id", "class_name", "confidence", "xmin", "ymin", "xmax", "ymax", "inference_time_ms", "image_width", "image_height"])

    for record in history:
        ts = record.get("timestamp", "")
        inf_time = record.get("inference_time_ms", 0)
        img_size = record.get("image_size", [0, 0])
        for det in record.get("detections", []):
            writer.writerow([
                ts,
                det.get("class_id", ""),
                det.get("class_name", ""),
                det.get("confidence", ""),
                det.get("bbox", {}).get("xmin", ""),
                det.get("bbox", {}).get("ymin", ""),
                det.get("bbox", {}).get("xmax", ""),
                det.get("bbox", {}).get("ymax", ""),
                inf_time,
                img_size[1] if len(img_size) > 1 else 0,
                img_size[0] if len(img_size) > 0 else 0
            ])

    output.seek(0)
    filename = f"detections_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
