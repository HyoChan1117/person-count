"""Vision LLM 기반 좌석 점유 감지."""
from __future__ import annotations

import base64
import cv2
import numpy as np


def _to_b64(frame: np.ndarray) -> str:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf).decode("utf-8")


def _extract_band_crop(frame: np.ndarray, pts: list) -> np.ndarray:
    """4점 밴드의 바운딩 박스 영역을 프레임에서 추출."""
    xs = [pts[i][0] for i in range(len(pts))]
    ys = [pts[i][1] for i in range(len(pts))]
    x1, y1 = max(0, int(min(xs))), max(0, int(min(ys)))
    x2, y2 = min(frame.shape[1], int(max(xs))), min(frame.shape[0], int(max(ys)))
    return frame[y1:y2, x1:x2]


def _is_in_seat_band(px: float, py: float, pts: list) -> bool:
    """4점(앞선+뒷선)이 이루는 볼록 영역 안에 (px, py)가 있으면 True."""
    quad = np.array([[float(pts[i][0]), float(pts[i][1])] for i in range(4)], dtype=np.float32)
    hull = cv2.convexHull(quad)
    return cv2.pointPolygonTest(hull, (float(px), float(py)), False) >= 0


# COCO keypoint index (backend/test/posture_detect.py와 동일한 판정 로직)
_L_SHOULDER, _R_SHOULDER = 5, 6
_L_HIP, _R_HIP, _L_KNEE, _R_KNEE, _L_ANKLE, _R_ANKLE = 11, 12, 13, 14, 15, 16
_KPT_CONF_THRESHOLD = 0.5  # 이 아래는 "안 보임"으로 취급
_KNEE_STRAIGHT_ANGLE = 150.0  # 무릎 각도(도)가 이 이상이면 다리가 펴져 있음(=standing)
_HIP_STRAIGHT_ANGLE = 150.0  # 엉덩이 관절 각도(도)가 이 이상이면 상체-허벅지가 일직선(=standing)
_HIP_KNEE_TILT_SITTING = 40.0  # 엉덩이->무릎 방향이 수직 기준 이 각도 이상 기울면 sitting
_VISIBLE_LEG_RATIO_STANDING = 1.0  # (bbox 하단 - 엉덩이y) / 상체길이 가 이 이상이면 standing
_ASPECT_SITTING_RATIO = 1.3  # bbox 세로/가로 비율이 이보다 작으면 sitting (fallback 전용)


def _angle_deg(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """세 점 a-b-c에서 b를 꼭짓점으로 하는 각도(도)."""
    v1, v2 = a - b, c - b
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < 1e-6 or n2 < 1e-6:
        return 180.0
    cos_theta = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_theta)))


def _leg_angle(kp: np.ndarray, hip_idx: int, knee_idx: int, ankle_idx: int) -> float | None:
    if (kp[hip_idx][2] <= _KPT_CONF_THRESHOLD
            or kp[knee_idx][2] <= _KPT_CONF_THRESHOLD
            or kp[ankle_idx][2] <= _KPT_CONF_THRESHOLD):
        return None
    return _angle_deg(kp[hip_idx][:2], kp[knee_idx][:2], kp[ankle_idx][:2])


def _hip_angle(kp: np.ndarray, shoulder_idx: int, hip_idx: int, knee_idx: int) -> float | None:
    """어깨-엉덩이-무릎 세 점으로 계산한 엉덩이 관절 각도(상체와 허벅지 사이 각도)."""
    if (kp[shoulder_idx][2] <= _KPT_CONF_THRESHOLD
            or kp[hip_idx][2] <= _KPT_CONF_THRESHOLD
            or kp[knee_idx][2] <= _KPT_CONF_THRESHOLD):
        return None
    return _angle_deg(kp[shoulder_idx][:2], kp[hip_idx][:2], kp[knee_idx][:2])


def _hip_knee_tilt(kp: np.ndarray, hip_idx: int, knee_idx: int) -> float | None:
    """엉덩이->무릎 방향이 수직축과 이루는 각도(도). 0=수직(다리 곧게 아래로),
    90=수평(허벅지가 앞으로 눕혀짐). 발목 없이 엉덩이/무릎만으로 대략적인 다리 굽힘을 추정."""
    if kp[hip_idx][2] <= _KPT_CONF_THRESHOLD or kp[knee_idx][2] <= _KPT_CONF_THRESHOLD:
        return None
    hip_x, hip_y = kp[hip_idx][:2]
    knee_x, knee_y = kp[knee_idx][:2]
    dx, dy = abs(knee_x - hip_x), abs(knee_y - hip_y)
    if dx < 1e-6 and dy < 1e-6:
        return None
    return float(np.degrees(np.arctan2(dx, dy)))


