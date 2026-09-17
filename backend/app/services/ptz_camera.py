"""Hikvision PTZ 카메라 제어 (ISAPI over HTTP Digest).

감시 장소마다 카메라 설정이 다를 수 있으므로 모든 함수는 카메라 설정 dict를 받는다.
TandemVu 듀얼렌즈 기준으로 스트리밍 채널(101=PTZ 렌즈, 201=광각)과 PTZ 제어 채널(1)의
번호 체계가 서로 다르다는 점에 주의.
"""
from __future__ import annotations

import re

import requests
from requests.auth import HTTPDigestAuth

_TIMEOUT = 5.0

# 카메라가 capabilities로 보고한 실제 절대좌표 범위
PAN_RANGE = (0, 3600)
TILT_RANGE = (-249, 750)
ZOOM_RANGE = (10, 250)


def default_camera() -> dict:
    """새 장소의 초기 카메라 설정.

    접속 정보(IP/계정)는 장소마다 다르므로 비워 두고 사용자가 직접 입력하게 한다.
    포트와 채널 코드만 Hikvision 관례값으로 채워 둔다.
    """
    return {
        # IP가 비어 있으면 PTZ 카메라가 없는 장소로 취급한다.
        "ip": "",
        "username": "",
        "password": "",
        "http_port": 80,
        "rtsp_port": 554,
        "channel_code": "101",
        "control_channel": 1,
    }


def rtsp_url(cam: dict) -> str:
    return (f"rtsp://{cam['username']}:{cam['password']}@"
            f"{cam['ip']}:{cam.get('rtsp_port', 554)}"
            f"/Streaming/Channels/{cam.get('channel_code', '101')}")


def _base(cam: dict) -> str:
    return (f"http://{cam['ip']}:{cam.get('http_port', 80)}"
            f"/ISAPI/PTZCtrl/channels/{cam.get('control_channel', 1)}")


def _auth(cam: dict) -> HTTPDigestAuth:
    return HTTPDigestAuth(cam["username"], cam["password"])


def _tag(xml: str, name: str) -> int | None:
    m = re.search(rf"<{name}>(-?\d+)</{name}>", xml)
    return int(m.group(1)) if m else None


def _clamp(value: int, bounds: tuple[int, int]) -> int:
    return max(bounds[0], min(bounds[1], int(value)))


def get_position(cam: dict) -> dict:
    """현재 절대 위치 조회. {pan, tilt, zoom}"""
    r = requests.get(f"{_base(cam)}/status", auth=_auth(cam), timeout=_TIMEOUT)
    r.raise_for_status()
    return {
        "pan": _tag(r.text, "azimuth"),
        "tilt": _tag(r.text, "elevation"),
        "zoom": _tag(r.text, "absoluteZoom"),
    }


def move_absolute(cam: dict, pan: int, tilt: int, zoom: int) -> None:
    """저장해 둔 구역 좌표로 이동."""
    body = (
        "<PTZData><AbsoluteHigh>"
        f"<elevation>{_clamp(tilt, TILT_RANGE)}</elevation>"
        f"<azimuth>{_clamp(pan, PAN_RANGE)}</azimuth>"
        f"<absoluteZoom>{_clamp(zoom, ZOOM_RANGE)}</absoluteZoom>"
        "</AbsoluteHigh></PTZData>"
    )
    r = requests.put(f"{_base(cam)}/absolute", data=body, auth=_auth(cam), timeout=_TIMEOUT)
    r.raise_for_status()


def move_continuous(cam: dict, pan: int = 0, tilt: int = 0, zoom: int = 0) -> None:
    """수동 조작용 연속 이동. 각 값은 속도(-100~100), 0이면 정지."""
    body = (
        "<PTZData>"
        f"<pan>{_clamp(pan, (-100, 100))}</pan>"
        f"<tilt>{_clamp(tilt, (-100, 100))}</tilt>"
        f"<zoom>{_clamp(zoom, (-100, 100))}</zoom>"
        "</PTZData>"
    )
    r = requests.put(f"{_base(cam)}/continuous", data=body, auth=_auth(cam), timeout=_TIMEOUT)
    r.raise_for_status()


def stop(cam: dict) -> None:
    move_continuous(cam, 0, 0, 0)


def device_info(cam: dict) -> dict:
    """연결 확인용. 카메라 모델/펌웨어를 반환한다."""
    r = requests.get(f"http://{cam['ip']}:{cam.get('http_port', 80)}/ISAPI/System/deviceInfo",
                     auth=_auth(cam), timeout=_TIMEOUT)
    r.raise_for_status()
    return {
        "model": (re.search(r"<model>(.*?)</model>", r.text) or [None, None])[1],
        "firmware": (re.search(r"<firmwareVersion>(.*?)</firmwareVersion>", r.text) or [None, None])[1],
    }
