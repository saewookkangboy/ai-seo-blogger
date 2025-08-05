# AI SEO Blogger Makefile

.PHONY: install run clean test optimize help

# 기본 설정
PYTHON = python3
PIP = pip3
APP_DIR = app
PORT = 8000

# 설치
install:
	@echo "📦 의존성 패키지 설치 중..."
	$(PIP) install -r requirements.txt
	@echo "✅ 설치 완료!"

# 개발 서버 실행
run:
	@echo "🚀 개발 서버 시작 중..."
	cd $(APP_DIR) && uvicorn main:app --reload --host 0.0.0.0 --port $(PORT)

# 프로덕션 서버 실행
run-prod:
	@echo "🚀 프로덕션 서버 시작 중..."
	cd $(APP_DIR) && uvicorn main:app --host 0.0.0.0 --port $(PORT)

# 시스템 최적화
optimize:
	@echo "🔧 시스템 최적화 중..."
	$(PYTHON) optimize_system.py

# 정리
clean:
	@echo "🧹 불필요한 파일 정리 중..."
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name ".DS_Store" -delete
	find . -name "*test*.json" -type f -delete
	find . -name "*performance*.json" -type f -delete
	find . -name "*optimization*.json" -type f -delete
	find . -name "*stress*.json" -type f -delete
	find . -name "*complete*.json" -type f -delete
	find . -name "*gemini*.json" -type f -delete
	find . -name "*seo*.json" -type f -delete
	find . -name "*system*.json" -type f -delete
	find . -name "*crawler*.json" -type f -delete
	find . -name "*content*.json" -type f -delete
	find . -name "*enhanced*.json" -type f -delete
	find . -name "*geo*.json" -type f -delete
	find . -name "debug_*.html" -type f -delete
	find . -name "test_*.html" -type f -delete
	find . -name "*.tmp" -type f -delete
	find . -name "*.bak" -type f -delete
	find . -name "*.backup" -type f -delete
	@echo "✅ 정리 완료!"

# 테스트 실행
test:
	@echo "🧪 테스트 실행 중..."
	python -m pytest tests/ -v

# API Key 테스트
test-api:
	@echo "🔑 API Key 테스트 중..."
	source venv/bin/activate && python test_api_keys.py

# 데이터베이스 초기화
init-db:
	@echo "🗄️ 데이터베이스 초기화 중..."
	cd $(APP_DIR) && python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"
	@echo "✅ 데이터베이스 초기화 완료!"

# 전체 설정 (설치 + DB 초기화)
setup: install init-db
	@echo "�� 전체 설정 완료!"

# 도움말
help:
	@echo "AI SEO Blogger Makefile 명령어:"
	@echo ""
	@echo "  install     - 의존성 패키지 설치"
	@echo "  run         - 개발 서버 실행 (포트 $(PORT))"
	@echo "  run-prod    - 프로덕션 서버 실행"
	@echo "  optimize    - 시스템 최적화 (불필요한 파일 정리)"
	@echo "  clean       - 빠른 정리 (캐시 파일만)"
	@echo "  test        - 테스트 실행"
	@echo "  test-api    - API Key 정상작동 확인"
	@echo "  init-db     - 데이터베이스 초기화"
	@echo "  setup       - 전체 설정 (install + init-db)"
	@echo "  help        - 이 도움말 표시"
	@echo ""
	@echo "사용 예시:"
	@echo "  make setup    # 처음 설치 시"
	@echo "  make run      # 개발 서버 시작"
	@echo "  make optimize # 시스템 최적화" 

test-drive:
	@echo "🔍 Google Drive API 테스트를 시작합니다..."
	@source venv/bin/activate && python3 test_google_drive_simple.py 