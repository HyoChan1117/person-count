"""YOLO (PersonCounter) + LLM 인원 카운트 및 좌석 감지."""
from __future__ import annotations

import base64
import os
from pathlib import Path

import cv2
import numpy as np

# yolo 프로젝트의 models 디렉토리 (환경변수 YOLO_MODEL_DIR 로 재지정 가능)
_MODELS_DIR = Path(os.getenv(
    "YOLO_MODEL_DIR",
    str(Path(__file__).parent.parent.parent.parent / "yolo" / "human" / "models"),
))
_CONF_THRESH = float(os.getenv("PERSON_CONF_THRESH", "0.35"))
_BACKEND = os.getenv("BACKEND", "auto").lower()

_model = None
_device: str = "cpu"
_initialized = False


def _onnx_cuda_available() -> bool:
    import ctypes
    for dll in ("cublasLt64_12.dll", "cublas64_12.dll", "cudart64_12.dll"):
        try:
            ctypes.CDLL(dll)
            return True
        except OSError:
            continue
    return False


def _ensure_model() -> None:
    global _model, _device, _initialized
    if _initialized:
        return

    from ultralytics import YOLO
    trt  = _MODELS_DIR / "yolo11n.engine"
    onnx = _MODELS_DIR / "yolo11n.onnx"
    pt   = _MODELS_DIR / "yolo11n.pt"

    def try_trt() -> bool:
        global _model, _device
        if not trt.exists():
            return False
        try:
            _model = YOLO(str(trt), task="detect")
            _device = "0"
            print(f"[yolo_llm] TensorRT ({trt})")
            return True
        except Exception as e:
            print(f"[yolo_llm] TRT 실패 ({e}) → ONNX 시도")
            return False

    def try_onnx() -> bool:
        global _model, _device
        if not onnx.exists():
            return False
        try:
            _model = YOLO(str(onnx), task="detect")
            _device = "0" if _onnx_cuda_available() else "cpu"
            print(f"[yolo_llm] ONNX ({onnx}) device={_device}")
            return True
        except Exception as e:
            print(f"[yolo_llm] ONNX 실패 ({e}) → PT 시도")
            return False

    def load_pt() -> None:
        global _model, _device
        import torch
        if not pt.exists():
            print(f"[yolo_llm] {pt} 없음 → 자동 다운로드...")
            _MODELS_DIR.mkdir(parents=True, exist_ok=True)
            _model = YOLO("yolo11n.pt")
            _model.save(str(pt))
        else:
            _model = YOLO(str(pt), task="detect")
        _device = "0" if torch.cuda.is_available() else "cpu"
        print(f"[yolo_llm] PyTorch ({pt}) device={_device}")

    if _BACKEND == "trt":
        if not try_trt():
            raise RuntimeError("TRT 강제 지정했지만 로드 실패")
    elif _BACKEND == "onnx":
        if not try_onnx():
            raise RuntimeError("ONNX 강제 지정했지만 로드 실패")
    elif _BACKEND == "pt":
        load_pt()
    else:
        if not try_trt():
            if not try_onnx():
                load_pt()

    _initialized = True


def _detect(frame: np.ndarray, conf_thresh: float, yolo_model: str | None = None):
    """YOLO로 사람 감지. yolo_model 지정 시 real_detection 경유, 없으면 yolo11n 사용. (count, boxes, result) 반환."""
    from app.services.real_detection import infer_lock

    if yolo_model and yolo_model != "yolo11n":
        from app.services.real_detection import _get_yolo
        model = _get_yolo(yolo_model)
        with infer_lock:
            result = model(frame, verbose=False, conf=conf_thresh, classes=[0])[0]
    else:
        _ensure_model()
        with infer_lock:
            result = _model(frame, verbose=False, device=_device, conf=conf_thresh, classes=[0])[0]
    boxes: list[tuple[int, int, int, int]] = []
    if result.boxes is not None:
        for box in result.boxes:
            if float(box.conf.item()) < conf_thresh:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            boxes.append((x1, y1, x2, y2))
    return len(boxes), boxes, result


