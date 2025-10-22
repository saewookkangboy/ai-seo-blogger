# Development Tests Directory

이 디렉토리는 AI SEO Blog Generator의 개발 및 테스트용 스크립트들을 포함합니다.

## 📁 디렉토리 구조

```
tests/development/
├── README.md                           # 이 파일
├── test_*.py                          # 일반 테스트 스크립트들
├── *_test.py                          # 특정 기능 테스트 스크립트들
├── api_*.py                           # API 관련 테스트
├── crawler_*.py                       # 크롤러 관련 테스트
├── performance_*.py                   # 성능 테스트
├── system_*.py                        # 시스템 테스트
├── gemini_*.py                        # Gemini API 테스트
├── feature_*.py                       # 기능 업데이트 스크립트
├── generate_*.py                      # 보고서 생성 스크립트
├── check_*.py                         # 검증 스크립트
├── report_*.py                        # 리포트 스크립트
└── *.db                              # 테스트용 데이터베이스 파일들
```

## 🚫 프로덕션 환경에서 제외

이 디렉토리의 모든 파일들은 **프로덕션 환경에서 제외**됩니다:

- `.gitignore`에 포함되어 Git에서 추적되지 않음
- 서버 실행 시 로드되지 않음
- 시스템 리소스에 부하를 주지 않음

## 🧪 테스트 실행 방법

개발 중에 테스트를 실행하려면:

```bash
# 특정 테스트 실행
python tests/development/test_realtime_progress.py

# 성능 테스트 실행
python tests/development/performance_optimization_test.py

# 전체 파이프라인 테스트
python tests/development/test_complete_pipeline.py
```

## 📋 테스트 파일 설명

### 주요 테스트 스크립트

1. **test_realtime_progress.py** - 실시간 진행 상황 표시 테스트
2. **performance_optimization_test.py** - 성능 최적화 테스트
3. **test_complete_pipeline.py** - 전체 파이프라인 테스트
4. **test_gemini_2_0_flash_integration.py** - Gemini 2.0 Flash 통합 테스트
5. **system_optimization_test.py** - 시스템 최적화 테스트

### API 테스트

1. **api_key_validator.py** - API 키 검증
2. **api_performance_test.py** - API 성능 테스트
3. **test_api_display.py** - API 표시 테스트

### 크롤러 테스트

1. **crawler_debug.py** - 크롤러 디버깅
2. **crawler_performance_test.py** - 크롤러 성능 테스트
3. **smart_crawler_test.py** - 스마트 크롤러 테스트
4. **selenium_crawler_test.py** - Selenium 크롤러 테스트

### 기능 테스트

1. **test_translation.py** - 번역 기능 테스트
2. **test_geo_optimization.py** - 지역 최적화 테스트
3. **test_dashboard_navigation.py** - 대시보드 네비게이션 테스트

## ⚠️ 주의사항

- 이 파일들은 **개발 및 테스트 목적**으로만 사용됩니다
- 프로덕션 환경에서는 실행되지 않습니다
- 테스트 실행 시 시스템 리소스를 사용할 수 있습니다
- 테스트 후에는 서버를 재시작하는 것을 권장합니다

## 🔧 유지보수

테스트 파일을 추가할 때:

1. 파일명에 `test_` 접두사 사용
2. 이 README.md 파일 업데이트
3. `.gitignore`에 새로운 패턴 추가 (필요시)

---

**마지막 업데이트**: 2025년 8월 1일  
**버전**: 1.0 