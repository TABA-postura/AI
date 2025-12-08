# 1. 베이스 이미지 (가벼운 Python 이미지)
FROM python:3.11-slim

# 2. OpenCV가 필요로 하는 시스템 라이브러리 설치
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 생성
WORKDIR /app

# 4. 파이썬 의존성 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# 5. 나머지 소스 코드 복사
COPY . .

# 6. uvicorn을 src/app/main.py 기준으로 실행할 거라 src를 워킹 디렉토리로
WORKDIR /app/src

# 7. 컨테이너에서 쓸 포트
EXPOSE 8000

# 8. (선택) Spring URL 환경변수 – 나중에 docker run 할 때 -e로 덮어씌워도 됨
# ENV SPRING_BASE_URL=http://backend:8080

# 9. 컨테이너 시작 시 실행할 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
