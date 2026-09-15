import base64
import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from app.models import Classroom, ClassroomCreate, ClassroomUpdate, PromptConfig

DATA_FILE = Path(__file__).parent.parent / "data" / "classrooms.json"
PROMPT_FILE = Path(__file__).parent.parent / "data" / "prompts.json"
MAP_DIR = Path(__file__).parent.parent / "data" / "maps"
MAP_DATA_DIR = Path(__file__).parent.parent / "data" / "map_data"
OCCUPANCY_DIR = Path(__file__).parent.parent / "data" / "occupancy"
OCCUPANCY_RETENTION_DAYS = 30
OCCUPANCY_RESET_MARKER_FILE = OCCUPANCY_DIR / "_reset_marker.json"


def _load() -> dict:
    DATA_FILE.parent.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps({"classrooms": [], "next_id": 1}))
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def _save(data: dict):
    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_all() -> List[Classroom]:
    return [Classroom(**c) for c in _load()["classrooms"]]


def get_one(classroom_id: int) -> Optional[Classroom]:
    for c in _load()["classrooms"]:
        if c["id"] == classroom_id:
            return Classroom(**c)
    return None


def create(payload: ClassroomCreate) -> Classroom:
    data = _load()
    now = datetime.now().isoformat()
    classroom = Classroom(
        id=data["next_id"],
        name=payload.name,
        created_at=now,
        updated_at=now,
    )
    data["classrooms"].append(classroom.model_dump())
    data["next_id"] += 1
    _save(data)
    return classroom


def update(classroom_id: int, payload: ClassroomUpdate) -> Optional[Classroom]:
    data = _load()
    for i, c in enumerate(data["classrooms"]):
        if c["id"] == classroom_id:
            merged = {**c, **payload.model_dump(exclude_none=True)}
            merged["updated_at"] = datetime.now().isoformat()
            data["classrooms"][i] = merged
            _save(data)
            _prune_stale_grabbers(data["classrooms"])
            return Classroom(**merged)
    return None


def delete(classroom_id: int) -> bool:
    data = _load()
    before = len(data["classrooms"])
    data["classrooms"] = [c for c in data["classrooms"] if c["id"] != classroom_id]
    if len(data["classrooms"]) < before:
        _save(data)
        _prune_stale_grabbers(data["classrooms"])
        return True
    return False


def _prune_stale_grabbers(classrooms_raw: list) -> None:
    """더 이상 어떤 카메라도 참조하지 않는 RTSP grabber 스레드를 정리한다."""
    active_urls = {
        cam["rtsp_url"]
        for c in classrooms_raw
        for cam in c.get("cameras", [])
        if cam.get("rtsp_url")
    }
    from app.services.frame_capture import prune_grabbers
    prune_grabbers(active_urls)


# ── 프롬프트 설정 ─────────────────────────────────────────────────────────────

def _load_prompts() -> dict:
    PROMPT_FILE.parent.mkdir(exist_ok=True)
    if not PROMPT_FILE.exists():
        default = {"system_prompt": "", "default_user_prompt": ""}
        PROMPT_FILE.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
    return json.loads(PROMPT_FILE.read_text(encoding="utf-8"))


def _save_prompts(data: dict):
    PROMPT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_prompt_config() -> PromptConfig:
    return PromptConfig(**_load_prompts())


def save_map_image(classroom_id: int, b64_png: str) -> None:
    MAP_DIR.mkdir(exist_ok=True)
    (MAP_DIR / f"{classroom_id}.png").write_bytes(base64.b64decode(b64_png))


def get_map_image_b64(classroom_id: int) -> Optional[str]:
    p = MAP_DIR / f"{classroom_id}.png"
    if p.exists():
        return base64.b64encode(p.read_bytes()).decode()
    return None


def save_map_data(classroom_id: int, data: dict) -> None:
    MAP_DATA_DIR.mkdir(exist_ok=True)
    (MAP_DATA_DIR / f"{classroom_id}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_map_data(classroom_id: int) -> Optional[dict]:
    p = MAP_DATA_DIR / f"{classroom_id}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def update_prompt_config(
    system_prompt: Optional[str] = None,
    default_user_prompt: Optional[str] = None,
) -> PromptConfig:
    data = _load_prompts()
    if system_prompt is not None:
        data["system_prompt"] = system_prompt
    if default_user_prompt is not None:
        data["default_user_prompt"] = default_user_prompt
    _save_prompts(data)
    return PromptConfig(**data)


