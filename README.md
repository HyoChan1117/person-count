# 교실 CCTV 인원 카운트 시스템 - MVP

## 실행 방법

### 백엔드 (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000
# → Swagger: http://localhost:8000/docs
```

### 프론트엔드 (Vue 3)
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## 프로젝트 구조

```
person-count/
├── backend/
│   ├── main.py                        # FastAPI 진입점
│   ├── requirements.txt
│   ├── data/classrooms.json           # JSON 저장소 (자동 생성)
│   └── app/
│       ├── models.py                  # Pydantic 모델
│       ├── storage.py                 # JSON 파일 CRUD
│       ├── routers/
│       │   ├── classrooms.py          # 교실 CRUD API
│       │   └── occupancy.py          # 점유 분석 API
│       └── services/
│           ├── mock_detection.py      # Mock YOLO 감지
│           └── occupancy_service.py  # seat_id 중복 제거 로직
└── frontend/
    └── src/
        ├── views/
        │   ├── ClassroomListView.vue  # 교실 목록/등록
        │   ├── ClassroomEditorView.vue # 맵 에디터 메인
        │   └── DashboardView.vue      # 점유 현황 대시보드
        ├── components/editor/
        │   ├── MapEditorCanvas.vue    # Konva.js 맵 에디터 (핵심)
        │   ├── EditorToolBar.vue      # 툴 선택 사이드바
        │   ├── PropertiesPanel.vue    # 선택 객체 속성 편집
        │   └── ObjectList.vue         # 객체 목록 트리
        └── stores/
            ├── classroomStore.js      # 교실 상태 관리
            └── occupancyStore.js      # 점유 결과 상태 관리
```

## 에디터 사용법

| 도구 | 동작 |
|------|------|
| 선택 | 객체 클릭 → 이동/리사이즈/속성 편집 |
| 좌석 추가 | 빈 공간 클릭 → 좌석 자동 배치 (seat_id 자동 부여) |
| CCTV 추가 | 빈 공간 클릭 → CCTV 배치 |
| 사각형 범위 | 드래그 → 측정 범위 생성 + 좌석 자동 매핑 |
| 다각형 범위 | 클릭으로 점 추가 → 더블클릭으로 완성 |
| 스크롤 | 줌 인/아웃 |

## 데이터 설계

- **classroom**: 교실 기본 정보 (크기, 이름)
- **seats**: 좌석 배치 (seat_id, 위치, 크기)
- **cameras**: CCTV (camera_id, 위치, 방향, IP, RTSP)
- **measurement_areas**: 측정 범위 (폴리곤 + 담당 camera_id + assigned_seat_ids)
- **occupancy_results**: 분석 결과 (occupied_seat_ids — seat_id 기준 중복 제거)
- **slack_notifications**: Slack 알림용 구조화된 페이로드

## 핵심 설계 원칙

여러 CCTV의 측정 범위가 겹쳐도 **seat_id 기준 중복 제거** 후 최종 인원 계산.
좌석과 매칭되지 않은 사람은 `standing_persons`로 별도 카운트.
