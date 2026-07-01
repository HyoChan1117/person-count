"""Slack 슬래시 커맨드 (/좌석, /좌석상세) 핸들러."""
import hashlib
import hmac
import json
import os
import time
import urllib.request
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from app import storage

router = APIRouter()

# 렌더링된 배치도 이미지를 임시 보관 (최대 50개)
_SNAPSHOTS: dict[str, bytes] = {}
_SNAPSHOT_ORDER: list[str] = []
_MAX_SNAPSHOTS = 50


def _store_snapshot(png_bytes: bytes) -> str:
    snap_id = str(uuid.uuid4())
    _SNAPSHOTS[snap_id] = png_bytes
    _SNAPSHOT_ORDER.append(snap_id)
    if len(_SNAPSHOT_ORDER) > _MAX_SNAPSHOTS:
        old = _SNAPSHOT_ORDER.pop(0)
        _SNAPSHOTS.pop(old, None)
    return snap_id


@router.get("/snapshot/{snap_id}")
def get_snapshot(snap_id: str):
    data = _SNAPSHOTS.get(snap_id)
    if not data:
        raise HTTPException(404, "snapshot not found")
    return Response(content=data, media_type="image/png")


def _verify_signature(body: bytes, timestamp: str, signature: str) -> bool:
    secret = os.getenv("SLACK_SIGNING_SECRET", "")
    if not secret:
        return True  # 개발 환경: signing secret 미설정 시 검증 스킵
    if not timestamp or abs(time.time() - int(timestamp)) > 300:
        return False
    sig_base = f"v0:{timestamp}:{body.decode('utf-8')}"
    expected = "v0=" + hmac.new(secret.encode(), sig_base.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _post_to_slack(url: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=10)



def _run_seat_and_reply(channel_id: str, response_url: str, classroom_id: int) -> None:
    """백그라운드: 좌석 점유 분석 → 배치도 이미지 → Slack 업로드."""
    classroom = storage.get_one(classroom_id)
    if not classroom:
        _post_to_slack(response_url, {"text": "교실을 찾을 수 없습니다."})
        return
    try:
        from app.services.frame_capture import capture_rtsp_frames_parallel
        from app.services.vision_llm_detection import _run_seat_occupancy

        all_occupied: set[str] = set()
        all_near: set[str] = set()
        all_seen: set[str] = set()

        cameras_with_seats = [c for c in classroom.cameras if c.rtsp_url and c.seat_lines]
        if not cameras_with_seats:
            _post_to_slack(response_url, {"text": f"❌ {classroom.name}: 좌석 선이 설정된 카메라가 없습니다."})
            return

        for cam, frame in capture_rtsp_frames_parallel(cameras_with_seats):
            if frame is None:
                continue
            r = _run_seat_occupancy(frame, cam, yolo_model=classroom.yolo_model or "yolov8x", conf_threshold=classroom.conf_threshold)
            all_occupied.update(r.get("occupied", []))
            all_near.update(r.get("near", []))
            all_seen.update(r.get("occupied", []))
            all_seen.update(r.get("near", []))
            all_seen.update(r.get("empty", []))

        all_near -= all_occupied  # 빨강 우선
        all_empty = all_seen - all_occupied - all_near

        total_seats = len(all_seen)
        total_occupied = len(all_occupied)
        total_near = len(all_near)
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        near_text = f", 🟠 근접 {total_near}석" if total_near else ""
        comment = (
            f"🪑 *{classroom.name}* 좌석 점유 현황 (YOLO) — "
            f"🔴 점유 {total_occupied}/{total_seats}석{near_text} ({now})"
        )

        map_data = storage.get_map_data(classroom_id)
        base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
        if map_data and base_url:
            from app.services.map_renderer import render_occupancy_map
            png_bytes = render_occupancy_map(map_data, all_occupied, all_empty, near=all_near)
            snap_id = _store_snapshot(png_bytes)
            image_url = f"{base_url}/api/slack/snapshot/{snap_id}"
            _post_to_slack(response_url, {
                "response_type": "in_channel",
                "blocks": [
                    {"type": "section", "text": {"type": "mrkdwn", "text": comment}},
                    {"type": "image", "image_url": image_url, "alt_text": "교실 배치도"},
                ],
            })
        else:
            _post_to_slack(response_url, {"response_type": "in_channel", "text": comment})
    except Exception as e:
        _post_to_slack(response_url, {"text": f"❌ 좌석 분석 오류: {e}"})


def _run_yolo_llm_and_reply(channel_id: str, response_url: str, classroom_id: int) -> None:
    """백그라운드: YOLO+LLM 좌석 점유 분석 → 배치도 이미지 → Slack 업로드."""
    classroom = storage.get_one(classroom_id)
    if not classroom:
        _post_to_slack(response_url, {"text": "교실을 찾을 수 없습니다."})
        return
    try:
        from app.services.frame_capture import capture_rtsp_frames_parallel
        from app.services.yolo_llm_detection import run_yolo_llm_count

        prompt_config = storage.get_prompt_config()
        base = prompt_config.default_user_prompt or ""
        extra = classroom.prompt or ""
        user_prompt = (base + "\n" + extra).strip() if extra else base

        all_occupied: set[str] = set()
        all_near: set[str] = set()
        all_seen: set[str] = set()
        total_yolo = 0

        cameras_with_seats = [c for c in classroom.cameras if c.rtsp_url and c.seat_lines]
        if not cameras_with_seats:
            _post_to_slack(response_url, {"text": f"❌ {classroom.name}: 좌석 선이 설정된 카메라가 없습니다."})
            return

        for cam, frame in capture_rtsp_frames_parallel(cameras_with_seats):
            if frame is None:
                continue
            r = run_yolo_llm_count(
                frame,
                system_prompt=prompt_config.system_prompt,
                user_prompt=user_prompt,
                conf_threshold=classroom.yolo_llm_conf_threshold,
                seat_lines=cam.seat_lines or {},
                llm_model=classroom.yolo_llm_model or "claude-haiku-4-5-20251001",
                yolo_model=classroom.yolo_llm_yolo_model or "yolo26x",
            )
            total_yolo += r["yolo_count"]
            all_occupied.update(r.get("occupied", []))
            all_near.update(r.get("near", []))
            all_seen.update(r.get("occupied", []))
            all_seen.update(r.get("near", []))
            all_seen.update(r.get("empty", []))

        all_near -= all_occupied
        all_empty = all_seen - all_occupied - all_near

        total_seats = len(all_seen)
        total_occupied = len(all_occupied)
        total_near = len(all_near)
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        near_text = f", 🟠 근접 {total_near}석" if total_near else ""
        comment = (
            f"🤖 *{classroom.name}* 좌석 점유 현황 (YOLO+LLM) — "
            f"🔴 점유 {total_occupied}/{total_seats}석{near_text} ({now})"
        )

        map_data = storage.get_map_data(classroom_id)
        base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
        if map_data and base_url:
            from app.services.map_renderer import render_occupancy_map
            png_bytes = render_occupancy_map(map_data, all_occupied, all_empty, near=all_near)
            snap_id = _store_snapshot(png_bytes)
            image_url = f"{base_url}/api/slack/snapshot/{snap_id}"
            _post_to_slack(response_url, {
                "response_type": "in_channel",
                "blocks": [
                    {"type": "section", "text": {"type": "mrkdwn", "text": comment}},
                    {"type": "image", "image_url": image_url, "alt_text": "교실 배치도"},
                ],
            })
        else:
            _post_to_slack(response_url, {"response_type": "in_channel", "text": comment})
    except Exception as e:
        _post_to_slack(response_url, {"text": f"❌ YOLO+LLM 좌석 분석 오류: {e}"})


@router.post("/slash-seat")
async def slash_seat_command(request: Request, background_tasks: BackgroundTasks):
    """Slack /좌석 커맨드 핸들러."""
    body = await request.body()
    if not _verify_signature(
        body,
        request.headers.get("X-Slack-Request-Timestamp", ""),
        request.headers.get("X-Slack-Signature", ""),
    ):
        raise HTTPException(403, "Invalid Slack signature")

    form = await request.form()
    text = (form.get("text") or "").strip()
    response_url = form.get("response_url", "")
    channel_id = form.get("channel_id", "")

    classrooms = storage.get_all()
    if not classrooms:
        return JSONResponse({"text": "등록된 교실이 없습니다."})

    classroom = None
    if text.isdigit():
        classroom = storage.get_one(int(text))
    elif text:
        classroom = next((c for c in classrooms if text in c.name), None)
    if classroom is None:
        classroom = classrooms[0]

    background_tasks.add_task(_run_seat_and_reply, channel_id, response_url, classroom.id)
    return JSONResponse({"text": f"⏳ *{classroom.name}* 좌석 점유 분석 중... 잠시만 기다려주세요."})


@router.post("/slash-seat-detail")
async def slash_seat_detail_command(request: Request, background_tasks: BackgroundTasks):
    """Slack /좌석상세 커맨드 핸들러 (YOLO+LLM)."""
    body = await request.body()
    if not _verify_signature(
        body,
        request.headers.get("X-Slack-Request-Timestamp", ""),
        request.headers.get("X-Slack-Signature", ""),
    ):
        raise HTTPException(403, "Invalid Slack signature")

    form = await request.form()
    text = (form.get("text") or "").strip()
    response_url = form.get("response_url", "")
    channel_id = form.get("channel_id", "")

    classrooms = storage.get_all()
    if not classrooms:
        return JSONResponse({"text": "등록된 교실이 없습니다."})

    classroom = None
    if text.isdigit():
        classroom = storage.get_one(int(text))
    elif text:
        classroom = next((c for c in classrooms if text in c.name), None)
    if classroom is None:
        classroom = classrooms[0]

    background_tasks.add_task(_run_yolo_llm_and_reply, channel_id, response_url, classroom.id)
    return JSONResponse({"text": f"⏳ *{classroom.name}* 좌석 점유 분석 중... 잠시만 기다려주세요."})


