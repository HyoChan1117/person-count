"""얼굴 인식: 감시 장소 / PTZ 카메라 설정 / 순찰 구역 / 감지 기록.

좌석 점유(교실)와는 독립된 기능이다. 현재는 장소 관리와 수동 제어·구역 등록까지
구현돼 있고, 순찰 루프와 얼굴 매칭은 다음 단계에서 붙인다.
"""
from __future__ import annotations

import asyncio

import cv2
import numpy as np
import requests
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi import Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app import detection_storage, face_storage, ptz_storage, seat_log_storage, storage
from app.services import ptz_camera

router = APIRouter()


class PlaceCreate(BaseModel):
    # 좌석 확인에 등록된 교실을 고른 경우 classroom_id만 보내면 교실 이름을 그대로 쓴다.
    name: str | None = None
    classroom_id: int | None = None


class PlaceUpdate(BaseModel):
    name: str | None = None
    camera: dict | None = None
    classroom_id: int | None = None
    clear_classroom: bool = False


class MoveRequest(BaseModel):
    pan: int = 0
    tilt: int = 0
    zoom: int = 0


class ZoneCreate(BaseModel):
    name: str


def _get_place(place_id: int) -> dict:
    place = ptz_storage.get_one(place_id)
    if not place:
        raise HTTPException(404, "장소를 찾을 수 없습니다")
    return place


def _require_ptz(place: dict) -> dict:
    """IP가 비어 있으면 PTZ 카메라가 없는 장소다."""
    cam = place["camera"]
    if not cam.get("ip"):
        raise HTTPException(400, "카메라 설정에서 IP를 먼저 입력해주세요")
    return cam


def _camera_call(fn, cam: dict, *args):
    """카메라 통신 실패를 502로 변환해 프론트에서 원인을 구분할 수 있게 한다."""
    try:
        return fn(cam, *args)
    except requests.RequestException as e:
        raise HTTPException(502, f"PTZ 카메라 통신 실패: {e}")


# ── 감시 장소 ────────────────────────────────────────────────────────────────

@router.get("/places")
def list_places():
    return {"places": ptz_storage.get_all()}


@router.post("/places")
def create_place(body: PlaceCreate):
    name = (body.name or "").strip()
    if body.classroom_id is not None:
        classroom = storage.get_one(body.classroom_id)
        if not classroom:
            raise HTTPException(404, "선택한 교실을 찾을 수 없습니다")
        name = name or classroom.name
    if not name:
        raise HTTPException(400, "장소 이름을 입력하거나 교실을 선택해주세요")
    return ptz_storage.create(name, ptz_camera.default_camera(), body.classroom_id)


@router.get("/places/{place_id}")
def get_place(place_id: int):
    return _get_place(place_id)


@router.put("/places/{place_id}")
def update_place(place_id: int, body: PlaceUpdate):
    _get_place(place_id)
    if body.classroom_id is not None and not storage.get_one(body.classroom_id):
        raise HTTPException(404, "선택한 교실을 찾을 수 없습니다")
    return ptz_storage.update(place_id, body.name, body.camera,
                              body.classroom_id, body.clear_classroom)


@router.delete("/places/{place_id}")
def delete_place(place_id: int):
    if not ptz_storage.remove(place_id):
        raise HTTPException(404, "장소를 찾을 수 없습니다")
    return {"ok": True}


@router.get("/places/{place_id}/camera/test")
def test_camera(place_id: int):
    """카메라 설정 화면에서 연결 확인용."""
    place = _get_place(place_id)
    cam = _require_ptz(place)
    info = _camera_call(ptz_camera.device_info, cam)
    position = _camera_call(ptz_camera.get_position, cam)
    return {"ok": True, **info, "position": position}


# ── PTZ 제어 ─────────────────────────────────────────────────────────────────

@router.get("/places/{place_id}/ptz/position")
def get_position(place_id: int):
    place = _get_place(place_id)
    return _camera_call(ptz_camera.get_position, _require_ptz(place))


@router.post("/places/{place_id}/ptz/move")
def move(place_id: int, body: MoveRequest):
    """수동 조작: 누르고 있는 동안 이동, 떼면 /stop 호출."""
    place = _get_place(place_id)
    _camera_call(ptz_camera.move_continuous, _require_ptz(place), body.pan, body.tilt, body.zoom)
    return {"ok": True}


@router.post("/places/{place_id}/ptz/stop")
def stop(place_id: int):
    place = _get_place(place_id)
    _camera_call(ptz_camera.stop, _require_ptz(place))
    return {"ok": True}


# ── 순찰 구역 ────────────────────────────────────────────────────────────────

@router.get("/places/{place_id}/zones")
def list_zones(place_id: int):
    return {"zones": _get_place(place_id)["zones"]}