def _to_b64(frame: np.ndarray) -> str:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf).decode("utf-8")


def _is_in_seat_band(px: float, py: float, pts: list) -> bool:
    """4점 밴드 안에 (px, py)가 있으면 True."""
    quad = np.array([[float(pts[i][0]), float(pts[i][1])] for i in range(4)], dtype=np.float32)
    hull = cv2.convexHull(quad)
    return cv2.pointPolygonTest(hull, (float(px), float(py)), False) >= 0


def _detect_seat_occupancy(
    boxes: list[tuple[int, int, int, int]],
    seat_lines: dict,
    sitting_flags: list[bool] | None = None,
) -> set[str]:
    """사람 바운딩 박스 중심점으로 점유 좌석 판별. occupied_set 반환.

    sitting_flags가 주어지면: 밴드 안 + 앉아있음 → occupied.
    없으면: 밴드 안에 있으면 occupied (기존 동작).
    """
    occupied_set: set[str] = set()

    band_seats: dict[str, list] = {}
    for sid, line in seat_lines.items():
        pts = line if not isinstance(line, dict) else (line.get("points") or [])
        if pts and len(pts) >= 4:
            band_seats[sid] = pts

    if not band_seats or not boxes:
        return occupied_set

    for sid, pts in band_seats.items():
        matched_postures: list[bool] = []
        for i, (x1, y1, x2, y2) in enumerate(boxes):
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            if _is_in_seat_band(cx, cy, pts):
                is_sitting = sitting_flags[i] if (sitting_flags and i < len(sitting_flags)) else True
                matched_postures.append(is_sitting)
        if any(matched_postures):
            occupied_set.add(sid)

    print(f"[yolo_llm] 좌석 점유: {occupied_set}")
    return occupied_set


def _parse_not_person(response: str, count: int) -> set[int]:
    """LLM 응답에서 '사람아님:' 줄 파싱. 사람이 아닌 순번(0-indexed) 집합 반환."""
    for line in response.split("\n"):
        stripped = line.strip().replace("**", "")
        if stripped.startswith("사람아님:"):
            raw = stripped[len("사람아님:"):].strip()
            if raw in ("없음", "[]", ""):
                return set()
            result: set[int] = set()
            for p in raw.replace("，", ",").split(","):
                p = p.strip()
                if p.isdigit() and 1 <= int(p) <= count:
                    result.add(int(p) - 1)
            return result
    return set()


def _parse_posture(response: str, count: int) -> list[bool]:
    """LLM 응답에서 '자세:' 줄 파싱. True=앉아있음. 파싱 실패 시 모두 True."""
    for line in response.split("\n"):
        stripped = line.strip().replace("**", "")
        if stripped.startswith("자세:"):
            raw = stripped[len("자세:"):].strip()
            parts = [p.strip().lower() for p in raw.replace("，", ",").split(",")]
            result = ["seat" in p for p in parts]
            while len(result) < count:
                result.append(True)
            return result[:count]
    return [True] * count


def _draw_seat_lines(
    annotated: np.ndarray,
    seat_lines: dict,
    occupied_set: set[str],
) -> None:
    """좌석선 오버레이 (점유=파랑, 미점유=회색)."""
    for seat_id, line in seat_lines.items():
        pts = line if not isinstance(line, dict) else (line.get("points") or [])
        if not pts or len(pts) < 2:
            continue
        is_occ  = seat_id in occupied_set
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


