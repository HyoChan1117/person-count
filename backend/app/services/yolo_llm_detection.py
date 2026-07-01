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
    if yolo_model and yolo_model != "yolo11n":
        from app.services.real_detection import _get_yolo
        model = _get_yolo(yolo_model)
        result = model(frame, verbose=False, conf=conf_thresh, classes=[0])[0]
    else:
        _ensure_model()
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
) -> tuple[set[str], set[str]]:
    """사람 바운딩 박스 중심점으로 점유 좌석 판별. (occupied_set, near_set) 반환.

    sitting_flags가 주어지면: 밴드 안 + 앉아있음 → occupied, 밴드 안 + 서있음 → near.
    없으면: 밴드 안에 있으면 occupied (기존 동작).
    """
    occupied_set: set[str] = set()
    near_set: set[str] = set()

    band_seats: dict[str, list] = {}
    for sid, line in seat_lines.items():
        pts = line if not isinstance(line, dict) else (line.get("points") or [])
        if pts and len(pts) >= 4:
            band_seats[sid] = pts

    if not band_seats or not boxes:
        return occupied_set, near_set

    for sid, pts in band_seats.items():
        matched_postures: list[bool] = []
        for i, (x1, y1, x2, y2) in enumerate(boxes):
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            if _is_in_seat_band(cx, cy, pts):
                is_sitting = sitting_flags[i] if (sitting_flags and i < len(sitting_flags)) else True
                matched_postures.append(is_sitting)
        if matched_postures:
            if any(matched_postures):
                occupied_set.add(sid)
            else:
                near_set.add(sid)

    print(f"[yolo_llm] 좌석 점유: {occupied_set}, 근접(서있음): {near_set}")
    return occupied_set, near_set


def _parse_posture_from_llm(response: str, count: int) -> list[bool]:
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
    near_set: set[str],
) -> None:
    """좌석선 오버레이 (점유=파랑, 근접=주황, 미점유=회색)."""
    for seat_id, line in seat_lines.items():
        pts = line if not isinstance(line, dict) else (line.get("points") or [])
        if not pts or len(pts) < 2:
            continue
        is_occ  = seat_id in occupied_set
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


def _parse_exclusions_from_prompt(prompt: str) -> list[str]:
    """user_prompt의 # 카운트 제외 대상 섹션에서 항목 추출."""
    header = "# 카운트 제외 대상"
    idx = prompt.find(header)
    if idx == -1:
        return []
    exclusions = []
    for line in prompt[idx + len(header):].split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            exclusions.append(stripped[2:].strip())
        elif stripped.startswith("#"):
            break
    return exclusions


def _parse_confirmed_seats(response: str) -> list[str] | None:
    """LLM 응답에서 '확정점유:' 줄 파싱. 여러 개이면 마지막 줄 사용. 없으면 None."""
    last_raw: str | None = None
    for line in response.split("\n"):
        stripped = line.strip().replace("**", "")
        if stripped.startswith("확정점유:"):
            last_raw = stripped[len("확정점유:"):].strip()
    if last_raw is None:
        return None
    if last_raw in ("없음", "[]", ""):
        return []
    return [s.strip() for s in last_raw.replace("，", ",").split(",") if s.strip()]