# ── 좌석 점유 모니터링 (10분 주기 스냅샷) ──────────────────────────────────────

def _occupancy_file(classroom_id: int) -> Path:
    return OCCUPANCY_DIR / f"{classroom_id}.json"


def append_occupancy_snapshot(classroom_id: int, snapshot: dict) -> None:
    """스냅샷 {"ts": iso문자열, "seats": {seat_id: "occupied"|"empty"}} 저장. 보관 기간 지난 항목은 정리.

    로컬 프로세스와 Docker 컨테이너처럼 인스턴스가 여러 개 동시에 돌아가는 경우, 같은 주기(interval) 안에
    중복 저장되는 것을 막기 위해 UTC 기준 interval 버킷이 마지막 기록과 같으면 건너뛴다. 각 프로세스가
    서로 다른 로컬 타임존을 쓰더라도(예: 컨테이너는 UTC, 호스트는 KST) 절대시각으로 비교하므로 안전하다.
    """
    OCCUPANCY_DIR.mkdir(exist_ok=True)
    p = _occupancy_file(classroom_id)
    data = {"snapshots": []}
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            data = {"snapshots": []}

    interval_seconds = int(os.getenv("OCCUPANCY_MONITOR_INTERVAL", "600"))
    bucket = int(datetime.now(timezone.utc).timestamp() // interval_seconds)
    if data["snapshots"] and data["snapshots"][-1].get("bucket") == bucket:
        return
    data["snapshots"].append({**snapshot, "bucket": bucket})

    cutoff = (datetime.now() - timedelta(days=OCCUPANCY_RETENTION_DAYS)).isoformat()
    data["snapshots"] = [s for s in data["snapshots"] if s.get("ts", "") >= cutoff]
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_occupancy_history(classroom_id: int, since: Optional[str] = None, until: Optional[str] = None) -> List[dict]:
    p = _occupancy_file(classroom_id)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    snapshots = data.get("snapshots", [])
    if since:
        snapshots = [s for s in snapshots if s.get("ts", "") >= since]
    if until:
        snapshots = [s for s in snapshots if s.get("ts", "") < until]
    return snapshots


def _current_week_monday() -> str:
    now = datetime.now()
    monday = now - timedelta(days=now.weekday())  # weekday(): 월=0
    return monday.strftime("%Y-%m-%d")


def clear_all_occupancy_now() -> None:
    """모든 교실의 점유 모니터링 기록을 즉시 비운다 (수동 초기화). 주간 리셋 마커는 건드리지 않는다."""
    OCCUPANCY_DIR.mkdir(exist_ok=True)
    for classroom in get_all():
        _occupancy_file(classroom.id).write_text(
            json.dumps({"snapshots": []}, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def clear_occupancy_if_new_week() -> bool:
    """월요일 00시 기준 새 주가 시작되면 모든 교실의 점유 모니터링 기록을 삭제한다.

    마지막으로 초기화한 주(월요일 날짜)를 마커 파일에 저장해두고, 현재 주와 다르면
    한 번만 초기화한다. 서버가 꺼져있다 켜져도 다음 틱에서 안전하게 처리된다.
    삭제를 수행했으면 True.
    """
    OCCUPANCY_DIR.mkdir(exist_ok=True)
    current_monday = _current_week_monday()

    last = None
    if OCCUPANCY_RESET_MARKER_FILE.exists():
        try:
            last = json.loads(OCCUPANCY_RESET_MARKER_FILE.read_text(encoding="utf-8")).get("last_cleared_monday")
        except Exception:
            last = None

    if last == current_monday:
        return False

    for classroom in get_all():
        _occupancy_file(classroom.id).write_text(
            json.dumps({"snapshots": []}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    OCCUPANCY_RESET_MARKER_FILE.write_text(
        json.dumps({"last_cleared_monday": current_monday}, ensure_ascii=False), encoding="utf-8"
    )
    return True
