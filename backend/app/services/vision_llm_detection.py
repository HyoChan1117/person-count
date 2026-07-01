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


def _is_sitting_by_pose(kps, bbox_h: float, frame_h: float) -> bool:
    """COCO 17개 키포인트로 앉음/섬 판별. True=앉아있음.

    1순위: 전신 감지(어깨+엉덩이+무릎) → 각도 판별 (150° 이상 = 서있음)
    2순위: 어깨 감지 → 앉아있음 (머리+어깨 = 책상 앞에 앉아있음)
    3순위: 어깨 미감지(머리만) → 서있음 (멀리 서있음)
    """
    import math
    CONF = 0.25

    def avg_pt(indices):
        pts = [(kps[i][0], kps[i][1]) for i in indices if kps[i][2] > CONF]
        if not pts:
            return None
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    shoulder = avg_pt((5, 6))
    hip      = avg_pt((11, 12))
    knee     = avg_pt((13, 14))

    # 1순위: 전신 감지 → 어깨-엉덩이-무릎 각도 (150° 이상 = 서있음)
    if shoulder and hip and knee:
        v1 = (shoulder[0] - hip[0], shoulder[1] - hip[1])
        v2 = (knee[0]     - hip[0], knee[1]     - hip[1])
        mag1, mag2 = math.hypot(*v1), math.hypot(*v2)
        if mag1 > 0 and mag2 > 0:
            cos_a = max(-1.0, min(1.0, (v1[0]*v2[0] + v1[1]*v2[1]) / (mag1 * mag2)))
            angle = math.degrees(math.acos(cos_a))
            print(f"[pose] shoulder-hip-knee angle: {angle:.1f}°")
            return angle < 150

    # 2순위: 어깨 감지 → 앉아있음
    if shoulder:
        return True

    # 3순위: 어깨 미감지(머리만) → 서있음
    return False


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
        from app.services.real_detection import _get_yolo, _CONF_THRESH
        conf = conf_threshold if conf_threshold is not None else _CONF_THRESH
        try:
            if yolo_model == "medium":
                raise FileNotFoundError("medium 모드: pose 건너뜀")
            pose_model = _get_yolo(_POSE_MODEL_NAME)
            use_pose = True
        except FileNotFoundError:
            pose_model = _get_yolo(yolo_model)

        pose_result = pose_model(frame, verbose=False, conf=conf, classes=[0], imgsz=640)[0]
        if pose_result.boxes is not None:
            min_h = frame.shape[0] * 0.05
            kps_data = pose_result.keypoints.data.cpu().numpy() if (use_pose and pose_result.keypoints is not None) else None
            for idx, box in enumerate(pose_result.boxes):
                x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())
                if (y2 - y1) < min_h:
                    continue
                yolo_boxes.append((int(x1), int(y1), int(x2), int(y2)))
                person_centers.append(((x1 + x2) / 2, (y1 + y2) / 2))
                if kps_data is not None and idx < len(kps_data):
                    sitting_flags.append(_is_sitting_by_pose(kps_data[idx], y2 - y1, frame.shape[0]))
                else:
                    sitting_flags.append(True)
        mode = "Pose" if use_pose else "YOLO"
        sitting_count = sum(sitting_flags)
        print(f"[seat_occ] {mode} 감지: {len(yolo_boxes)}명 (앉음 {sitting_count}명)")
    except Exception as e:
        print(f"[seat_occ] 모델 실행 오류: {e}")

    pose_annotated = pose_result.plot() if (use_pose and pose_result is not None) else None

    # 4점 밴드: 앉아있는 사람의 중심점이 밴드 안에 있으면 점유
    near_set: set[str] = set()

    if band_seats and person_centers:
        for sid, pts in band_seats.items():
            matched = [sitting_flags[i] for i, (cx, cy) in enumerate(person_centers) if _is_in_seat_band(cx, cy, pts)]
            if matched:
                if any(matched):
                    occupied_set.add(sid)
                else:
                    near_set.add(sid)
        print(f"[seat_occ] 점유: {occupied_set}, 서있음(근접): {near_set}")

    occupied = [s for s in all_seat_ids if s in occupied_set]
    near = [s for s in all_seat_ids if s in near_set]
    empty = [s for s in all_seat_ids if s not in occupied_set and s not in near_set]

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
        is_near = seat_id in near_set
        front_color = (0, 60, 220) if is_occ else (0, 165, 255) if is_near else (160, 160, 160)
        back_color  = (0, 150, 80) if is_occ else (0, 120, 200) if is_near else (120, 120, 120)
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
        "near": near,
        "empty": empty,
        "total": len(all_seat_ids),
        "occupied_count": len(occupied),
        "image": _to_b64(annotated),
    }
