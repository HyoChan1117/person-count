FROM python:3.11-slim

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

COPY requirements.txt .
# insightface는 휠이 없으면 소스 빌드가 필요하므로 빌드 도구를 같은 레이어에서 쓰고 정리한다.
# 또 insightface가 의존성으로 CPU판 onnxruntime을 끌어오는데, 두 패키지가 같은 디렉터리를
# 공유해 CPU판이 GPU판을 가려버린다 -> CPU판을 지우고 GPU판을 다시 깔아 복구한다.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y onnxruntime \
    && pip install --no-cache-dir --force-reinstall --no-deps onnxruntime-gpu \
    && apt-get purge -y build-essential && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# 얼굴 인식 모델(buffalo_l)을 마운트된 data 볼륨에 두어 컨테이너를 다시 만들어도 유지되게 한다
ENV INSIGHTFACE_HOME=/app/data/insightface

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