@router.post("/places/{place_id}/zones")
def create_zone(place_id: int, body: ZoneCreate):
    """현재 카메라가 보고 있는 위치를 구역으로 저장."""
    place = _get_place(place_id)
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "구역 이름을 입력해주세요")
    pos = _camera_call(ptz_camera.get_position, _require_ptz(place))
    if pos["pan"] is None:
        raise HTTPException(502, "카메라가 현재 위치를 반환하지 않았습니다")
    return ptz_storage.add_zone(place_id, name, pos["pan"], pos["tilt"], pos["zoom"])


class ZoneOrder(BaseModel):
    zone_ids: list[int]


@router.put("/places/{place_id}/zones/order")
def reorder_zones(place_id: int, body: ZoneOrder):
    """순찰 도는 순서를 바꾼다. 마지막 구역이 순찰이 끝나는 자리가 된다."""
    _get_place(place_id)
    zones = ptz_storage.reorder_zones(place_id, body.zone_ids)
    if zones is None:
        raise HTTPException(400, "구역 목록이 일치하지 않습니다")
    return {"zones": zones}


@router.delete("/places/{place_id}/zones/{zone_id}")
def delete_zone(place_id: int, zone_id: int):
    _get_place(place_id)
    if not ptz_storage.remove_zone(place_id, zone_id):
        raise HTTPException(404, "구역을 찾을 수 없습니다")
    return {"ok": True}


class Roi(BaseModel):
    """자리 영역. 앞선 2점 + 뒷선 2점이 이루는 4점 밴드이며 좌표는 0~1 비율값.

    좌석 확인의 좌석 선과 같은 방식이다. 비스듬히 보이는 자리는 축에 나란한 사각형으로
    감싸면 옆자리까지 물리므로, 네 점으로 기울어진 영역을 그린다.
    """
    name: str
    points: list[list[float]]


class RoiUpdate(BaseModel):
    rois: list[Roi]


@router.put("/places/{place_id}/zones/{zone_id}/rois")
def set_rois(place_id: int, zone_id: int, body: RoiUpdate):
    _get_place(place_id)
    if not ptz_storage.get_zone(place_id, zone_id):
        raise HTTPException(404, "구역을 찾을 수 없습니다")

    rois = []
    for index, r in enumerate(body.rois, start=1):
        if len(r.points) != 4:
            raise HTTPException(400, f"자리 영역은 4점이어야 합니다 ({len(r.points)}점 전달됨)")
        rois.append({
            "id": index,
            "name": r.name.strip() or f"{index}번 자리",
            "points": [[round(float(x), 4), round(float(y), 4)] for x, y in r.points],
        })
    return ptz_storage.set_zone_rois(place_id, zone_id, rois)


@router.post("/places/{place_id}/zones/{zone_id}/test")
async def test_zone(place_id: int, zone_id: int):
    """한 구역만 즉시 확인한다. 카메라를 옮겨 한 장 찍고 자리별 인식 결과를 돌려준다.

    순찰과 달리 기록을 남기지 않으므로 ROI를 조정하며 반복해서 시험할 수 있다.
    """
    place = _get_place(place_id)
    cam = _require_ptz(place)
    zone = ptz_storage.get_zone(place_id, zone_id)
    if not zone:
        raise HTTPException(404, "구역을 찾을 수 없습니다")
    face_db = _face_db()

    from app.services.frame_capture import capture_rtsp_frame
    from app.services.patrol import _Patrol, SETTLE_EXTRA

    def _run():
        ptz_camera.move_absolute(cam, zone["pan"], zone["tilt"], zone["zoom"])
        # 순찰과 같은 조건이 되도록 이동·안정화를 기다린 뒤 새 프레임으로 찍는다
        import time
        time.sleep(2.0 + SETTLE_EXTRA)
        frame = capture_rtsp_frame(ptz_camera.rtsp_url(cam), timeout_ms=5000, fresh=True)
        if frame is None:
            return None, []

        results = []
        for face in face_db.detect(frame):
            roi = _Patrol._find_roi(zone, face, frame.shape)
            name, score = face_db.match(face.normed_embedding)
            person = face_storage.get_by_name(name) if name else None
            results.append({
                "seat": roi["name"] if roi else None,
                "name": name,
                "score": round(score, 3),
                "authorized": bool(person["authorized"]) if person else None,
                "box": [int(v) for v in face.bbox],
            })
        return frame, results

    frame, faces = await asyncio.to_thread(_run)
    if frame is None:
        raise HTTPException(502, "카메라에서 화면을 가져오지 못했습니다")

    # 자리마다 누가 있는지 (빈 자리는 null) — 순찰 기록에 쓸 형식과 같다
    seats = {roi["name"]: None for roi in zone.get("rois") or []}
    for f in faces:
        if f["seat"]:
            seats[f["seat"]] = {"name": f["name"], "score": f["score"], "authorized": f["authorized"]}

    return {
        "zone": zone["name"],
        "detected": len(faces),
        "outside_roi": sum(1 for f in faces if f["seat"] is None),
        "faces": faces,
        "seats": seats,
    }


