# 교실 CCTV 좌석 점유 모니터링 시스템

RTSP CCTV 영상에서 YOLO Pose + Claude Vision LLM으로 **좌석 단위 점유 여부**를 판정하고,
주기적으로 기록해 좌석별·시간대별 사용 통계를 내며, Slack 슬래시 커맨드로 현황을 조회하는 시스템.

- **백엔드**: FastAPI + Ultralytics YOLO + Anthropic Claude (JSON 파일 저장소)
- **프론트엔드**: Vue 3 + Vite + Pinia + Tailwind CSS
- **배포**: Docker Compose (nginx + uvicorn), Windows 시작 프로그램 등록 + ngrok

## 실행 방법

### 개발 환경

```bash
# 백엔드 (FastAPI)
cd backend
cp .env.example .env          # 키 값 채우기
pip install -r requirements.txt
python main.py
# → http://localhost:8000  /  Swagger: http://localhost:8000/docs

# 프론트엔드 (Vue 3)
cd frontend
npm install
npm run dev
# → http://localhost:5173  (/api, /auth 는 8000 포트로 프록시)
```

### 프로덕션 (Docker Compose)

```bash
# backend/.env.production 준비 후
docker compose up -d --build
# → http://localhost  (nginx가 정적 파일 서빙 + /api, /auth 백엔드 프록시)
```

`start-server.ps1`은 Docker 준비를 기다렸다가 `docker-compose up -d` 후 ngrok 터널을 띄우고,
`register-startup.ps1`은 이 스크립트를 Windows 로그인 시 자동 실행되도록 등록한다.

### 환경 변수 (`backend/.env`)

| 변수 | 설명 |
|------|------|
| `ANTHROPIC_API_KEY` | Claude Vision LLM 호출 키 |
| `SLACK_WEBHOOK_URL` | Slack 알림 전송용 Webhook |
| `SLACK_SIGNING_SECRET` | 슬래시 커맨드 서명 검증 |
| `PUBLIC_BASE_URL` | Slack에 첨부할 스냅샷 이미지의 공개 주소 |
| `ADMIN_PANEL_URL` | `/관리자` 커맨드가 안내할 주소 (미설정 시 `PUBLIC_BASE_URL`) |
| `ADMIN_PASSWORD` | 관리자 로그인 비밀번호 |
| `JWT_SECRET` | 관리자 토큰 서명 키 |
| `CORS_ORIGINS` | 허용 오리진 (쉼표 구분, 기본 `localhost:5173,localhost:3000`) |
| `OCCUPANCY_MONITOR_INTERVAL` | 점유 스냅샷 수집 주기(초), 기본 `600` |
| `YOLO_MODEL_DIR` | YOLO+LLM용 모델 디렉토리 (기본 `../yolo/human/models`) |
| `PERSON_CONF_THRESH` / `BACKEND` | 사람 감지 임계값 / 추론 백엔드(`auto`·`onnx`·`torch`) |

## 프로젝트 구조

