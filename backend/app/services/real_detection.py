"""YOLO 인원 감지."""
from __future__ import annotations

from pathlib import Path

_MODELS_DIR = Path(__file__).parent.parent.parent.parent.parent / "person-count" / "backend" / "models"
_CONF_THRESH = 0.60

_yolo_cache: dict[str, object] = {}


def _get_yolo(model_name: str = "yolo26x"):
    if model_name not in _yolo_cache:
        from ultralytics import YOLO
        path = _MODELS_DIR / f"{model_name}.pt"
        if not path.exists():
            print(f"[real_detection] {model_name}.pt 없음 → 자동 다운로드...")
            _MODELS_DIR.mkdir(parents=True, exist_ok=True)
            tmp = YOLO(f"{model_name}.pt")
            tmp.save(str(path))
        _yolo_cache[model_name] = YOLO(str(path))
    return _yolo_cache[model_name]