@router.get("/places/{place_id}/ptz/snapshot")
def snapshot(place_id: int):
    """ROI를 그릴 정지 화면 한 장. 미리보기와 달리 현재 프레임만 즉시 돌려준다."""
    place = _get_place(place_id)
    cam = _require_ptz(place)

    from app.services.frame_capture import capture_rtsp_frame
    frame = capture_rtsp_frame(ptz_camera.rtsp_url(cam), timeout_ms=5000, fresh=True)
    if frame is None:
        raise HTTPException(502, "카메라에서 화면을 가져오지 못했습니다")

    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise HTTPException(500, "화면을 이미지로 변환하지 못했습니다")
    return Response(content=buf.tobytes(), media_type="image/jpeg",
                    headers={"Cache-Control": "no-store"})


@router.post("/places/{place_id}/zones/{zone_id}/goto")
def goto_zone(place_id: int, zone_id: int):
    place = _get_place(place_id)
    zone = ptz_storage.get_zone(place_id, zone_id)
    if not zone:
        raise HTTPException(404, "구역을 찾을 수 없습니다")
    _camera_call(ptz_camera.move_absolute, _require_ptz(place), zone["pan"], zone["tilt"], zone["zoom"])
    return {"ok": True}


# ── 인물 등록 ────────────────────────────────────────────────────────────────

class AuthorizedUpdate(BaseModel):
    authorized: bool


def _face_db():
    """얼굴 인식 엔진 로드. 실패 원인이 화면에 드러나도록 503으로 변환한다.

    insightface는 backend/.venv에만 설치돼 있어, 다른 인터프리터로 서버를 띄우면
    여기서 ImportError가 난다 (그냥 두면 원인 모를 500이 된다).
    """
    try:
        from app.services import face_db
        return face_db
    except ImportError as e:
        raise HTTPException(503, f"얼굴 인식 엔진을 불러오지 못했습니다 ({e}). "
                                 "백엔드를 backend/.venv 인터프리터로 실행 중인지 확인해주세요.")


@router.get("/people")
def list_people():
    return {"people": face_storage.get_all()}


@router.post("/people")
async def enroll_person(name: str = Form(...), images: list[UploadFile] = File(...)):
    """사진 여러 장의 얼굴 임베딩을 평균내 등록한다. 같은 이름이면 재등록(갱신)."""
    face_db = _face_db()

    name = name.strip()
    if not name:
        raise HTTPException(400, "이름을 입력해주세요")

    frames = []
    for upload in images:
        buf = np.frombuffer(await upload.read(), dtype=np.uint8)
        frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if frame is not None:
            frames.append(frame)
    if not frames:
        raise HTTPException(400, "이미지를 읽지 못했습니다")

    try:
        # 모델 추론은 CPU/GPU를 오래 점유하므로 이벤트 루프를 막지 않게 별도 스레드에서
        found = await asyncio.to_thread(face_db.enroll, name, frames)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"얼굴 등록 처리 중 오류: {type(e).__name__}: {e}")

    person = face_storage.upsert(name, found)

    # 목록에 보여줄 썸네일: 얼굴이 검출된 첫 사진을 줄여서 저장
    face_storage.PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    thumb = frames[0]
    h, w = thumb.shape[:2]
    if w > 320:
        thumb = cv2.resize(thumb, (320, int(h * 320 / w)))
    cv2.imwrite(str(face_storage.photo_path(person["id"])), thumb)

    return {**person, "found": found, "total": len(frames)}


@router.get("/people/{person_id}/photo")
def person_photo(person_id: int):
    path = face_storage.photo_path(person_id)
    if not path.exists():
        raise HTTPException(404, "사진이 없습니다")
    return FileResponse(path, media_type="image/jpeg")


@router.put("/people/{person_id}/authorized")
def set_authorized(person_id: int, body: AuthorizedUpdate):
    person = face_storage.set_authorized(person_id, body.authorized)
    if not person:
        raise HTTPException(404, "등록된 인물을 찾을 수 없습니다")
    return person


@router.delete("/people/{person_id}")
def delete_person(person_id: int):
    face_db = _face_db()

    person = face_storage.remove(person_id)
    if not person:
        raise HTTPException(404, "등록된 인물을 찾을 수 없습니다")
    face_db.remove(person["name"])
    return {"ok": True}