```
person-count/
├── backend/
│   ├── main.py                          # FastAPI 진입점 + 점유 모니터 백그라운드 루프
│   ├── models/                          # YOLO 가중치 (*.pt, 대용량은 git 제외)
│   ├── data/                            # JSON 저장소 (런타임 생성)
│   │   ├── classrooms.json              # 교실/카메라/좌석선 설정
│   │   ├── prompts.json                 # 시스템·기본 사용자 프롬프트
│   │   ├── maps/, map_data/             # 배치도 PNG / 배치도 객체 JSON
│   │   ├── occupancy/                   # 교실별 점유 스냅샷 기록
│   │   └── bg_references/               # 배경 차분용 기준 프레임
│   └── app/
│       ├── models.py                    # Pydantic 모델 (Classroom, Camera …)
│       ├── storage.py                   # JSON CRUD · 스냅샷 적재 · 주간 초기화
│       ├── auth.py                      # 관리자 JWT 발급/검증 (require_admin)
│       ├── routers/
│       │   ├── classrooms.py            # 교실 CRUD, 배치도 데이터
│       │   ├── analysis.py              # 프레임/실시간/좌석점유/통계 API
│       │   ├── prompts.py               # 프롬프트 설정
│       │   ├── slack.py                 # 슬래시 커맨드 · 스냅샷 이미지 제공
│       │   └── auth.py                  # 관리자 로그인
│       └── services/
│           ├── frame_capture.py         # RTSP 상시 수신 스레드 + 병렬 캡처
│           ├── live_stream.py           # 카메라별 추론 워커 + MJPEG 스트리밍
│           ├── real_detection.py        # YOLO 모델 캐시 + 추론 직렬화 락
│           ├── vision_llm_detection.py  # Pose 키포인트 기반 착석 판정
│           ├── yolo_llm_detection.py    # YOLO 감지 + Claude LLM 검증/카운트
│           ├── background_detection.py  # 배경 차분 기반 인원 유무
│           ├── occupancy_monitor.py     # 주기 스냅샷 수집 · 좌석별/시간별 집계
│           └── map_renderer.py          # 배치도 + 점유 오버레이 PNG 렌더링
├── frontend/src/
│   ├── views/
│   │   ├── ClassroomListView.vue        # 교실 목록/등록/검색
│   │   ├── CameraSetupView.vue          # 카메라 등록 + 좌석 선(ROI) 지정
│   │   ├── MapEditorView.vue            # 교실 배치도 에디터 (CCTV·책상·의자)
│   │   ├── DashboardView.vue            # 점유 분석 실행 + 실시간 영상
│   │   └── MonitoringView.vue           # 좌석별 누적 점유 시간 · 시간표
│   ├── components/modals/               # 로그인·프롬프트·시간표 모달
│   └── stores/                          # authStore, classroomStore, promptStore
├── docker-compose.yml
├── start-server.ps1 / register-startup.ps1
└── runs/                                # YOLO 파인튜닝 결과 (git 제외)
```

## 화면 흐름

| 화면 | 경로 | 역할 |
|------|------|------|
| 교실 목록 | `/classrooms` | 교실 등록·검색·삭제 |
| 카메라 설정 | `/classrooms/:id/setup` | RTSP 등록, 좌석별 4점 밴드(앞선 2클릭 + 뒷선 2클릭) 지정, 배경 기준 프레임 저장 |
| 배치도 에디터 | `/classrooms/:id/map` | CCTV·책상·의자 배치, 책상↔CCTV 매칭 → 카메라별 담당 좌석 수/번호 자동 동기화 |
| 대시보드 | `/dashboard/:id` | YOLO 좌석 점유 / YOLO+LLM 분석 실행, 배치도 오버레이, MJPEG 실시간 보기 |
| 모니터링 | `/monitoring/:id` | 좌석별 누적 점유 시간, 시간대별 점유 좌석 수, 요일별 시간표 설정 |

## 좌석 점유 판정 방식

1. **좌석 밴드 정의** — 카메라 화면 좌표에 좌석마다 앞/뒤 선 2개(4점)를 그려 `seat_lines`로 저장한다.
2. **감지** — RTSP 최신 프레임에 YOLO Pose를 돌려 사람 박스와 키포인트를 얻는다.
3. **착석 판정** — 무릎·엉덩이 각도, 상체 기울기, 박스 대비 엉덩이 위치로 서 있음/앉음을 분류한다.
4. **좌석 매칭** — 착석으로 분류된 사람의 기준점이 어느 좌석 밴드 안에 있는지로 좌석을 배정한다.
5. **중복 제거** — 여러 카메라의 결과를 `seat_id` 기준 합집합으로 합쳐 최종 점유 좌석 수를 계산한다.

`/api/analysis/{id}/seat-occupancy`는 LLM 없이 Pose만으로 판정해 비용이 들지 않고,
`/api/analysis/{id}/yolo-llm-count`는 감지 결과 크롭을 Claude에 넘겨 오탐(사람 아님)과 자세를 한 번 더 검증한다.

