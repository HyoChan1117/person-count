import base64
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from app.models import Classroom, ClassroomCreate, ClassroomUpdate, PromptConfig

DATA_FILE = Path(__file__).parent.parent / "data" / "classrooms.json"
PROMPT_FILE = Path(__file__).parent.parent / "data" / "prompts.json"
MAP_DIR = Path(__file__).parent.parent / "data" / "maps"
MAP_DATA_DIR = Path(__file__).parent.parent / "data" / "map_data"


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
            return Classroom(**merged)
    return None


def delete(classroom_id: int) -> bool:
    data = _load()
    before = len(data["classrooms"])
    data["classrooms"] = [c for c in data["classrooms"] if c["id"] != classroom_id]
    if len(data["classrooms"]) < before:
        _save(data)
        return True
    return False


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