def _hip_below_ratio(kp: np.ndarray, box: tuple[float, float, float, float]) -> float | None:
    """(bbox 하단 - 엉덩이y) / 상체길이(어깨-엉덩이). 무릎 없이 어깨+엉덩이만으로 판정.

    서 있으면 다리 전체(대개 상체보다 긴 구간)가 bbox 안에 보여서 이 값이 크고,
    앉아있으면 다리가 책상/의자에 금방 가려져 엉덩이 아래로 남는 bbox가 짧아 값이 작다.
    """
    shoulder_ys = [kp[i][1] for i in (_L_SHOULDER, _R_SHOULDER) if kp[i][2] > _KPT_CONF_THRESHOLD]
    hip_ys = [kp[i][1] for i in (_L_HIP, _R_HIP) if kp[i][2] > _KPT_CONF_THRESHOLD]
    if not shoulder_ys or not hip_ys:
        return None
    shoulder_y = sum(shoulder_ys) / len(shoulder_ys)
    hip_y = sum(hip_ys) / len(hip_ys)
    torso_len = hip_y - shoulder_y
    if torso_len <= 1e-3:
        return None
    _x1, _y1, _x2, y2 = box
    return (y2 - hip_y) / torso_len


def _classify_posture(kp: np.ndarray | None, box: tuple[float, float, float, float]) -> tuple[str, str]:
    """(posture, source) 반환. posture: "sitting"/"standing".
    source: "knee_angle" / "hip_angle" / "hip_knee_tilt" / "hip_below_ratio" / "aspect_ratio"."""
    if kp is not None:
        angles = [a for a in (
            _leg_angle(kp, _L_HIP, _L_KNEE, _L_ANKLE),
            _leg_angle(kp, _R_HIP, _R_KNEE, _R_ANKLE),
        ) if a is not None]
        if angles:
            avg_angle = sum(angles) / len(angles)
            posture = "standing" if avg_angle >= _KNEE_STRAIGHT_ANGLE else "sitting"
            return posture, "knee_angle"

        hip_angles = [a for a in (
            _hip_angle(kp, _L_SHOULDER, _L_HIP, _L_KNEE),
            _hip_angle(kp, _R_SHOULDER, _R_HIP, _R_KNEE),
        ) if a is not None]
        if hip_angles:
            avg_hip_angle = sum(hip_angles) / len(hip_angles)
            posture = "standing" if avg_hip_angle >= _HIP_STRAIGHT_ANGLE else "sitting"
            return posture, "hip_angle"

        tilts = [t for t in (
            _hip_knee_tilt(kp, _L_HIP, _L_KNEE),
            _hip_knee_tilt(kp, _R_HIP, _R_KNEE),
        ) if t is not None]
        if tilts:
            avg_tilt = sum(tilts) / len(tilts)
            posture = "sitting" if avg_tilt >= _HIP_KNEE_TILT_SITTING else "standing"
            return posture, "hip_knee_tilt"

        below_ratio = _hip_below_ratio(kp, box)
        if below_ratio is not None:
            posture = "standing" if below_ratio >= _VISIBLE_LEG_RATIO_STANDING else "sitting"
            return posture, "hip_below_ratio"

    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    ratio = h / w if w > 0 else 0.0
    posture = "sitting" if ratio < _ASPECT_SITTING_RATIO else "standing"
    return posture, "aspect_ratio"


def _is_sitting_by_pose(kps: np.ndarray | None, box: tuple[float, float, float, float]) -> bool:
    """COCO 17개 키포인트(없으면 bbox 비율)로 앉음/섬 판별. True=앉아있음."""
    posture, source = _classify_posture(kps, box)
    print(f"[pose] posture={posture} (source={source})")
    return posture == "sitting"


_POSE_MODEL_NAME = "yolo26x-pose"


