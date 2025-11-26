FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 및 설정 파일 복사
COPY app/ ./app/
COPY synonyms.json .
COPY site_crawler_configs.json .
# api_usage.json은 없을 수도 있으므로 무시하거나 초기화 (여기서는 복사 시도하지 않음, 앱이 생성함)

# 데이터 저장을 위한 디렉토리 생성
RUN mkdir -p logs data

# 환경 변수 설정 (Python 출력 버퍼링 비활성화)
ENV PYTHONUNBUFFERED=1

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 