"""ArcFace(insightface) 임베딩 기반 얼굴 등록/매칭.

모델은 처음 필요할 때만 로드한다 — 서버 기동만으로 수백 MB를 점유하지 않도록.
임베딩은 512차원 L2 정규화 벡터라 코사인 유사도가 내적 한 번으로 계산된다.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path

import numpy as np

_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "face"
_EMBEDDINGS_PATH = _DATA_DIR / "embeddings.npz"

MODEL_NAME = "buffalo_l"
# 검출 입력 크기. 2560x1440 프레임을 640으로 줄이면 멀리 앉은 사람의 얼굴이 20px 수준으로
# 뭉개져 검출 자체가 안 된다. 1024로 올리면 그만큼 살아남는다 (GPU라 비용은 수십 ms 수준).
DET_SIZE = (1024, 1024)
MATCH_THRESHOLD = 0.45   # 코사인 유사도. 이보다 높으면 동일인으로 판정
MIN_DET_SCORE = 0.5      # 이보다 낮은 검출 신뢰도는 무시

_app = None
_app_lock = threading.Lock()


def _enable_cudnn_lookup() -> None:
    """onnxruntime이 torch와 함께 설치된 cuDNN DLL을 찾게 한다.

    ORT는 cuDNN을 기본 DLL 경로에서만 찾기 때문에, 이게 없으면 CUDA provider가
    cudnn64_9.dll을 못 찾았다는 경고를 매번 남긴다 (Windows 전용).
    """
    if not hasattr(os, "add_dll_directory"):
        return
    try:
        import torch
        lib_dir = Path(torch.__file__).parent / "lib"
        if lib_dir.exists():
            os.add_dll_directory(str(lib_dir))
    except Exception:
        pass


def _get_app():
    """insightface FaceAnalysis를 최초 요청 시 1회만 로드한다."""
    global _app
    if _app is not None:
        return _app
    with _app_lock:
        if _app is None:
            _enable_cudnn_lookup()
            from insightface.app import FaceAnalysis
            # insightface는 INSIGHTFACE_HOME 환경변수를 보지 않고 root 인자만 쓴다.
            # 명시하지 않으면 컨테이너 안 ~/.insightface에 매번 280MB를 새로 받는다.
            app = FaceAnalysis(
                name=MODEL_NAME,
                root=os.getenv("INSIGHTFACE_HOME", "~/.insightface"),
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
            )
            app.prepare(ctx_id=0, det_size=DET_SIZE)
            _app = app
    return _app


def providers() -> list[str]:
    """실제로 사용 중인 실행 제공자(GPU/CPU 확인용)."""
    app = _get_app()
    return sorted({m.session.get_providers()[0] for m in app.models.values()})


# ── 검출 ─────────────────────────────────────────────────────────────────────

def detect(bgr_image: np.ndarray) -> list:
    """검출 신뢰도가 충분한 얼굴만 반환."""
    return [f for f in _get_app().get(bgr_image) if f.det_score >= MIN_DET_SCORE]


def largest_face(bgr_image: np.ndarray):
    faces = detect(bgr_image)
    if not faces:
        return None
    return max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))


# ── 저장소 ───────────────────────────────────────────────────────────────────

def _load() -> tuple[list[str], np.ndarray]:
    if not _EMBEDDINGS_PATH.exists():
        return [], np.zeros((0, 512), dtype=np.float32)
    data = np.load(_EMBEDDINGS_PATH, allow_pickle=True)
    return list(data["names"]), data["embeddings"].astype(np.float32)


def _save(names: list[str], embeddings: np.ndarray) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(_EMBEDDINGS_PATH, names=np.array(names, dtype=object), embeddings=embeddings)


def enrolled_names() -> list[str]:
    return _load()[0]


# ── 등록 / 매칭 ──────────────────────────────────────────────────────────────

def enroll(name: str, bgr_images: list[np.ndarray]) -> int:
    """여러 장에서 얼굴 임베딩을 뽑아 평균낸 뒤 등록/갱신. 얼굴을 찾은 장수 반환."""
    vectors = []
    for img in bgr_images:
        face = largest_face(img)
        if face is not None:
            vectors.append(face.normed_embedding)

    if not vectors:
        raise ValueError("사진에서 얼굴을 찾지 못했습니다")

    mean_vec = np.mean(vectors, axis=0)
    mean_vec = mean_vec / np.linalg.norm(mean_vec)

    names, embeddings = _load()
    if name in names:
        embeddings[names.index(name)] = mean_vec
    else:
        names.append(name)
        embeddings = np.vstack([embeddings, mean_vec[None, :]])

    _save(names, embeddings)
    return len(vectors)


def remove(name: str) -> bool:
    names, embeddings = _load()
    if name not in names:
        return False
    idx = names.index(name)
    names.pop(idx)
    _save(names, np.delete(embeddings, idx, axis=0))
    return True


def match(embedding: np.ndarray, threshold: float | None = None) -> tuple[str | None, float]:
    """가장 유사한 등록 인물과 코사인 유사도. 임계값 미만이면 (None, 유사도)."""
    threshold = MATCH_THRESHOLD if threshold is None else threshold
    names, embeddings = _load()
    if not names:
        return None, 0.0

    sims = embeddings @ embedding
    best = int(np.argmax(sims))
    score = float(sims[best])
    return (names[best], score) if score >= threshold else (None, score)
