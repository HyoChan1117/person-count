from pydantic import BaseModel
from typing import List, Optional


class Point(BaseModel):
    x: float
    y: float


class Camera(BaseModel):
    camera_id: str
    name: str
    ip_address: Optional[str] = None
    rtsp_url: Optional[str] = None
    roi_polygon: List[Point] = []
    view_group: Optional[str] = None
    seat_count: Optional[int] = None
    seat_ids: List[str] = []
    seat_lines: dict = {}  # {"A1": [[x1, y1], [x2, y2]]} line points in camera frame coords


class Classroom(BaseModel):
    id: int
    name: str
    cameras: List[Camera] = []
    prompt: Optional[str] = None
    yolo_model: Optional[str] = "yolov8x"
    conf_threshold: Optional[float] = None  # YOLO 감지 신뢰도 임계값 (None = 기본값 0.30)
    yolo_llm_model: Optional[str] = "claude-sonnet-5"  # YOLO+LLM에 사용할 Claude 모델
    yolo_llm_conf_threshold: Optional[float] = None  # YOLO+LLM용 YOLO 임계값 (None = 기본값 0.35)
    yolo_llm_yolo_model: Optional[str] = "yolo26x-pose"  # YOLO+LLM용 YOLO 모델
    schedule: Optional[dict] = None  # {"mon": [9, 10, ...], ...} 요일별 수업이 있는 정시(9~21)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ClassroomCreate(BaseModel):
    name: str


class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    cameras: Optional[List[Camera]] = None
    prompt: Optional[str] = None
    yolo_model: Optional[str] = None
    conf_threshold: Optional[float] = None
    yolo_llm_model: Optional[str] = None
    yolo_llm_conf_threshold: Optional[float] = None
    yolo_llm_yolo_model: Optional[str] = None
    schedule: Optional[dict] = None


class PromptConfig(BaseModel):
    system_prompt: str = ""
    default_user_prompt: str = ""


class PromptConfigUpdate(BaseModel):
    system_prompt: Optional[str] = None
    default_user_prompt: Optional[str] = None

