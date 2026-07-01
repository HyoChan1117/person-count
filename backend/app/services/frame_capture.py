"""RTSP 프레임 캡처 유틸리티."""
from __future__ import annotations

import base64
import threading
import time
from typing import Optional

import cv2
import numpy as np


class _RTSPGrabber:
    """백그라운드 스레드로 RTSP 스트림을 지속 수신하여 최신 프레임을 보관."""

    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url
        self._frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while True:
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                with self._lock:
                    self._frame = frame
            cap.release()
            time.sleep(1)  # 재연결 대기

    def get(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._frame.copy() if self._frame is not None else None


_grabbers: dict[str, _RTSPGrabber] = {}
_grabbers_lock = threading.Lock()


def _get_grabber(rtsp_url: str) -> _RTSPGrabber:
    with _grabbers_lock:
        if rtsp_url not in _grabbers:
            _grabbers[rtsp_url] = _RTSPGrabber(rtsp_url)
        return _grabbers[rtsp_url]


def capture_rtsp_frame(rtsp_url: str, timeout_ms: int = 15000) -> Optional[np.ndarray]:
    grabber = _get_grabber(rtsp_url)
    # 최초 연결 시 프레임이 없으면 잠시 대기
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        frame = grabber.get()
        if frame is not None:
            return frame
        time.sleep(0.1)
    return None


def capture_rtsp_frames_parallel(cameras, timeout_ms: int = 15000) -> list[tuple]:
    """모든 카메라 grabber를 동시에 warm-up 후 동일 시점 스냅샷 반환."""
    for cam in cameras:
        _get_grabber(cam.rtsp_url)

    # 모든 grabber가 첫 프레임을 수신할 때까지 대기 (warm-up)
    deadline = time.time() + timeout_ms / 1000
    pending = {cam.rtsp_url for cam in cameras}
    while pending and time.time() < deadline:
        for rtsp_url in list(pending):
            if _grabbers[rtsp_url].get() is not None:
                pending.discard(rtsp_url)
        if pending:
            time.sleep(0.05)

    # 모든 grabber가 준비된 시점에 동시 스냅샷
    return [(cam, _grabbers[cam.rtsp_url].get()) for cam in cameras]


def frame_to_base64(frame: np.ndarray, quality: int = 80) -> str:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buf).decode("utf-8")
