"""순찰: 등록된 구역을 순서대로 한 바퀴 돌며 미허가 인물을 촬영해 기록한다.

백그라운드 스레드가 구역마다 [이동 -> 정착 대기 -> 촬영 -> 얼굴 매칭]을 수행하고,
마지막 구역까지 마치면 그 자리에서 끝난다(반복하지 않음). PTZ 이동은 물리적으로 수 초가
걸리므로 목표 좌표에 도달했는지 확인한 뒤 촬영하고, 흔들림 때문에 한 장에서 얼굴을
놓칠 수 있어 여러 장을 시도한다.

한 사람이 인접한 구역에 겹쳐 잡혀 같은 기록이 중복되지 않도록 쿨다운을 둔다.
"""
from __future__ import annotations

import threading
import time

import cv2
import numpy as np

from app import detection_storage, face_storage, ptz_storage, seat_log_storage
from app.services import ptz_camera

SETTLE_TIMEOUT = 5.0      # 구역에서 멈출 때까지 최대 대기(초)
SETTLE_TOLERANCE = 12     # 팬/틸트 도달 판정 허용 오차 (0.1도 단위)
SETTLE_POLL_INTERVAL = 0.2
SETTLE_STABLE_POLLS = 3   # 연속 이만큼 좌표가 같아야 "멈췄다"고 본다
SETTLE_EXTRA = 2.0        # 정지 후 영상 흔들림이 가라앉을 때까지 추가 대기
SHOTS_PER_ZONE = 1        # 구역당 촬영 시도 장수
SHOT_INTERVAL = 0.0
ZONE_REST = 0.0           # 다음 구역으로 넘어가기 전 여유
COOLDOWN_SEC = 120.0      # 같은 대상을 다시 기록하기까지의 최소 간격


def wait_until_settled(cam: dict, zone: dict, stop_event: threading.Event | None = None) -> None:
    """카메라가 목표 구역에서 실제로 멈출 때까지 빠르게 기다린다."""
    deadline = time.time() + SETTLE_TIMEOUT
    last = None
    stable = 0
    while time.time() < deadline and not (stop_event and stop_event.is_set()):
        try:
            pos = ptz_camera.get_position(cam)
        except Exception:
            break
        if pos["pan"] is None:
            break

        current = (pos["pan"], pos["tilt"], pos["zoom"])
        near = (abs(pos["pan"] - zone["pan"]) <= SETTLE_TOLERANCE
                and abs(pos["tilt"] - zone["tilt"]) <= SETTLE_TOLERANCE)
        stable = stable + 1 if (current == last and near) else 0
        if stable >= SETTLE_STABLE_POLLS:
            break
        last = current
        time.sleep(SETTLE_POLL_INTERVAL)

    # 좌표가 멈춘 뒤에도 영상 쪽 흔들림이 남아 있어 잠시 더 기다린다.
    if stop_event:
        stop_event.wait(SETTLE_EXTRA)
    else:
        time.sleep(SETTLE_EXTRA)


