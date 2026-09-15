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
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop_event.is_set():
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
            while cap.isOpened() and not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    break
                with self._lock:
                    self._frame = frame
            cap.release()
            if not self._stop_event.is_set():
                time.sleep(1)  # 재연결 대기

    def stop(self):
        """카메라 설정이 바뀌어 이 URL을 더 이상 아무도 쓰지 않을 때 재연결 루프를 종료한다."""
        self._stop_event.set()

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


def prune_grabbers(active_urls: set[str]) -> None:
    """현재 저장된 카메라 설정에 더 이상 없는 RTSP URL의 grabber 스레드를 정리한다.

    카메라 URL을 수정/삭제해도 이전 URL로 만들어진 백그라운드 재연결 스레드가
    프로세스 수명 내내 남아 무한 재시도 로그를 남기는 문제를 막기 위함.
    """
    with _grabbers_lock:
        stale = [url for url in _grabbers if url not in active_urls]
        for url in stale:
            _grabbers.pop(url).stop()


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
