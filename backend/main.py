from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import classrooms, analysis, prompts, slack
from app.routers import auth as auth_router

OCCUPANCY_MONITOR_INTERVAL = int(os.getenv("OCCUPANCY_MONITOR_INTERVAL", "600"))


def _seconds_until_next_boundary(interval_seconds: int) -> float:
    """자정 기준 interval의 배수가 되는 다음 시각(예: 정각 10분 단위)까지 남은 초."""
    now = datetime.now()
    seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1e6
    remainder = seconds_since_midnight % interval_seconds
    return interval_seconds - remainder if remainder else 0.0


async def _occupancy_monitor_loop():
    from app import storage
    from app.services.occupancy_monitor import collect_all

    while True:
        wait = _seconds_until_next_boundary(OCCUPANCY_MONITOR_INTERVAL)
        print(f"[occupancy_monitor] 다음 수집까지 {wait:.0f}초 대기")
        await asyncio.sleep(wait)
        try:
            if storage.clear_occupancy_if_new_week():
                print("[occupancy_monitor] 새 주(월요일 00시) 시작 → 점유 기록 초기화")
            await asyncio.to_thread(collect_all)
        except Exception as e:
            print(f"[occupancy_monitor] 루프 오류: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app import storage
    from app.services.frame_capture import _get_grabber
    try:
        for classroom in storage.get_all():
            for cam in classroom.cameras:
                if cam.rtsp_url:
                    _get_grabber(cam.rtsp_url)
        print("[startup] grabber 사전 등록 완료")
    except Exception as e:
        print(f"[startup] grabber 사전 등록 실패: {e}")

    monitor_task = asyncio.create_task(_occupancy_monitor_loop())
    yield
    monitor_task.cancel()


app = FastAPI(title="Classroom Person Count API", version="1.0.0", lifespan=lifespan)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(classrooms.router, prefix="/api/classrooms", tags=["classrooms"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])
app.include_router(slack.router, prefix="/api/slack", tags=["slack"])


@app.get("/")
def root():
    return {"status": "ok", "service": "Classroom Person Count API v1.0"}


if __name__ == "__main__":
    import sys
    import uvicorn
    # debugpy(VS Code 디버거)와 reload=True는 호환되지 않으므로 자동 감지
    in_debug = "debugpy" in sys.modules
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=not in_debug)
