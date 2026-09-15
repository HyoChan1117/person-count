"""YOLO 인원 감지."""
from __future__ import annotations

import threading
from pathlib import Path

_MODELS_DIR = Path(__file__).parent.parent.parent / "models"
_CONF_THRESH = 0.60

_yolo_cache: dict[str, object] = {}

# 실시간 스트리밍 워커와 온디맨드 분석(좌석 점유, YOLO+LLM)이 같은 모델 이름을 쓰면
# _yolo_cache의 동일 인스턴스를 공유한다. ultralytics YOLO 모델은 predict() 호출마다
# 내부 predictor 상태를 재사용하므로 여러 스레드가 동시에 predict()를 호출하면
# 서로의 conf/classes 등 설정을 덮어써 결과가 뒤섞일 수 있다 — 이 락으로 모든
# 추론 호출을 프로세스 전체에서 직렬화해 방지한다.
infer_lock = threading.Lock()


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
