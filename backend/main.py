from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import classrooms, analysis, prompts, slack


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
    yield


app = FastAPI(title="Classroom Person Count API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=not in_debug)
