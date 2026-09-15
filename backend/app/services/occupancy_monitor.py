"""좌석 점유 모니터링: 주기적으로 YOLO Pose로 좌석 점유 스냅샷을 저장한다.

LLM 호출 없이 vision_llm_detection._run_seat_occupancy(Pose 모델 기반)만 사용해
비용 없이 반복 실행할 수 있도록 한다.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from app import storage
from app.models import Classroom

HOURLY_START_HOUR = 9
HOURLY_END_HOUR = 21
WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def collect_snapshot(classroom: Classroom) -> dict | None:
    """교실의 카메라들을 모두 캡처해 좌석 상태를 합치고 스냅샷으로 저장한다."""
    cameras_with_seats = [c for c in classroom.cameras if c.rtsp_url and c.seat_lines]
    if not cameras_with_seats:
        return None

    from app.services.frame_capture import capture_rtsp_frames_parallel
    from app.services.vision_llm_detection import _run_seat_occupancy

    seats: dict[str, str] = {}
    for camera, frame in capture_rtsp_frames_parallel(cameras_with_seats):
        if frame is None:
            continue
        try:
            r = _run_seat_occupancy(
                frame, camera,
                yolo_model=classroom.yolo_model or "yolov8x",
                conf_threshold=classroom.conf_threshold,
            )
        except Exception as e:
            print(f"[occupancy_monitor] {classroom.name}/{camera.name} 감지 오류: {e}")
            continue
        for sid in r.get("occupied", []):
            seats[sid] = "occupied"
        for sid in r.get("empty", []):
            seats.setdefault(sid, "empty")

    if not seats:
        return None

    snapshot = {"ts": datetime.now().isoformat(timespec="seconds"), "seats": seats}
    storage.append_occupancy_snapshot(classroom.id, snapshot)
    print(f"[occupancy_monitor] {classroom.name}: {len(seats)}석 스냅샷 저장")
    return snapshot


def collect_all() -> None:
    for classroom in storage.get_all():
        try:
            collect_snapshot(classroom)
        except Exception as e:
            print(f"[occupancy_monitor] {classroom.name} 스냅샷 오류: {e}")


def compute_seat_stats(classroom_id: int, since_iso: str, until_iso: str | None = None) -> dict[str, dict]:
    """[since_iso, until_iso) 구간의 스냅샷을 좌석별로 집계.

    반환: {seat_id: {occupied, empty, total, occupied_pct, occupied_minutes}}
    """
    interval_min = int(os.getenv("OCCUPANCY_MONITOR_INTERVAL", "600")) / 60
    snapshots = storage.get_occupancy_history(classroom_id, since=since_iso, until=until_iso)

    stats: dict[str, dict] = {}
    for snap in snapshots:
        for sid, state in snap.get("seats", {}).items():
            s = stats.setdefault(sid, {"occupied": 0, "empty": 0, "total": 0})
            s["total"] += 1
            if state in ("occupied", "empty"):
                s[state] += 1

    for s in stats.values():
        s["occupied_pct"] = round(s["occupied"] / s["total"] * 100) if s["total"] else 0
        s["occupied_minutes"] = round(s["occupied"] * interval_min)

    return stats


def compute_hourly_occupancy(classroom_id: int, date_str: str, schedule: dict | None = None) -> list[dict]:
    """지정 날짜의 09시~21시 정각 스냅샷만 뽑아 시간별 점유 좌석 수를 반환.

    카메라는 10분마다 촬영하지만, 여기서는 각 정각(예: 09:00, 10:00, ...)에 가장 가까운
    스냅샷(정각~정각+9분 사이) 하나만 사용한다. 아직 지나지 않은 시각이거나 그 시간대에
    기록이 없으면 occupied/total은 null.

    schedule이 주어지면 해당 요일에 수업으로 등록된 시간(scheduled=True)만 점유 데이터를
    채우고, 나머지는 수업이 없는 시간으로 표시한다(scheduled=False). schedule이 없으면
    (아직 시간표를 설정하지 않은 교실) 09~21시 전체를 수업 시간으로 간주한다.
    """
    day = datetime.strptime(date_str, "%Y-%m-%d")
    since = day.isoformat(timespec="seconds")
    until = (day + timedelta(days=1)).isoformat(timespec="seconds")
    snapshots = storage.get_occupancy_history(classroom_id, since=since, until=until)
    now = datetime.now()

    day_key = WEEKDAY_KEYS[day.weekday()]
    scheduled_hours = set(schedule.get(day_key, [])) if schedule else None

    result = []
    for hour in range(HOURLY_START_HOUR, HOURLY_END_HOUR + 1):
        is_scheduled = True if scheduled_hours is None else (hour in scheduled_hours)
        mark = day.replace(hour=hour, minute=0, second=0, microsecond=0)
        entry = {
            "hour": hour, "time": f"{hour:02d}:00", "scheduled": is_scheduled,
            "occupied": None, "total": None, "seats": None,
        }
        if is_scheduled and mark <= now:
            window_end_iso = (mark + timedelta(minutes=9, seconds=59)).isoformat(timespec="seconds")
            mark_iso = mark.isoformat(timespec="seconds")
            snap = next((s for s in snapshots if mark_iso <= s.get("ts", "") < window_end_iso), None)
            if snap:
                seats = snap.get("seats", {})
                occupied_seats = [sid for sid, v in seats.items() if v == "occupied"]
                occupied_seats.sort(key=lambda sid: (not sid.isdigit(), int(sid) if sid.isdigit() else 0, sid))
                entry["occupied"] = len(occupied_seats)
                entry["total"] = len(seats)
                entry["seats"] = occupied_seats
        result.append(entry)

    return result