class _Patrol:
    def __init__(self, place_id: int, record_all: bool = False):
        self.place_id = place_id
        # record_all: 허가된 인원까지 모두 촬영한다 (동작 확인용).
        self.record_all = record_all
        self.stop_event = threading.Event()
        self.state = {
            "running": True,
            "zone": None,
            "zone_index": 0,
            "total_zones": 0,
            "detections": 0,
            "completed": False,
            "record_all": record_all,
            "seats_logged": 0,
            "error": None,
            "started_at": time.time(),
        }
        self._recent: dict[str, float] = {}   # 쿨다운 키 -> 마지막 기록 시각
        self._seats: dict[str, dict | None] = {}   # 이번 순찰의 자리번호별 결과
        self.thread = threading.Thread(target=self._run_safe, daemon=True)
        self.thread.start()

    # ── 루프 ─────────────────────────────────────────────────────────────────

    def _run_safe(self):
        try:
            self._run()
        except Exception as e:
            self.state["error"] = f"{type(e).__name__}: {e}"
        finally:
            self.state["running"] = False
            self.state["zone"] = None

    def _run(self):
        from app.services import face_db
        from app.services.frame_capture import capture_rtsp_frame

        place = ptz_storage.get_one(self.place_id)
        if not place:
            raise RuntimeError("장소가 삭제되었습니다")
        zones = place["zones"]
        if not zones:
            raise RuntimeError("등록된 순찰 구역이 없습니다")

        cam = place["camera"]
        rtsp = ptz_camera.rtsp_url(cam)
        self.state["total_zones"] = len(zones)

        # 등록된 순서대로 한 바퀴만 돈다. 마지막 구역에서 카메라가 멈춘 채 끝난다.
        for index, zone in enumerate(zones, start=1):
            if self.stop_event.is_set():
                return
            self.state["zone"] = zone["name"]
            self.state["zone_index"] = index
            ptz_camera.move_absolute(cam, zone["pan"], zone["tilt"], zone["zoom"])

            # 자리 영역이 없는 구역은 대기 위치로만 쓰는 곳이므로 인식하지 않고 지나간다.
            # (초기 고정 구역처럼 순찰이 끝난 뒤 카메라를 세워두는 자리)
            if not zone.get("rois"):
                if index < len(zones) and self.stop_event.wait(ZONE_REST):
                    return
                continue

            self._wait_until_settled(cam, zone)

            if self.stop_event.is_set():
                return
            # fresh=True: 이동 전 장면이 섞이지 않도록 새로 디코딩된 프레임만 쓴다.
            frame = capture_rtsp_frame(rtsp, timeout_ms=3000, fresh=True)
            matches = self._analyze(frame, zone, face_db) if frame is not None else []

            if frame is not None:
                self._record(frame, matches, zone)
            self._collect_seats(zone, matches)
            if self._seats:
                seat_log_storage.append_snapshot(self.place_id, self._seats)
                self.state["seats_logged"] = len(self._seats)

            # 마지막 구역 뒤에는 쉴 필요가 없다 (그 자리에서 순찰이 끝난다)
            if index < len(zones) and self.stop_event.wait(ZONE_REST):
                return

        self.state["seats_logged"] = len(self._seats)
        self.state["completed"] = True

    def _wait_until_settled(self, cam: dict, zone: dict) -> None:
        """카메라가 목표 구역에서 실제로 멈출 때까지 기다린다.

        오차 범위에 들어왔다고 멈춘 것은 아니다 — 지나쳤다가 되돌아오는 중일 수 있다.
        그래서 목표 근처인 동시에 연속 조회에서 좌표(줌 포함)가 변하지 않아야 정지로 본다.
        """
        wait_until_settled(cam, zone, self.stop_event)

    # ── 판정 ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _find_roi(zone: dict, face, frame_shape) -> dict | None:
        """얼굴 중심이 들어가는 자리 영역을 찾는다. ROI가 없는 구역이면 None.

        좌석 확인의 좌석 밴드와 같이 4점의 볼록 영역으로 판정하므로, 점을 찍은 순서가
        달라도 같은 영역이 된다.
        """
        rois = zone.get("rois")
        if not rois:
            return None
        h, w = frame_shape[:2]
        cx = (face.bbox[0] + face.bbox[2]) / 2 / w
        cy = (face.bbox[1] + face.bbox[3]) / 2 / h
        for roi in rois:
            quad = np.array(roi["points"], dtype=np.float32)
            hull = cv2.convexHull(quad)
            if cv2.pointPolygonTest(hull, (float(cx), float(cy)), False) >= 0:
                return roi
        return None

    def _cooldown_key(self, zone: dict, face, name: str | None) -> str:
        """중복 기록을 막는 키.

        미등록 인물은 이름이 없어 전부 'unknown'으로 묶이는데, 그러면 한 구역에 여러 명이
        있어도 첫 사람만 기록되고 나머지는 쿨다운에 걸려 사라진다. 자리마다 사람이 다르므로
        얼굴 위치(100px 격자)로 구분한다.
        """
        if name:
            return f"{zone['name']}|{name}"
        cx = int((face.bbox[0] + face.bbox[2]) / 2) // 100
        cy = int((face.bbox[1] + face.bbox[3]) / 2) // 100
        return f"{zone['name']}|unknown@{cx},{cy}"

    def _analyze(self, frame, zone: dict, face_db) -> list[dict]:
        """프레임 속 얼굴을 모두 찾아 자리·신원을 매칭한다 (기록은 하지 않음)."""
        has_rois = bool(zone.get("rois"))
        matches = []
        for face in face_db.detect(frame):
            roi = self._find_roi(zone, face, frame.shape)
            # ROI를 설정한 구역에서는 영역 밖 얼굴(모니터 속 얼굴, 지나가는 사람)을 무시한다
            if has_rois and roi is None:
                continue
            name, score = face_db.match(face.normed_embedding)
            person = face_storage.get_by_name(name) if name else None
            authorized = bool(person["authorized"]) if person else None
            matches.append({"face": face, "name": name, "score": score,
                            "authorized": authorized, "roi": roi})
        return matches

    def _collect_seats(self, zone: dict, matches: list[dict]) -> None:
        """자리 번호별 결과를 이번 순찰분에 쌓는다. 사람이 없으면 None으로 남긴다."""
        found: dict[str, dict] = {}
        for m in matches:
            if not m["roi"]:
                continue
            name = m["roi"]["name"]
            current = found.get(name)
            if current is None or self._seat_match_rank(m) > self._seat_match_rank(current):
                found[name] = m
        for roi in zone.get("rois") or []:
            key = seat_log_storage.seat_key(roi["name"])
            m = found.get(roi["name"])
            self._seats[key] = None if m is None else {
                # 등록됐고 허가까지 된 사람만 검증 통과로 본다
                "verified": bool(m["authorized"]),
                "name": m["name"],
                "score": round(m["score"], 3),
                "zone": zone["name"],
            }

    @staticmethod
    def _seat_match_rank(match: dict) -> tuple[int, int, float]:
        """Pick the best representative when multiple faces fall in the same seat ROI."""
        return (
            1 if match.get("authorized") else 0,
            1 if match.get("name") else 0,
            float(match.get("score") or 0),
        )

    def _record(self, frame, matches: list[dict], zone: dict) -> bool:
        """기록 대상 인물이 있으면 사진과 함께 남긴다. 기록했으면 True."""
        recorded = False
        for m in matches:
            key = (f"{zone['name']}|{m['roi']['name']}" if m["roi"]
                   else self._cooldown_key(zone, m["face"], m["name"]))
            now = time.time()
            if now - self._recent.get(key, 0) < COOLDOWN_SEC:
                continue
            self._recent[key] = now

            zone_label = f"{zone['name']} · {m['roi']['name']}" if m["roi"] else zone["name"]
            record = detection_storage.add(self.place_id, zone_label, m["name"],
                                           m["score"], m["authorized"])
            self._save_image(frame, matches, m, record["id"], zone)
            self.state["detections"] += 1
            recorded = True
        return recorded

    def _save_image(self, frame, matches: list[dict], subject: dict,
                    detection_id: int, zone: dict) -> None:
        """기록 대상은 굵게, 같은 프레임의 다른 얼굴도 함께 표시해 상황을 알 수 있게 한다."""
        annotated = frame.copy()
        h, w = annotated.shape[:2]

        # 설정된 자리 영역을 옅게 깔아 어느 자리에서 잡힌 것인지 보이게 한다
        for roi in zone.get("rois") or []:
            quad = np.array([[p[0] * w, p[1] * h] for p in roi["points"]], dtype=np.int32)
            hull = cv2.convexHull(quad)
            cv2.polylines(annotated, [hull], True, (200, 120, 0), 1)
            top_left = hull.reshape(-1, 2).min(axis=0)
            cv2.putText(annotated, roi["name"], (int(top_left[0]) + 4, int(top_left[1]) + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 120, 0), 1)

        for m in matches:
            is_subject = m is subject
            x1, y1, x2, y2 = (int(v) for v in m["face"].bbox)
            # 기록 대상=빨강 굵게, 허가된 사람=초록, 그 외=회색
            color = (0, 0, 255) if is_subject else (0, 170, 0) if m["authorized"] else (150, 150, 150)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3 if is_subject else 2)
            label = f"{m['name'] or 'UNKNOWN'} {m['score']:.2f}"
            cv2.putText(annotated, label, (x1, max(y1 - 8, 16)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        h, w = annotated.shape[:2]
        if w > 1280:
            annotated = cv2.resize(annotated, (1280, int(h * 1280 / w)))
        detection_storage.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(detection_storage.image_path(detection_id)), annotated)

    def stop(self):
        self.stop_event.set()


_patrols: dict[int, _Patrol] = {}
_lock = threading.Lock()


def start(place_id: int, record_all: bool = False) -> dict:
    with _lock:
        current = _patrols.get(place_id)
        if current and current.state["running"]:
            return current.state
        _patrols[place_id] = _Patrol(place_id, record_all)
        return _patrols[place_id].state


def start_all() -> list[str]:
    """정기 수집용: 순찰할 수 있는 모든 장소를 한 바퀴 돌린다.

    카메라가 없거나 자리 영역을 하나도 그리지 않은 장소, 자동 순찰을 꺼 둔 장소는 건너뛴다.
    이미 돌고 있는 장소는 start()가 알아서 무시한다.
    """
    started = []
    for place in ptz_storage.get_all():
        if not ptz_storage.auto_patrol_enabled(place):
            continue
        if not place["camera"].get("ip"):
            continue
        if not any(z.get("rois") for z in place["zones"]):
            continue
        state = start(place["id"])
        if state["running"]:
            started.append(place["name"])
    return started


def stop(place_id: int) -> None:
    with _lock:
        patrol = _patrols.pop(place_id, None)
    if patrol:
        patrol.stop()


def status(place_id: int) -> dict:
    patrol = _patrols.get(place_id)
    if not patrol:
        return {"running": False, "zone": None, "zone_index": 0, "total_zones": 0,
                "detections": 0, "completed": False, "record_all": False,
                "seats_logged": 0, "error": None}
    return patrol.state