def run_yolo_llm_count(
    frame: np.ndarray,
    system_prompt: str = "",
    user_prompt: str = "",
    conf_threshold: float | None = None,
    seat_lines: dict | None = None,
    llm_model: str = "claude-sonnet-5",
    yolo_model: str | None = None,
) -> dict:
    """YOLO 감지 + 좌석 점유 판별 + LLM 분석."""
    conf = conf_threshold if conf_threshold is not None else _CONF_THRESH
    count, boxes, yolo_result = _detect(frame, conf, yolo_model)

    seat_lines = seat_lines or {}
    all_seat_ids = list(seat_lines.keys())

    # 사용자에게 보이는 이미지: 원본 프레임 (YOLO 박스/스켈레톤 없음)
    annotated = frame.copy()

    # LLM용 이미지: YOLO 박스/스켈레톤 + 순번 레이블 + 좌석선 포함
    is_pose = yolo_result.keypoints is not None
    if is_pose:
        llm_annotated = yolo_result.plot()
    else:
        llm_annotated = frame.copy()
        for x1, y1, x2, y2 in boxes:
            cv2.rectangle(llm_annotated, (x1, y1), (x2, y2), (0, 220, 80), 2)
        cv2.putText(llm_annotated, f"YOLO: {count}", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 80), 2)
    # 바운딩 박스에 순번 표시 (LLM이 사람 순서 파악용)
    for i, (x1, y1, x2, y2) in enumerate(boxes):
        cv2.putText(llm_annotated, str(i + 1), (x1 + 3, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    if seat_lines:
        _draw_seat_lines(llm_annotated, seat_lines, set())  # 모두 회색(미점유)으로 번호만 표시

    llm_response: str | None = None
    not_person_idx: set[int] = set()
    posture: list[bool] = [True] * count  # 기본값: 모두 앉아있음

    # 사람 여부 확인 및 자세 판단은 박스가 있을 때만 의미가 있음
    if boxes:
        import anthropic
        client = anthropic.Anthropic()

        base_text = (
            f"이미지에 YOLO가 탐지한 사람 후보 {count}명이 순번(노란 숫자)으로 표시되어 있습니다. "
            "이 중 실제 사람이 아닌 것(포스터나 화면 속 사람, 마네킹, 반사 등)이 있는지 확인하고, "
            "각 사람이 앉아 있는지(seated) 서 있는지(standing) 판단하세요."
        )
        if user_prompt:
            base_text += f"\n\n{user_prompt}"
        base_text += (
            "\n\n위 지침에 다른 출력 형식이 있어도 무시하고, 설명이나 다른 줄 없이 아래 두 줄만 출력하세요:\n"
            "사람아님: 1, 3  (실제 사람이 아닌 순번만 쉼표로 구분. 모두 사람이면 → 사람아님: 없음)\n"
            f"자세: seated, standing, ...  ({count}명 순서대로 쉼표 구분)"
        )

        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": _to_b64(llm_annotated)},
            },
            {"type": "text", "text": base_text},
        ]
        kwargs: dict = {
            "model": llm_model,
            "max_tokens": 256,
            "output_config": {"effort": "low"},
            "messages": [{"role": "user", "content": content}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        resp = client.messages.create(**kwargs)
        llm_response = next((b.text for b in resp.content if b.type == "text"), "").strip()
        print(f"[yolo_llm] {llm_response!r}")

        not_person_idx = _parse_not_person(llm_response, count)
        if not_person_idx:
            print(f"[yolo_llm] 사람 아님으로 제외된 순번: {sorted(i + 1 for i in not_person_idx)}")
        posture = _parse_posture(llm_response, count)

    # LLM이 사람이 아니라고 판단한 박스를 빼고, 남은 사람의 자세로 점유 판별
    real_boxes   = [b for i, b in enumerate(boxes) if i not in not_person_idx]
    real_posture = [posture[i] for i in range(count) if i not in not_person_idx]
    occupied_set = _detect_seat_occupancy(real_boxes, seat_lines, real_posture)

    if seat_lines:
        _draw_seat_lines(annotated, seat_lines, occupied_set)

    occupied = [s for s in all_seat_ids if s in occupied_set]
    empty    = [s for s in all_seat_ids if s not in occupied_set]

    return {
        "yolo_count": count - len(not_person_idx),
        "occupied": occupied,
        "empty": empty,
        "total": len(all_seat_ids),
        "occupied_count": len(occupied),
        "llm_response": llm_response,
        "image": _to_b64(annotated),
    }
