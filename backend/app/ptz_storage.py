"""얼굴 인식 감시 장소 저장소.

장소 하나당 PTZ 카메라 1대와 순찰 구역 목록을 갖는다. 교실(classrooms.json)과는
완전히 분리된 파일을 쓴다 — 좌석 점유와 얼굴 인식은 별개 기능이기 때문이다.
"""
from __future__ import annotations

import json
from pathlib import Path

_FILE = Path(__file__).parent.parent / "data" / "face_places.json"


def _read() -> dict:
    if not _FILE.exists():
        return {"places": [], "next_id": 1}
    return json.loads(_FILE.read_text(encoding="utf-8"))


def _write(data: dict) -> None:
    _FILE.parent.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 장소 ─────────────────────────────────────────────────────────────────────

def get_all() -> list[dict]:
    return _read()["places"]


def get_one(place_id: int) -> dict | None:
    return next((p for p in _read()["places"] if p["id"] == place_id), None)


def create(name: str, camera: dict, classroom_id: int | None = None) -> dict:
    data = _read()
    place = {
        "id": data["next_id"],
        "name": name,
        # 좌석 확인에 등록된 교실과 연결한 경우 그 교실 id. 직접 입력한 장소는 None.
        "classroom_id": classroom_id,
        "camera": camera,
        "zones": [],
        "next_zone_id": 1,
    }
    data["places"].append(place)
    data["next_id"] += 1
    _write(data)
    return place


def update(place_id: int, name: str | None = None, camera: dict | None = None,
           classroom_id: int | None = None, clear_classroom: bool = False) -> dict | None:
    data = _read()
    for place in data["places"]:
        if place["id"] == place_id:
            if name is not None:
                place["name"] = name
            if camera is not None:
                place["camera"] = camera
            if clear_classroom:
                place["classroom_id"] = None
            elif classroom_id is not None:
                place["classroom_id"] = classroom_id
            _write(data)
            return place
    return None


def remove(place_id: int) -> bool:
    data = _read()
    remaining = [p for p in data["places"] if p["id"] != place_id]
    if len(remaining) == len(data["places"]):
        return False
    data["places"] = remaining
    _write(data)
    return True


# ── 순찰 구역 ────────────────────────────────────────────────────────────────

def add_zone(place_id: int, name: str, pan: int, tilt: int, zoom: int) -> dict | None:
    data = _read()
    for place in data["places"]:
        if place["id"] == place_id:
            zone = {
                "id": place["next_zone_id"],
                "name": name,
                "pan": pan,
                "tilt": tilt,
                "zoom": zoom,
            }
            place["zones"].append(zone)
            place["next_zone_id"] += 1
            _write(data)
            return zone
    return None


def get_zone(place_id: int, zone_id: int) -> dict | None:
    place = get_one(place_id)
    if not place:
        return None
    return next((z for z in place["zones"] if z["id"] == zone_id), None)


def reorder_zones(place_id: int, zone_ids: list[int]) -> list[dict] | None:
    """순찰 순서를 zone_ids 순으로 바꾼다. 목록이 정확히 일치하지 않으면 거부한다."""
    data = _read()
    for place in data["places"]:
        if place["id"] != place_id:
            continue
        by_id = {z["id"]: z for z in place["zones"]}
        if set(zone_ids) != set(by_id):
            return None   # 빠지거나 없는 구역이 섞이면 순서를 건드리지 않는다
        place["zones"] = [by_id[zid] for zid in zone_ids]
        _write(data)
        return place["zones"]
    return None


def set_zone_rois(place_id: int, zone_id: int, rois: list[dict]) -> dict | None:
    """구역 안의 관심 영역(자리)을 통째로 교체한다.

    좌표는 그 구역에서 촬영한 화면 기준의 비율값(0~1)이다. 미리보기(1280)와 순찰 촬영
    (2560)의 해상도가 달라 절대 픽셀로 두면 어긋나기 때문이다.
    """
    data = _read()
    for place in data["places"]:
        if place["id"] != place_id:
            continue
        for zone in place["zones"]:
            if zone["id"] == zone_id:
                zone["rois"] = rois
                _write(data)
                return zone
    return None


def remove_zone(place_id: int, zone_id: int) -> bool:
    data = _read()
    for place in data["places"]:
        if place["id"] == place_id:
            remaining = [z for z in place["zones"] if z["id"] != zone_id]
            if len(remaining) == len(place["zones"]):
                return False
            place["zones"] = remaining
            _write(data)
            return True
    return False
