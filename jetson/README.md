# Jetson Orin Nano 배포

x86(개발 PC/서버)용 `docker-compose.yml`과 별개로, Jetson Orin Nano(ARM64)에서 돌리기 위한
설정을 이 폴더에 따로 둔다. **주의: 실제 Jetson 하드웨어에서 빌드·실행해 검증하지 않았다** —
아래 가정이 실제 보드 환경과 다르면(특히 JetPack 세부 버전) 손봐야 할 수 있다.

## 가정

- JetPack 6.x (L4T r36) — 다른 버전이면 `jetson/backend.Dockerfile`의 베이스 이미지 태그를 맞는 걸로 바꿔야 한다.
- Docker + NVIDIA Container Runtime이 이미 설치되어 있다 (JetPack SDK Manager로 보통 같이 깔린다).
- YOLO(ultralytics)는 GPU로, 얼굈인식(insightface)은 CPU로 돌린다 — 얼굈인식까지 GPU로 돌리려면
  JetPack 버전에 맞는 onnxruntime-gpu 휠(NVIDIA Jetson Zoo 배포)을 따로 구해 넣어야 한다.

## x86 버전과 다른 점

| | x86 (`../docker-compose.yml`) | Jetson (`docker-compose.yml`) |
|---|---|---|
| 베이스 이미지 | `python:3.11-slim` | `dustynv/l4t-pytorch:r36.4.0` (torch/torchvision 내장) |
| GPU 연결 | `gpus: all` | `runtime: nvidia` |
| onnxruntime | `onnxruntime-gpu` | `onnxruntime` (CPU) |
| 빌드 컨텍스트 | `./backend` | 리포 루트(`..`) — jetson 전용 requirements를 같이 COPY하려고 |

프론트엔드는 손대지 않았다 — `node:20-alpine`, `nginx:alpine` 둘 다 ARM64 이미지를 공식
제공해서 기존 `frontend/Dockerfile` 그대로 쓴다.

## 사전 준비

1. **JetPack 버전 확인**
   ```
   cat /etc/nv_tegra_release
   ```
   r36 계열이 아니면 `jetson/backend.Dockerfile`의 `FROM dustynv/l4t-pytorch:r36.4.0` 태그를
   맞는 버전으로 바꾼다 (https://hub.docker.com/r/dustynv/l4t-pytorch/tags).

2. **도커 nvidia 런타임 확인**
   ```
   docker info | grep -i runtime
   ```
   목록에 `nvidia`가 없으면 `/etc/docker/daemon.json`에 아래를 추가하고 도커를 재시작한다:
   ```json
   {
     "runtimes": {
       "nvidia": { "path": "nvidia-container-runtime", "runtimeArgs": [] }
     }
   }
   ```

3. **환경 파일 준비** — `backend/.env.production`, 리포 루트 `.env`는 git에 안 올라가므로
   (`.gitignore`) 기존 PC에서 쓰던 값을 Jetson 쪽에도 복사하거나 새로 만들어야 한다
   (API 키, Slack 시크릿, 관리자 비밀번호 등).

4. **모델/데이터** — `backend/models`의 커스텀 YOLO 가중치(.pt)를 Jetson에도 복사해 둔다.
   `backend/data`는 처음엔 비어 있어도 런타임에 채워진다.

## 실행

리포지토리 루트에서:

```
docker compose -f jetson/docker-compose.yml up -d --build
```

## 확인해야 할 것들 (실기 테스트 시)

- `docker compose -f jetson/docker-compose.yml logs -f backend` 로 `insightface`/`ultralytics`
  임포트 단계에서 에러 없이 뜨는지
- YOLO가 실제로 GPU를 쓰는지: 로그에 `device=0`이 찍히는지, `tegrastats`로 GPU 사용률이 오르는지
- `onnxruntime`이 CPU 프로바이더로 도는지 (의도한 대로 — `CUDAExecutionProvider`를 요청해도
  onnxruntime이 알아서 `CPUExecutionProvider`로 폴백한다)
- insightface 빌드(소스 컴파일)가 Jetson eMMC/SD카드 용량과 빌드 시간에 부담되는지 — 느리면
  버퍼로 스왑 공간을 늘리는 걸 고려한다