@router.post("/recognize")
async def recognize(images: list[UploadFile] = File(...)):
    """사진에서 얼굴을 찾아 등록된 인물과 매칭한다 (인식 확인용)."""
    face_db = _face_db()

    frames = []
    for upload in images:
        buf = np.frombuffer(await upload.read(), dtype=np.uint8)
        frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if frame is not None:
            frames.append(frame)
    if not frames:
        raise HTTPException(400, "이미지를 읽지 못했습니다")

    def _run():
        results = []
        for frame in frames:
            for face in face_db.detect(frame):
                name, score = face_db.match(face.normed_embedding)
                person = face_storage.get_by_name(name) if name else None
                results.append({
                    "name": name,
                    "score": round(score, 3),
                    "authorized": bool(person["authorized"]) if person else None,
                    "det_score": round(float(face.det_score), 3),
                    "box": [int(v) for v in face.bbox],
                })
        return results

    faces = await asyncio.to_thread(_run)
    return {"faces": faces, "threshold": face_db.MATCH_THRESHOLD}


@router.get("/engine")
def engine_status():
    """얼굴 인식 모델이 GPU로 도는지 확인용."""
    try:
        from app.services import face_db
        return {"ok": True, "model": face_db.MODEL_NAME, "providers": face_db.providers()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── 순찰 ─────────────────────────────────────────────────────────────────────

class PatrolStart(BaseModel):
    # 동작 확인용: 허가된 인원까지 모두 촬영해 기록한다
    record_all: bool = False


@router.post("/places/{place_id}/patrol/start")
def patrol_start(place_id: int, body: PatrolStart | None = None):
    place = _get_place(place_id)
    _require_ptz(place)
    if not place["zones"]:
        raise HTTPException(400, "순찰할 구역을 먼저 등록해주세요")
    _face_db()   # 엔진을 못 불러오면 여기서 원인을 알려준다

    from app.services import patrol
    return patrol.start(place_id, body.record_all if body else False)


@router.post("/places/{place_id}/patrol/stop")
def patrol_stop(place_id: int):
    _get_place(place_id)
    from app.services import patrol
    patrol.stop(place_id)
    return {"ok": True}


@router.get("/places/{place_id}/patrol/status")
def patrol_status(place_id: int):
    _get_place(place_id)
    from app.services import patrol
    return patrol.status(place_id)


@router.get("/places/{place_id}/seat-logs")
def seat_logs(place_id: int, limit: int = 50):
    """순찰 1회마다 남는 자리 번호별 결과 (최신순)."""
    _get_place(place_id)
    return {"snapshots": seat_log_storage.get_snapshots(place_id, limit)}


# ── 감지 기록 ────────────────────────────────────────────────────────────────

@router.get("/places/{place_id}/detections")
def list_detections(place_id: int):
    _get_place(place_id)
    return {"detections": detection_storage.get_for_place(place_id)}


@router.get("/detections/{detection_id}/photo")
def detection_photo(detection_id: int):
    path = detection_storage.image_path(detection_id)
    if not path.exists():
        raise HTTPException(404, "사진이 없습니다")
    return FileResponse(path, media_type="image/jpeg")


@router.delete("/detections/{detection_id}")
def delete_detection(detection_id: int):
    if not detection_storage.remove(detection_id):
        raise HTTPException(404, "기록을 찾을 수 없습니다")
    return {"ok": True}


@router.delete("/places/{place_id}/detections")
def clear_detections(place_id: int):
    _get_place(place_id)
    return {"removed": detection_storage.clear_place(place_id)}


# ── 미리보기 스트림 ──────────────────────────────────────────────────────────

_EMIT_INTERVAL = 0.066  # 약 15fps
_PREVIEW_WIDTH = 1280   # 원본 2560x1440은 인코딩 비용이 커서 줄여 보낸다
_JPEG_QUALITY = 70


async def _preview_frames(cam: dict):
    """PTZ 조준용 미리보기. 카메라를 겨냥하는 용도라 YOLO 추론 없이 원본만 보낸다."""
    from app.services.frame_capture import capture_rtsp_frame

    url = ptz_camera.rtsp_url(cam)
    while True:
        frame = await asyncio.to_thread(capture_rtsp_frame, url, 2000)
        if frame is None:
            await asyncio.sleep(0.3)
            continue
        h, w = frame.shape[:2]
        if w > _PREVIEW_WIDTH:
            scale = _PREVIEW_WIDTH / w
            frame = cv2.resize(frame, (_PREVIEW_WIDTH, int(h * scale)))
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY])
        if ok:
            jpg = buf.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n"
                   b"Content-Length: " + str(len(jpg)).encode() + b"\r\n\r\n" +
                   jpg + b"\r\n")
        await asyncio.sleep(_EMIT_INTERVAL)


@router.get("/places/{place_id}/ptz/preview")
def preview(place_id: int):
    place = _get_place(place_id)
    cam = _require_ptz(place)
    return StreamingResponse(
        _preview_frames(cam),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"},
    )
