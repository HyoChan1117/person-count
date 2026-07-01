"""배경 차분(Background Subtraction) 기반 인원 유무 감지."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

_REFERENCE_DIR = Path(__file__).parent.parent.parent / "data" / "bg_references"
_REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

# 픽셀 차이 임계값 (0~255), 이 값 이상 차이나는 픽셀을 "변화"로 판단
_PIXEL_THRESH = 30
# 전체 픽셀 중 변화된 비율이 이 값 이상이면 "사람 있음"으로 판단 (2% = 0.02)
_CHANGE_RATIO_THRESH = 0.02


def _ref_path(camera_id: str) -> Path:
    return _REFERENCE_DIR / f"{camera_id}.jpg"


def _meta_path(camera_id: str) -> Path:
    return _REFERENCE_DIR / f"{camera_id}_meta.json"


def save_reference(camera_id: str, frame: np.ndarray) -> None:
    """현재 프레임을 해당 카메라의 빈 강의실 기준으로 저장."""
    cv2.imwrite(str(_ref_path(camera_id)), frame)
    meta = {"width": frame.shape[1], "height": frame.shape[0]}
    _meta_path(camera_id).write_text(json.dumps(meta))


def has_reference(camera_id: str) -> bool:
    return _ref_path(camera_id).exists()


def detect_occupied(camera_id: str, frame: np.ndarray) -> dict:
    """
    기준 프레임과 현재 프레임을 비교해 사람 유무를 반환.

    Returns:
        {
            "occupied": bool,
            "change_ratio": float,   # 변화된 픽셀 비율 (0.0 ~ 1.0)
            "has_reference": bool,
        }
    """
    if not has_reference(camera_id):
        return {"occupied": None, "change_ratio": None, "has_reference": False}

    ref = cv2.imread(str(_ref_path(camera_id)))

    # 크기가 다르면 현재 프레임을 기준 크기로 리사이즈
    if ref.shape != frame.shape:
        frame = cv2.resize(frame, (ref.shape[1], ref.shape[0]))

    # 그레이스케일로 변환 후 차이 계산
    ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 노이즈 제거를 위한 블러
    ref_gray = cv2.GaussianBlur(ref_gray, (21, 21), 0)
    frame_gray = cv2.GaussianBlur(frame_gray, (21, 21), 0)

    diff = cv2.absdiff(ref_gray, frame_gray)
    _, thresh = cv2.threshold(diff, _PIXEL_THRESH, 255, cv2.THRESH_BINARY)

    total_pixels = thresh.size
    changed_pixels = int(np.count_nonzero(thresh))
    change_ratio = changed_pixels / total_pixels

    return {
        "occupied": change_ratio >= _CHANGE_RATIO_THRESH,
        "change_ratio": round(change_ratio, 4),
        "has_reference": True,
    }