def _run_seat_occupancy(frame: np.ndarray, camera, yolo_model: str = "yolov8x", conf_threshold: float | None = None) -> dict:
    """좌석 점유: Pose 모델 밴드 감지 + 앉음 판별."""
    seat_lines = getattr(camera, 'seat_lines', {}) or {}
    all_seat_ids = list(seat_lines.keys())

    occupied_set: set[str] = set()

    band_seats: dict[str, list] = {}
    for sid, line in seat_lines.items():
        pts = line if not isinstance(line, dict) else (line.get("points") or [])
        if pts and len(pts) >= 4:
            band_seats[sid] = pts

    # Pose 모델 실행 (없으면 일반 YOLO fallback)
    yolo_boxes: list[tuple[int, int, int, int]] = []
    person_centers: list[tuple[float, float]] = []
    sitting_flags: list[bool] = []  # 각 사람이 앉아있는지
    pose_result = None
    use_pose = False

    try:
        from app.services.real_detection import _get_yolo, _CONF_THRESH, infer_lock, yolo_device
        conf = conf_threshold if conf_threshold is not None else _CONF_THRESH
        try:
            pose_model = _get_yolo(_POSE_MODEL_NAME)
            use_pose = True
        except FileNotFoundError:
            pose_model = _get_yolo(yolo_model)

        with infer_lock:
            pose_result = pose_model(frame, verbose=False, device=yolo_device(), conf=conf, classes=[0], imgsz=640)[0]
        if pose_result.boxes is not None:
            min_h = frame.shape[0] * 0.05
            kps_data = pose_result.keypoints.data.cpu().numpy() if (use_pose and pose_result.keypoints is not None) else None
            for idx, box in enumerate(pose_result.boxes):
                x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())
                if (y2 - y1) < min_h:
                    continue
                yolo_boxes.append((int(x1), int(y1), int(x2), int(y2)))
                person_centers.append(((x1 + x2) / 2, (y1 + y2) / 2))
                kp = kps_data[idx] if (kps_data is not None and idx < len(kps_data)) else None
                sitting_flags.append(_is_sitting_by_pose(kp, (x1, y1, x2, y2)))
        mode = "Pose" if use_pose else "YOLO"
        sitting_count = sum(sitting_flags)
        print(f"[seat_occ] {mode} 감지: {len(yolo_boxes)}명 (앉음 {sitting_count}명)")
    except Exception as e:
        print(f"[seat_occ] 모델 실행 오류: {e}")

    pose_annotated = pose_result.plot() if (use_pose and pose_result is not None) else None

    # 4점 밴드: 앉아있는 사람의 중심점이 밴드 안에 있으면 점유
    if band_seats and person_centers:
        for sid, pts in band_seats.items():
            matched = [sitting_flags[i] for i, (cx, cy) in enumerate(person_centers) if _is_in_seat_band(cx, cy, pts)]
            if any(matched):
                occupied_set.add(sid)
        print(f"[seat_occ] 점유: {occupied_set}")

    occupied = [s for s in all_seat_ids if s in occupied_set]
    empty = [s for s in all_seat_ids if s not in occupied_set]

    # 결과 이미지: 포즈 스켈레톤(또는 bbox) + 좌석 선
    if use_pose and pose_result is not None:
        annotated = pose_annotated if pose_annotated is not None else pose_result.plot()
    else:
        annotated = frame.copy()
        for (bx1, by1, bx2, by2) in yolo_boxes:
            cv2.rectangle(annotated, (bx1, by1), (bx2, by2), (0, 220, 80), 2)
    if yolo_boxes:
        cv2.putText(annotated, f"{'Pose' if use_pose else 'YOLO'}: {len(yolo_boxes)}", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 80), 2)

    for seat_id, line in seat_lines.items():
        pts = line if not isinstance(line, dict) else (line.get("points") or [])
        if not pts or len(pts) < 2:
            continue
        is_occ = seat_id in occupied_set
        front_color = (0, 60, 220) if is_occ else (160, 160, 160)
        back_color  = (0, 150, 80) if is_occ else (120, 120, 120)
        p1 = (int(pts[0][0]), int(pts[0][1]))
        p2 = (int(pts[1][0]), int(pts[1][1]))
        cv2.line(annotated, p1, p2, front_color, 3)
        if len(pts) >= 4:
            p3 = (int(pts[2][0]), int(pts[2][1]))
            p4 = (int(pts[3][0]), int(pts[3][1]))
            cv2.line(annotated, p3, p4, back_color, 3)
            lx = (p1[0] + p2[0] + p3[0] + p4[0]) // 4
            ly = max((p1[1] + p2[1] + p3[1] + p4[1]) // 4 - 6, 12)
        else:
            lx, ly = p1[0] + 2, max(p1[1] - 4, 12)
        (tw, th), _ = cv2.getTextSize(seat_id, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(annotated, (lx - 2, ly - th - 3), (lx + tw + 2, ly + 3), (0, 0, 0), -1)
        cv2.putText(annotated, seat_id, (lx, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.55, front_color, 1)

    return {
        "occupied": occupied,
        "empty": empty,
        "total": len(all_seat_ids),
        "occupied_count": len(occupied),
        "image": _to_b64(annotated),
    }