def run_yolo_llm_count(
    frame: np.ndarray,
    system_prompt: str = "",
    user_prompt: str = "",
    conf_threshold: float | None = None,
    seat_lines: dict | None = None,
    llm_model: str = "claude-haiku-4-5-20251001",
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
        _draw_seat_lines(llm_annotated, seat_lines, set(), set())  # 모두 회색(미점유)으로 번호만 표시

    llm_response: str | None = None
    sitting_flags: list[bool] = [True] * count  # LLM 판단 전 기본값: 모두 앉아있음

    # seat_lines가 있거나 user_prompt가 있으면 LLM 호출
    if seat_lines or user_prompt:
        import anthropic
        client = anthropic.Anthropic()

        # 초기 점유 후보: sitting_flags 없이 기하학적으로만 계산 (seat_info용)
        _geo_occupied, _ = _detect_seat_occupancy(boxes, seat_lines)
        candidate_occupied_geo = [s for s in all_seat_ids if s in _geo_occupied]
        candidate_empty_geo    = [s for s in all_seat_ids if s not in _geo_occupied]

        seat_info = ""
        if all_seat_ids:
            seat_info = (
                f"\nYOLO 점유 후보 좌석: {', '.join(candidate_occupied_geo) or '없음'}"
                f" ({len(candidate_occupied_geo)}/{len(all_seat_ids)}석)"
                f"\n미점유 좌석: {', '.join(candidate_empty_geo) or '없음'}"
            )

        # user_prompt에 자세 판단 기준이 없을 때 폴백. 형식 요청은 항상 포함.
        _has_posture_guide = user_prompt and ("seated" in user_prompt or "앉" in user_prompt)
        _posture_body = "" if _has_posture_guide else "각 사람이 좌석에 앉아 있는지(seated), 서 있는지(standing) 판단하세요. "
        posture_instruction = (
            f"\n\n이미지에 YOLO가 탐지한 {count}명의 사람이 순번(노란 숫자)으로 표시되어 있습니다. "
            f"{_posture_body}"
            "설명·분석·근거 없이 아래 형식만 출력하세요:\n"
            f"자세: seated, standing, ...  ({count}명 순서대로 쉼표 구분)"
        )

        # 제외 대상이 설정돼 있으면 LLM에게 확정 점유 출력 요청
        exclusions = _parse_exclusions_from_prompt(user_prompt) if user_prompt else []
        verification_note = ""
        if exclusions and all_seat_ids:
            verification_note = (
                "\n\n위의 제외 대상을 적용해 실제 착석한 사람이 있는 좌석만 확정하세요. "
                "설명 없이 마지막 줄에 형식만 출력하세요:\n"
                "확정점유: 좌석번호1, 좌석번호2  (착석자 없으면 → 확정점유: 없음)"
            )

        base_text = f"YOLO 감지 인원: {count}명{seat_info}"
        if user_prompt:
            base_text += f"\n\n{user_prompt}"
        base_text += posture_instruction + verification_note

        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": _to_b64(llm_annotated)},
            },
            {"type": "text", "text": base_text},
        ]
        kwargs: dict = {
            "model": llm_model,
            "max_tokens": 512,
            "messages": [{"role": "user", "content": content}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        resp = client.messages.create(**kwargs)
        llm_response = resp.content[0].text.strip()
        print(f"[yolo_llm] {llm_response!r}")

        # LLM 자세 판단 파싱
        sitting_flags = _parse_posture_from_llm(llm_response, count)
        sitting_count = sum(sitting_flags)
        print(f"[yolo_llm] 자세 판단: {count}명 중 {sitting_count}명 앉음, {count - sitting_count}명 서있음")

    # sitting_flags 기반으로 점유/근접 판별
    occupied_set, near_set = _detect_seat_occupancy(boxes, seat_lines, sitting_flags)
    confirmed_occupied_set = occupied_set

    # 제외 대상 있을 때 LLM 확정 점유로 덮어쓰기
    if llm_response and seat_lines:
        exclusions = _parse_exclusions_from_prompt(user_prompt) if user_prompt else []
        if exclusions and all_seat_ids:
            confirmed = _parse_confirmed_seats(llm_response)
            if confirmed is not None:
                valid_ids = set(all_seat_ids)
                confirmed_occupied_set = {s for s in confirmed if s in valid_ids}
                invalid = [s for s in confirmed if s not in valid_ids]
                if invalid:
                    print(f"[yolo_llm] 유효하지 않은 좌석 ID 무시: {invalid}")
                print(f"[yolo_llm] LLM 확정 점유: {confirmed_occupied_set}")

    # LLM 확정 결과로 좌석 오버레이 그리기
    if seat_lines:
        _draw_seat_lines(annotated, seat_lines, confirmed_occupied_set, near_set)

    occupied = [s for s in all_seat_ids if s in confirmed_occupied_set]
    near     = [s for s in all_seat_ids if s in near_set and s not in confirmed_occupied_set]
    empty    = [s for s in all_seat_ids if s not in confirmed_occupied_set and s not in near_set]

    return {
        "yolo_count": count,
        "occupied": occupied,
        "near": near,
        "empty": empty,
        "total": len(all_seat_ids),
        "occupied_count": len(occupied),
        "llm_response": llm_response,
        "image": _to_b64(annotated),
    }
