"""순찰 1회분의 자리별 인식 결과 스냅샷.

좌석 점유(data/occupancy/*.json)와 같은 모양으로 남겨서 두 기능을 같은 축에서 비교할 수
있게 한다. 자리 이름이 "30번 자리"면 키는 "30"이 된다.

자리 값:
  null                                         아무도 없음
  {"verified": true,  "name": "김민석", ...}    등록·허가된 사람
  {"verified": false, "name": null, ...}        미등록 인물
  {"verified": false, "name": "홍길동", ...}    등록됐지만 허가되지 않은 사람
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

_DIR = Path(__file__).parent.parent / "data" / "face"
MAX_SNAPSHOTS = 500


def _file(place_id: int) -> Path:
    return _DIR / f"seat_log_{place_id}.json"


def seat_key(roi_name: str) -> str:
    """'30번 자리' -> '30'. 숫자가 없으면 이름을 그대로 쓴다."""
    m = re.search(r"\d+", roi_name)
    return m.group() if m else roi_name


def append_snapshot(place_id: int, seats: dict) -> dict:
    path = _file(place_id)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"snapshots": []}

    snapshot = {"ts": datetime.now().isoformat(timespec="seconds"), "seats": seats}
    data["snapshots"].append(snapshot)
    data["snapshots"] = data["snapshots"][-MAX_SNAPSHOTS:]

    _DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return snapshot


def get_snapshots(place_id: int, limit: int = 50) -> list[dict]:
    """최신순으로 반환."""
    path = _file(place_id)
    if not path.exists():
        return []
    snapshots = json.loads(path.read_text(encoding="utf-8"))["snapshots"]
    return list(reversed(snapshots[-limit:]))
