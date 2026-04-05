# --- 1. Base Image ---
FROM python:3.12-slim

# --- 2. Environment Variables ---
ENV PYTHONUNBUFFERED=1
ENV PIP_USE_PEP517=yes

# --- 3. System Dependencies ---
# ffmpeg 및 기타 필요한 시스템 라이브러리 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git libsm6 libxext6 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# --- 4. Application Setup ---
WORKDIR /app

# --- 5. Python Dependencies ---
# pip 업그레이드
RUN python -m pip install --upgrade pip

# PyTorch CPU 버전 설치
RUN pip install torch==2.3.1+cpu torchvision==0.18.1+cpu torchaudio==2.3.1+cpu --index-url https://download.pytorch.org/whl/cpu

# requirements.txt 복사
COPY requirements.txt .

# requirements.txt 에 명시된 나머지 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# Whisper 설치 시 openai 버전 충돌이 있다면 아래 주석 해제 후 openai 버전 명시
# RUN pip install --upgrade --no-deps --force-reinstall openai==<원하는_openai_버전>

# --- 6. Application Code ---
# 나머지 애플리케이션 코드 복사
# (app.py, pipeline.py, ui_components.py 등)
COPY . .

# --- 7. Port Exposure ---
EXPOSE 8501

# --- 8. Healthcheck---
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# --- 9. Entrypoint / Command ---
CMD ["streamlit", "run", "app.py", "--server.fileWatcherType", "none", "--server.runOnSave", "false", "--server.headless", "true"]