"""분석 라우터: 프레임 캡처, ROI 저장, 인원 카운트."""
from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List

from app import storage

router = APIRouter()


# ── 프레임 캡처 ──────────────────────────────────────────────────────────────

@router.get("/{classroom_id}/frame/{camera_id}")
def get_camera_frame(classroom_id: int, camera_id: str):
    classroom = storage.get_one(classroom_id)
    if not classroom:
        raise HTTPException(404, "Classroom not found")
    camera = next((c for c in classroom.cameras if c.camera_id == camera_id), None)
    if not camera:
        raise HTTPException(404, "Camera not found")
    if not camera.rtsp_url:
        raise HTTPException(400, "카메라에 RTSP URL이 없습니다")
    try:
        from app.services.frame_capture import capture_rtsp_frame, frame_to_base64
        frame = capture_rtsp_frame(camera.rtsp_url)
        if frame is None:
            raise HTTPException(503, "RTSP 프레임 캡처 실패")
        return {"image": frame_to_base64(frame), "width": int(frame.shape[1]), "height": int(frame.shape[0])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(503, f"프레임 캡처 오류: {e}")


# ── ROI / 맵 저장 ─────────────────────────────────────────────────────────────

class MapImageRequest(BaseModel):
    image: str

class SeatCountsRequest(BaseModel):
    seat_counts: dict
    seat_ids: dict = {}

class SeatLinesRequest(BaseModel):
    seat_lines: dict  # {"A1": [[x1, y1], [x2, y2]]}

@router.post("/{classroom_id}/map-image")
def save_map_image(classroom_id: int, body: MapImageRequest):
    storage.save_map_image(classroom_id, body.image)
    return {"ok": True}

@router.post("/{classroom_id}/seat-counts")
def update_seat_counts(classroom_id: int, body: SeatCountsRequest):
    """맵 에디터에서 카메라별 담당 자리 수를 동기화한다. 라벨(대소문자 무시)로 카메라를 매칭."""
    classroom = storage.get_one(classroom_id)
    if not classroom:
        raise HTTPException(404, "Classroom not found")
    from app.models import ClassroomUpdate
    updated_cameras = classroom.model_dump()["cameras"]
    for cam in updated_cameras:
        cam_name = cam["name"].strip().lower()
        for label, count in body.seat_counts.items():
            if label.strip().lower() == cam_name:
                cam["seat_count"] = count if count > 0 else None
                ids = [str(s) for s in body.seat_ids.get(label, [])]
                cam["seat_ids"] = ids
                # 맵에서 삭제된 좌석의 seat_lines 항목 제거
                valid = set(ids)
                cam["seat_lines"] = {
                    k: v for k, v in (cam.get("seat_lines") or {}).items()
                    if k in valid
                }
                break
    storage.update(classroom_id, ClassroomUpdate(cameras=updated_cameras))
    return {"ok": True}



@router.post("/{classroom_id}/seat-lines/{camera_id}")
def save_seat_lines(classroom_id: int, camera_id: str, body: SeatLinesRequest):
    """Save per-seat occupancy lines in camera frame coordinates."""
    classroom = storage.get_one(classroom_id)
    if not classroom:
        raise HTTPException(404, "Classroom not found")
    from app.models import ClassroomUpdate
    updated_cameras = classroom.model_dump()["cameras"]
    for cam in updated_cameras:
        if cam["camera_id"] == camera_id:
            cam["seat_lines"] = body.seat_lines
            storage.update(classroom_id, ClassroomUpdate(cameras=updated_cameras))
            return {"ok": True}
    raise HTTPException(404, "Camera not found")



# ── Background Subtraction ───────────────────────────────────────────────────

@router.post("/{classroom_id}/bg-reference/{camera_id}")
def save_bg_reference(classroom_id: int, camera_id: str):
    """현재 RTSP 프레임을 이 카메라의 '빈 강의실 기준'으로 저장."""
    classroom = storage.get_one(classroom_id)
    if not classroom:
        raise HTTPException(404, "Classroom not found")
    camera = next((c for c in classroom.cameras if c.camera_id == camera_id), None)
    if not camera:
        raise HTTPException(404, "Camera not found")
    if not camera.rtsp_url:
        raise HTTPException(400, "카메라에 RTSP URL이 없습니다")
    try:
        from app.services.frame_capture import capture_rtsp_frame, frame_to_base64
        from app.services.background_detection import save_reference

        frame = capture_rtsp_frame(camera.rtsp_url)
        if frame is None:
            raise HTTPException(503, "RTSP 프레임 캡처 실패")
        save_reference(camera_id, frame)
        return {"ok": True, "image": frame_to_base64(frame), "camera_id": camera_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(503, f"기준 저장 오류: {e}")


@router.get("/{classroom_id}/bg-detect/{camera_id}")
def bg_detect(classroom_id: int, camera_id: str):
    """기준 프레임과 현재 프레임을 비교해 사람 유무를 반환."""
    classroom = storage.get_one(classroom_id)
    if not classroom:
        raise HTTPException(404, "Classroom not found")
    camera = next((c for c in classroom.cameras if c.camera_id == camera_id), None)
    if not camera:
        raise HTTPException(404, "Camera not found")
    if not camera.rtsp_url:
        raise HTTPException(400, "카메라에 RTSP URL이 없습니다")
    try:
        from app.services.frame_capture import capture_rtsp_frame, frame_to_base64
        from app.services.background_detection import detect_occupied

        frame = capture_rtsp_frame(camera.rtsp_url)
        if frame is None:
            raise HTTPException(503, "RTSP 프레임 캡처 실패")
        result = detect_occupied(camera_id, frame)
        result["image"] = frame_to_base64(frame)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(503, f"배경 차분 감지 오류: {e}")


@router.post("/{classroom_id}/bg-reference-upload/{camera_id}")
async def upload_bg_reference(classroom_id: int, camera_id: str, file: UploadFile = File(...)):
    """업로드한 이미지를 이 카메라의 빈 강의실 기준으로 저장."""
    classroom = storage.get_one(classroom_id)
    if not classroom:
        raise HTTPException(404, "Classroom not found")
    if not any(c.camera_id == camera_id for c in classroom.cameras):
        raise HTTPException(404, "Camera not found")
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "이미지 파일만 업로드할 수 있습니다")
    try:
        from app.services.frame_capture import frame_to_base64
        from app.services.background_detection import save_reference

        data = await file.read()
        arr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(400, "이미지 파일을 읽을 수 없습니다")
        save_reference(camera_id, frame)
        return {"ok": True, "image": frame_to_base64(frame), "camera_id": camera_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"업로드 오류: {e}")


@router.get("/{classroom_id}/bg-status/{camera_id}")
def bg_status(classroom_id: int, camera_id: str):
    """이 카메라에 기준 이미지가 저장되어 있는지 확인."""
    from app.services.background_detection import has_reference
    return {"camera_id": camera_id, "has_reference": has_reference(camera_id)}


# ── LLM 좌석 점유 분석 ─────────────────────────────────────────────────────────

@router.get("/{classroom_id}/seat-occupancy")
def seat_occupancy(classroom_id: int):
    """모든 카메라에 대해 LLM으로 좌석 점유 현황을 반환한다."""
    classroom = storage.get_one(classroom_id)
    if not classroom:
        raise HTTPException(404, "Classroom not found")

    cameras_with_seats = [c for c in classroom.cameras if c.rtsp_url and c.seat_lines]
    if not cameras_with_seats:
        raise HTTPException(400, "좌석 선이 설정된 카메라가 없습니다")

    try:
        from app.services.frame_capture import capture_rtsp_frames_parallel
        from app.services.vision_llm_detection import _run_seat_occupancy

        results = []
        global_occupied: set[str] = set()
        global_near: set[str] = set()
        global_seen: set[str] = set()

        for camera, frame in capture_rtsp_frames_parallel(cameras_with_seats):
            seat_ids = list((camera.seat_lines or {}).keys())
            if frame is None:
                results.append({
                    "camera_id": camera.camera_id,
                    "name": camera.name,
                    "error": "캡처 실패",
                    "occupied": [], "near": [], "empty": seat_ids,
                    "total": len(seat_ids), "occupied_count": 0,
                })
                global_seen.update(seat_ids)
                continue
            try:
                r = _run_seat_occupancy(frame, camera, yolo_model=classroom.yolo_model or "yolov8x", conf_threshold=classroom.conf_threshold)
                results.append({"camera_id": camera.camera_id, "name": camera.name, **r})
                global_occupied.update(r.get("occupied", []))
                global_near.update(r.get("near", []))
                global_seen.update(r.get("occupied", []))
                global_seen.update(r.get("near", []))
                global_seen.update(r.get("empty", []))
            except Exception as e:
                results.append({
                    "camera_id": camera.camera_id, "name": camera.name,
                    "error": str(e),
                    "occupied": [], "near": [], "empty": seat_ids,
                    "total": len(seat_ids), "occupied_count": 0,
                })
                global_seen.update(seat_ids)

        global_near -= global_occupied  # 빨강 우선: 이미 점유된 좌석은 near에서 제거
        global_empty = global_seen - global_occupied - global_near
        return {
            "cameras": results,
            "total_seats": len(global_seen),
            "total_occupied": len(global_occupied),
            "total_near": len(global_near),
            "total_empty": len(global_empty),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(503, f"좌석 점유 분석 오류: {e}")


# ── YOLO (PersonCounter) + LLM 인원 카운트 ────────────────────────────────────

@router.get("/{classroom_id}/yolo-llm-count")
def yolo_llm_count(classroom_id: int):
    """모든 카메라에 대해 PersonCounter(yolo11n)로 감지 후 LLM이 프롬프트에 따라 분석."""
    classroom = storage.get_one(classroom_id)
    if not classroom:
        raise HTTPException(404, "Classroom not found")

    cameras_with_rtsp = [c for c in classroom.cameras if c.rtsp_url]
    if not cameras_with_rtsp:
        raise HTTPException(400, "RTSP URL이 설정된 카메라가 없습니다")

    try:
        from app.services.frame_capture import capture_rtsp_frames_parallel
        from app.services.yolo_llm_detection import run_yolo_llm_count

        prompt_config = storage.get_prompt_config()
        base = prompt_config.default_user_prompt or ""
        extra = classroom.prompt or ""
        user_prompt = (base + "\n" + extra).strip() if extra else base

        results = []
        total_count = 0
        global_occupied: set[str] = set()
        global_near: set[str] = set()
        global_seen: set[str] = set()

        for camera, frame in capture_rtsp_frames_parallel(cameras_with_rtsp):
            seat_ids = list((camera.seat_lines or {}).keys())
            if frame is None:
                results.append({
                    "camera_id": camera.camera_id,
                    "name": camera.name,
                    "error": "캡처 실패",
                    "yolo_count": 0,
                    "occupied": [], "near": [], "empty": seat_ids,
                    "total": len(seat_ids), "occupied_count": 0,
                    "llm_response": None,
                })
                global_seen.update(seat_ids)
                continue
            try:
                r = run_yolo_llm_count(
                    frame,
                    system_prompt=prompt_config.system_prompt,
                    user_prompt=user_prompt,
                    conf_threshold=classroom.yolo_llm_conf_threshold,
                    seat_lines=camera.seat_lines or {},
                    llm_model=classroom.yolo_llm_model or "claude-haiku-4-5-20251001",
                    yolo_model=classroom.yolo_llm_yolo_model or "yolo26x",
                )
                results.append({"camera_id": camera.camera_id, "name": camera.name, **r})
                total_count += r["yolo_count"]
                global_occupied.update(r.get("occupied", []))
                global_near.update(r.get("near", []))
                global_seen.update(r.get("occupied", []))
                global_seen.update(r.get("near", []))
                global_seen.update(r.get("empty", []))
            except Exception as e:
                results.append({
                    "camera_id": camera.camera_id,
                    "name": camera.name,
                    "error": str(e),
                    "yolo_count": 0,
                    "occupied": [], "near": [], "empty": seat_ids,
                    "total": len(seat_ids), "occupied_count": 0,
                    "llm_response": None,
                })
                global_seen.update(seat_ids)

        global_near -= global_occupied
        return {
            "cameras": results,
            "total_yolo_count": total_count,
            "total_seats": len(global_seen),
            "total_occupied": len(global_occupied),
            "total_near": len(global_near),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(503, f"YOLO+LLM 카운트 오류: {e}")
