"""RTSP 프레임 캡처 유틸리티."""
from __future__ import annotations

import base64
import os
import threading
import time
from typing import Optional

import cv2
import numpy as np

# 마지막 프레임 요청 후 이 시간(초)이 지나면 RTSP 연결과 디코딩 스레드를 종료한다.
# 다음 요청 때 자동으로 다시 연결되므로, 아무도 보지 않는 동안의 유휴 부하가 사라진다.
_IDLE_TIMEOUT = float(os.getenv("RTSP_IDLE_TIMEOUT", "60"))


class _RTSPGrabber:
    """백그라운드 스레드로 RTSP 스트림을 수신하되, 요청이 있을 때만 프레임을 디코딩한다.

    read()는 매 프레임마다 디코딩 + 색변환 + 수 MB 배열 할당을 수행하므로 카메라 여러 대를
    24시간 돌리면 그 자체로 CPU/메모리 부하가 크다. 스트림을 최신 상태로 유지하는 데는
    grab()만으로 충분하고, 실제 배열이 필요한 순간(get() 호출 직후)에만 retrieve()로
    꺼내면 같은 신선도를 유지하면서 불필요한 변환/할당을 없앨 수 있다.
    """

    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url
        self._frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._want = threading.Event()
        self._last_request = time.monotonic()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _idle_expired(self) -> bool:
        return time.monotonic() - self._last_request > _IDLE_TIMEOUT

    def _run(self):
        # 바깥 루프에서도 유휴 검사를 해야 카메라가 오프라인일 때
        # 아무도 쓰지 않는 재연결 루프가 영원히 돌지 않는다.
        while not self._stop_event.is_set() and not self._idle_expired():
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 오래된 프레임이 버퍼에 쌓이지 않게
            while cap.isOpened() and not self._stop_event.is_set():
                if self._idle_expired():
                    cap.release()
                    self._shutdown()
                    return
                if not cap.grab():
                    break
                if self._want.is_set():
                    ok, frame = cap.retrieve()
                    if ok:
                        with self._lock:
                            self._frame = frame
                        self._want.clear()
            cap.release()
            if not self._stop_event.is_set():
                time.sleep(1)  # 재연결 대기
        self._shutdown()

    def _shutdown(self):
        self._stop_event.set()
        with self._lock:
            self._frame = None  # 유휴 상태에서 프레임 버퍼(장당 수 MB)를 들고 있지 않도록

    def stop(self):
        """카메라 설정이 바뀌어 이 URL을 더 이상 아무도 쓰지 않을 때 재연결 루프를 종료한다."""
        self._stop_event.set()

    def alive(self) -> bool:
        return self._thread.is_alive() and not self._stop_event.is_set()

    def get(self) -> Optional[np.ndarray]:
        self._last_request = time.monotonic()
        self._want.set()
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def invalidate(self) -> None:
        """갖고 있던 프레임을 버려, 다음 get()이 새로 디코딩된 것만 돌려주게 한다.

        get()은 보관 중이던 프레임을 돌려주고 다음 것을 요청하는 구조라, PTZ로 카메라를
        옮긴 직후에 부르면 이동 전(이전 구역) 장면이 나올 수 있다.
        """
        with self._lock:
            self._frame = None
        self._want.set()

    def prewarm(self, hold_seconds: float) -> None:
        """곧 쓰일 연결이 유휴 종료되지 않도록 마감 시각을 미리 늦춰 둔다.

        화면을 열어둔 동안 연결을 살려두어, 실제로 볼 때 RTSP 재연결을 기다리지 않게 한다.
        """
        self._last_request = max(self._last_request, time.monotonic() + hold_seconds)
        self._want.set()  # 첫 프레임을 미리 디코딩해 두어 바로 꺼내 쓸 수 있게


_grabbers: dict[str, _RTSPGrabber] = {}
_grabbers_lock = threading.Lock()


def _get_grabber(rtsp_url: str) -> _RTSPGrabber:
    with _grabbers_lock:
        grabber = _grabbers.get(rtsp_url)
        if grabber is None or not grabber.alive():
            # 유휴 상태로 종료된 grabber는 여기서 다시 연결한다
            grabber = _RTSPGrabber(rtsp_url)
            _grabbers[rtsp_url] = grabber
        return grabber


def prewarm_rtsp(rtsp_url: str, hold_seconds: float = 300.0) -> None:
    """RTSP 연결을 미리 열어 두고 일정 시간 유휴 종료되지 않게 한다."""
    _get_grabber(rtsp_url).prewarm(hold_seconds)


def prune_grabbers(active_urls: set[str]) -> None:
    """현재 저장된 카메라 설정에 더 이상 없는 RTSP URL의 grabber 스레드를 정리한다.

    카메라 URL을 수정/삭제해도 이전 URL로 만들어진 백그라운드 재연결 스레드가
    프로세스 수명 내내 남아 무한 재시도 로그를 남기는 문제를 막기 위함.
    """
    with _grabbers_lock:
        stale = [url for url in _grabbers if url not in active_urls]
        for url in stale:
            _grabbers.pop(url).stop()


def capture_rtsp_frame(rtsp_url: str, timeout_ms: int = 15000,
                       fresh: bool = False) -> Optional[np.ndarray]:
    """fresh=True면 보관 중이던 프레임을 버리고 새로 디코딩된 것만 기다린다."""
    grabber = _get_grabber(rtsp_url)
    if fresh:
        grabber.invalidate()
    # 최초 연결 시 프레임이 없으면 잠시 대기
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        # 요청 직전에 유휴 종료된 grabber를 잡았다면 새로 연결한다
        if not grabber.alive():
            grabber = _get_grabber(rtsp_url)
        frame = grabber.get()
        if frame is not None:
            return frame
        time.sleep(0.1)
    return None


def capture_rtsp_frames_parallel(cameras, timeout_ms: int = 15000) -> list[tuple]:
    """모든 카메라 grabber를 동시에 warm-up 후 동일 시점 스냅샷 반환."""
    grabbers = {cam.rtsp_url: _get_grabber(cam.rtsp_url) for cam in cameras}

    # 모든 grabber가 첫 프레임을 수신할 때까지 대기 (warm-up)
    deadline = time.time() + timeout_ms / 1000
    pending = set(grabbers)
    while pending and time.time() < deadline:
        for rtsp_url in list(pending):
            if not grabbers[rtsp_url].alive():
                grabbers[rtsp_url] = _get_grabber(rtsp_url)
            if grabbers[rtsp_url].get() is not None:
                pending.discard(rtsp_url)
        if pending:
            time.sleep(0.05)

    # 모든 grabber가 준비된 시점에 동시 스냅샷
    return [(cam, grabbers[cam.rtsp_url].get()) for cam in cameras]


def frame_to_base64(frame: np.ndarray, quality: int = 80) -> str:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buf).decode("utf-8")
