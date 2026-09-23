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
import os
import re
import threading
from datetime import datetime
from pathlib import Path

_DIR = Path(__file__).parent.parent / "data" / "face"
MAX_SNAPSHOTS = 500

# 순찰은 구역마다 파일 전체를 다시 쓴다. 한 프로세스 안에서 두 순찰이 겹쳐 읽고-고쳐-쓰지 않도록 묶는다.
_write_lock = threading.Lock()


def _file(place_id: int) -> Path:
    return _DIR / f"seat_log_{place_id}.json"


def seat_key(roi_name: str) -> str:
    """'30번 자리' -> '30'. 숫자가 없으면 이름을 그대로 쓴다."""
    m = re.search(r"\d+", roi_name)
    return m.group() if m else roi_name


def _write_atomic(path: Path, text: str) -> None:
    """같은 폴더에 임시 파일로 먼저 쓴 뒤 교체한다.

    파일을 곧바로 덮어쓰면 쓰는 도중에 프로세스가 끊길 때 JSON이 반만 남아 깨진다
    (한 번 깨지면 이 파일을 읽는 순찰과 모니터링 화면이 모두 멈춘다).
    줄바꿈이 운영체제마다 달라지지 않도록 바이트로 쓴다.
    """
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as f:
        f.write(text.encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def append_snapshot(place_id: int, seats: dict) -> dict:
    path = _file(place_id)
    snapshot = {"ts": datetime.now().isoformat(timespec="seconds"), "seats": seats}

    with _write_lock:
        data = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {"snapshots": []}
        data["snapshots"].append(snapshot)
        data["snapshots"] = data["snapshots"][-MAX_SNAPSHOTS:]

        _DIR.mkdir(parents=True, exist_ok=True)
        _write_atomic(path, json.dumps(data, ensure_ascii=False, indent=2))
    return snapshot


def get_snapshots(place_id: int, limit: int = 50) -> list[dict]:
    """최신순으로 반환."""
    path = _file(place_id)
    if not path.exists():
        return []
    snapshots = json.loads(path.read_text(encoding="utf-8-sig"))["snapshots"]
    return list(reversed(snapshots[-limit:]))
