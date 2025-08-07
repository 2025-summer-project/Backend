FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

# 필수 시스템 패키지 + netcat 설치 (한 번에 처리)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    python3-dev \
    pkg-config \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# requirements 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# wait-for-it.sh 복사 및 실행 권한 부여
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# 폰트 적용
COPY fonts/NanumGothic*.ttf /app/fonts/

# 전체 프로젝트 복사
COPY . .