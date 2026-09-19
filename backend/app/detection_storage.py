"""순찰 중 감지된 인물 기록 저장소."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_DIR = Path(__file__).parent.parent / "data" / "face"
_FILE = _DIR / "detections.json"
IMAGE_DIR = _DIR / "detections"

MAX_RECORDS = 500  # 무한정 쌓이지 않게 오래된 기록부터 지운다


def _read() -> dict:
    if not _FILE.exists():
        return {"detections": [], "next_id": 1}
    return json.loads(_FILE.read_text(encoding="utf-8"))


def _write(data: dict) -> None:
    _DIR.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def image_path(detection_id: int) -> Path:
    return IMAGE_DIR / f"{detection_id}.jpg"


def get_for_place(place_id: int) -> list[dict]:
    """최신 기록이 먼저 오도록 정렬해 반환."""
    rows = [d for d in _read()["detections"] if d["place_id"] == place_id]
    return sorted(rows, key=lambda d: d["id"], reverse=True)


def add(place_id: int, zone_name: str, name: str | None, score: float,
        authorized: bool | None) -> dict:
    data = _read()
    record = {
        "id": data["next_id"],
        "place_id": place_id,
        "zone_name": zone_name,
        "name": name,
        "score": round(score, 3),
        "authorized": authorized,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
    data["detections"].append(record)
    data["next_id"] += 1

    # 보관 한도를 넘으면 오래된 기록과 사진을 함께 정리
    if len(data["detections"]) > MAX_RECORDS:
        for old in data["detections"][:-MAX_RECORDS]:
            image_path(old["id"]).unlink(missing_ok=True)
        data["detections"] = data["detections"][-MAX_RECORDS:]

    _write(data)
    return record


def remove(detection_id: int) -> bool:
    data = _read()
    remaining = [d for d in data["detections"] if d["id"] != detection_id]
    if len(remaining) == len(data["detections"]):
        return False
    data["detections"] = remaining
    _write(data)
    image_path(detection_id).unlink(missing_ok=True)
    return True


def clear_place(place_id: int) -> int:
    data = _read()
    removed = [d for d in data["detections"] if d["place_id"] == place_id]
    data["detections"] = [d for d in data["detections"] if d["place_id"] != place_id]
    _write(data)
    for d in removed:
        image_path(d["id"]).unlink(missing_ok=True)
    return len(removed)
