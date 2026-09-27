# Jetson Orin Nano (JetPack 6.x / L4T r36) 전용 백엔드 이미지.
#
# 리포 루트를 빌드 컨텍스트로 써야 한다 (jetson/requirements-jetson.txt와 backend/ 소스를
# 같이 COPY하기 위해). jetson/docker-compose.yml이 이렇게 설정해 둔다:
#   docker compose -f jetson/docker-compose.yml build
#
# x86용 backend/Dockerfile과 다른 점:
#   - 베이스: python:3.11-slim(x86) 대신 dustynv/l4t-pytorch(ARM64, JetPack에 맞는
#     CUDA·torch·torchvision이 이미 빌드되어 있음).
#   - onnxruntime: GPU판 대신 CPU판 (jetson/requirements-jetson.txt 참고 — 얼굈인식은
#     CPU로 충분하다는 판단, YOLO만 GPU로 돈다).
#
# 태그(r36.4.0)는 JetPack 6.x 기준 예시다. 실제 보드의 JetPack 버전에 맞아야 하며, 다음으로
# 확인 후 필요하면 아래 FROM 줄의 태그를 바꿔라:
#   cat /etc/nv_tegra_release
#   https://hub.docker.com/r/dustynv/l4t-pytorch/tags
FROM dustynv/l4t-pytorch:r36.4.0

ENV TZ=Asia/Seoul
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    tzdata \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    curl \
    fonts-nanum \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY jetson/requirements-jetson.txt ./requirements.txt
# insightface는 ARM64용 사전 빌드 휠이 없어 소스 빌드가 필요하다 — build-essential/cmake는
# 그 때문이고, 빌드가 끝나면 이미지 용량을 위해 지운다(Jetson eMMC는 보통 넉넉하지 않다).
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake python3-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y build-essential cmake python3-dev && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# 얼굴 인식 모델(buffalo_l)을 마운트된 data 볼륨에 두어 컨테이너를 다시 만들어도 유지되게 한다
ENV INSIGHTFACE_HOME=/app/data/insightface

COPY backend/. .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
