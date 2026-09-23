"""등록된 인물 정보 저장소.

얼굴 임베딩 자체는 face_db(embeddings.npz)가 이름을 키로 갖고 있고, 여기서는
허가 여부·등록 시각·썸네일 같은 부가 정보를 관리한다.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_DIR = Path(__file__).parent.parent / "data" / "face"
_FILE = _DIR / "people.json"
PHOTO_DIR = _DIR / "photos"


def _classroom_ids(person: dict) -> list[int]:
    ids = person.get("classroom_ids")
    if isinstance(ids, list):
        return [int(i) for i in ids if i is not None]
    legacy_id = person.get("classroom_id")
    return [int(legacy_id)] if legacy_id is not None else []


def _read() -> dict:
    if not _FILE.exists():
        return {"people": [], "next_id": 1}
    return json.loads(_FILE.read_text(encoding="utf-8-sig"))


def _write(data: dict) -> None:
    _DIR.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_all(classroom_id: int | None = None) -> list[dict]:
    people = _read()["people"]
    if classroom_id is None:
        return people
    return [p for p in people if classroom_id in _classroom_ids(p)]


def get_by_name(name: str) -> dict | None:
    return next((p for p in _read()["people"] if p["name"] == name), None)


def get_one(person_id: int) -> dict | None:
    return next((p for p in _read()["people"] if p["id"] == person_id), None)


def photo_path(person_id: int) -> Path:
    """이름을 파일명에 쓰면 경로 주입 위험이 있어 id로만 만든다."""
    return PHOTO_DIR / f"{person_id}.jpg"


def upsert(name: str, samples: int, authorized: bool | None = None, classroom_ids: list[int] | None = None) -> dict:
    """같은 이름이 있으면 갱신(재등록), 없으면 추가."""
    data = _read()
    classroom_ids = sorted(set(classroom_ids or []))
    for person in data["people"]:
        if person["name"] == name:
            person["samples"] = samples
            person.pop("classroom_id", None)
            person["classroom_ids"] = classroom_ids
            person["enrolled_at"] = datetime.now().isoformat(timespec="seconds")
            if authorized is not None:
                person["authorized"] = authorized
            _write(data)
            return person

    person = {
        "id": data["next_id"],
        "name": name,
        "classroom_ids": classroom_ids,
        "authorized": True if authorized is None else authorized,
        "samples": samples,
        "enrolled_at": datetime.now().isoformat(timespec="seconds"),
    }
    data["people"].append(person)
    data["next_id"] += 1
    _write(data)
    return person


def set_authorized(person_id: int, authorized: bool) -> dict | None:
    data = _read()
    for person in data["people"]:
        if person["id"] == person_id:
            person["authorized"] = authorized
            _write(data)
            return person
    return None


def remove(person_id: int) -> dict | None:
    data = _read()
    person = next((p for p in data["people"] if p["id"] == person_id), None)
    if not person:
        return None
    data["people"] = [p for p in data["people"] if p["id"] != person_id]
    _write(data)
    photo_path(person_id).unlink(missing_ok=True)
    return person
