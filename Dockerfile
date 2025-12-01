# 베이스 이미지: Python 3.11 + 최소 리눅스
FROM python:3.11-slim

# 컨테이너 안에서 작업 디렉터리
WORKDIR /app

# 필수 OS 라이브러리 (mediapipe / opencv가 필요로 하는 것들)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 libsm6 libxext6 libxrender1 \
 && rm -rf /var/lib/apt/lists/*

# 파이썬 패키지 설치
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY src ./src

# 로그 플러시 빨리 되도록
ENV PYTHONUNBUFFERED=1

# 컨테이너가 열어 줄 포트
EXPOSE 8000

# 컨테이너가 시작될 때 실행할 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]