## 주기 모니터링

- `OCCUPANCY_MONITOR_INTERVAL`(기본 10분) 주기로 자정 기준 정각에 맞춰 스냅샷을 수집한다 (LLM 미사용).
- 스냅샷은 `data/occupancy/{classroom_id}.json`에 누적되고 30일이 지나면 정리된다.
- 매주 월요일 00시에 기록을 초기화한다.
- 집계는 09~21시를 대상으로 하며, 교실별 요일 시간표(`schedule`)가 있으면 수업이 있는 시간만 집계한다.

## 주요 API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/auth/admin/login` | 비밀번호 → 관리자 JWT(8시간) |
| `GET/POST/PUT/DELETE` | `/api/classrooms` | 교실 CRUD (쓰기는 관리자) |
| `GET/PUT` | `/api/classrooms/{id}/map-data` | 배치도 객체 JSON |
| `GET` | `/api/analysis/{id}/frame/{cam}` | 단일 프레임 캡처 (base64) |
| `GET` | `/api/analysis/{id}/live/{cam}` | MJPEG 실시간 탐지 스트림 |
| `POST` | `/api/analysis/{id}/seat-lines/{cam}` | 좌석 밴드 저장 |
| `POST` | `/api/analysis/{id}/bg-reference/{cam}` | 배경 기준 프레임 저장 (업로드/캡처) |
| `GET` | `/api/analysis/{id}/bg-detect/{cam}` | 배경 차분 기반 인원 유무 |
| `GET` | `/api/analysis/{id}/seat-occupancy` | Pose 기반 좌석 점유 현황 |
| `GET` | `/api/analysis/{id}/yolo-llm-count` | YOLO + Claude 인원 카운트 |
| `GET` | `/api/analysis/{id}/occupancy-stats-daily?date=` | 하루치 좌석별 점유 시간(분) |
| `GET` | `/api/analysis/{id}/occupancy-hourly?date=` | 시간대별 점유 좌석 수 |
| `GET/PUT` | `/api/prompts` | 시스템·기본 사용자 프롬프트 |

교실 생성/수정/삭제, 배치도·좌석선·프롬프트 저장 등 쓰기 API는 모두 `require_admin` JWT가 필요하다.

## Slack 연동

| 커맨드 | 동작 |
|--------|------|
| `/좌석 [교실명\|ID]` | Pose 기반 좌석 점유 요약 + 배치도 오버레이 이미지 |
| `/좌석상세 [교실명\|ID]` | YOLO+LLM 분석 결과와 LLM 코멘트 |
| `/관리자` | 관리자 페이지 주소 안내 (요청자에게만 표시) |

요청은 `SLACK_SIGNING_SECRET`으로 서명을 검증한 뒤 백그라운드에서 처리하고 `response_url`로 회신한다.
결과 이미지는 `map_renderer`가 배치도에 점유 상태를 그려 `/api/slack/snapshot/{id}`로 공개한다.

## 설계 메모

- **RTSP 상시 수신**: 카메라마다 백그라운드 스레드가 최신 프레임만 보관해, 분석 요청 시 연결 지연 없이 즉시 프레임을 얻는다.
- **추론 직렬화**: Ultralytics 모델 인스턴스를 캐시해 공유하므로, 스레드 간 설정 덮어쓰기를 막기 위해 `real_detection.infer_lock`으로 추론을 직렬화한다.
- **실시간 스트림**: 카메라별 워커가 자기 속도로 추론해 최신 프레임만 캐시하고, 스트리밍은 그 캐시를 일정 주기로 내보내 프레임 간격을 고르게 유지한다. 같은 카메라를 여러 화면에서 봐도 추론은 한 번만 수행된다.
- **저장소**: 별도 DB 없이 `backend/data` 아래 JSON 파일을 사용하며, Docker에서는 이 디렉토리를 볼륨으로 마운트해 유지한다.
