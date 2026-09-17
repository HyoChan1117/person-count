"""실시간 YOLO 탐지 MJPEG 스트리밍.

원본 캡처(수십 ms)와 YOLO 추론(모델·GPU 부하에 따라 수십~수백 ms)의 속도 차이 때문에
매 프레임마다 "캡처 → 추론 → 인코딩 → 전송"을 동기적으로 반복하면 프레임 간격이
들쭉날쭉해져 화면이 끊겨 보인다. 카메라별로 백그라운드 스레드에서 자신의 속도대로
계속 추론하며 최신 결과 프레임만 캐시해 두고, 스트리밍 쪽은 그 캐시를 일정한 주기로
읽어 전송해 추론 속도와 무관하게 매끄러운 프레임 간격을 유지한다. 같은 카메라를 여러
탭/카드에서 동시에 보더라도 추론은 한 번만 수행되도록 워커를 참조 카운트로 공유한다.

워커 스레드가 모델 로드 실패나 RTSP 장애로 프레임을 한 장도 만들지 못하면 스트림이
영원히 빈 상태로 매달릴 수 있으므로, 그 사이에는 "연결 중.../오류" 플레이스홀더
프레임을 대신 내보내 최소한 화면이 응답하도록 한다.
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time

import cv2
import numpy as np
from fastapi import Request

from app.services.frame_capture import capture_rtsp_frame
from app.services.real_detection import _get_yolo, infer_lock

logger = logging.getLogger(__name__)

_BOUNDARY = b"--frame"
_EMIT_INTERVAL = 0.05  # 전송 주기: 추론보다 촘촘히 확인해 새 프레임이 나오는 즉시 내보낸다
_INFER_INTERVAL = 0.066  # 추론 최소 간격(약 15fps): 이게 없으면 워커가 쉬지 않고 GPU를 점유해 다른 YOLO 요청까지 지연됨
_JPEG_QUALITY = 75


def _placeholder_jpeg(text: str) -> bytes:
    img = np.zeros((360, 640, 3), dtype=np.uint8)
    cv2.putText(img, text, (16, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY])
    return buf.tobytes() if ok else b""


_CONNECTING_JPEG = _placeholder_jpeg("connecting...")
_ERROR_JPEG = _placeholder_jpeg("live view error")


class _LiveWorker:
    """카메라 1대에 대해 지속적으로 YOLO 추론을 수행하며 최신 인코딩된 프레임만 보관."""

    def __init__(self, rtsp_url: str, model_name: str, conf_threshold: float):
        self.rtsp_url = rtsp_url
        self.model_name = model_name
        self.conf_threshold = conf_threshold
        self._jpeg: bytes = _CONNECTING_JPEG
        self._lock = threading.Lock()
        self._viewers = 0
        self._stop = False
        self._thread = threading.Thread(target=self._run_safe, daemon=True)
        self._thread.start()

    def _run_safe(self):
        try:
            self._run()
        except Exception:
            logger.exception("[live_stream] 워커 종료됨 (rtsp=%s, model=%s)", self.rtsp_url, self.model_name)
            with self._lock:
                self._jpeg = _ERROR_JPEG

    def _run(self):
        model = _get_yolo(self.model_name)
        while not self._stop:
            t0 = time.monotonic()
            frame = capture_rtsp_frame(self.rtsp_url, timeout_ms=2000)
            if frame is None:
                time.sleep(0.3)
                continue
            try:
                with infer_lock:
                    result = model.predict(frame, conf=self.conf_threshold, classes=[0], verbose=False)[0]
                annotated = result.plot()
                count = int((result.boxes.cls == 0).sum()) if result.boxes is not None else 0
                cv2.rectangle(annotated, (0, 0), (150, 28), (0, 0, 0), -1)
                cv2.putText(annotated, f"person: {count}", (8, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            except Exception:
                logger.exception("[live_stream] 추론 오류 (rtsp=%s)", self.rtsp_url)
                annotated = frame
            try:
                ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY])
                if ok:
                    with self._lock:
                        self._jpeg = buf.tobytes()
            except Exception:
                logger.exception("[live_stream] 인코딩 오류 (rtsp=%s)", self.rtsp_url)
            elapsed = time.monotonic() - t0
            time.sleep(max(0.0, _INFER_INTERVAL - elapsed))

    def get_jpeg(self) -> bytes:
        with self._lock:
            return self._jpeg

    def acquire(self) -> None:
        with self._lock:
            self._viewers += 1

    def release(self) -> int:
        with self._lock:
            self._viewers -= 1
            return self._viewers

    def stop(self) -> None:
        self._stop = True


_workers: dict[tuple[str, str, float], _LiveWorker] = {}
_workers_lock = threading.Lock()


def _acquire_worker(key: tuple[str, str, float]) -> _LiveWorker:
    with _workers_lock:
        worker = _workers.get(key)
        if worker is None:
            worker = _LiveWorker(*key)
            _workers[key] = worker
        worker.acquire()
        return worker


def _release_worker(key: tuple[str, str, float], worker: _LiveWorker) -> None:
    if worker.release() <= 0:
        with _workers_lock:
            if _workers.get(key) is worker:
                del _workers[key]
        worker.stop()


async def mjpeg_stream(request: Request, rtsp_url: str, model_name: str, conf_threshold: float):
    """클라이언트가 연결을 끊을 때까지 워커의 최신 프레임(또는 플레이스홀더)을 일정 주기로 전송한다."""
    key = (rtsp_url, model_name, conf_threshold)
    worker = _acquire_worker(key)
    last_sent: bytes | None = None
    try:
        while True:
            if await request.is_disconnected():
                break
            jpg = worker.get_jpeg()
            if jpg is not last_sent:
                yield (
                    _BOUNDARY + b"\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: " + str(len(jpg)).encode() + b"\r\n\r\n" +
                    jpg + b"\r\n"
                )
                last_sent = jpg
            await asyncio.sleep(_EMIT_INTERVAL)
    finally:
        _release_worker(key, worker)
