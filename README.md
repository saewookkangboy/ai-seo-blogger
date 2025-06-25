<<<<<<< HEAD
# ai-seo-blogger
blog generator with ai
=======
# AI-Powered SEO Blog Post Generator

AI를 활용하여 특정 키워드에 대한 해외 자료를 수집, 번역, 요약하고 SEO에 최적화된 블로그 초안을 생성하는 프로젝트입니다.

## 🚀 주요 기능

| 구분 | 기능명 | 설명 |
|------|--------|------|
| UI/UX | 공통 네비게이션/푸터 | 모든 페이지에 일관된 네비게이션 바(`_navbar.html`)와 푸터 적용, 유지보수성 강화 |
| UI/UX | 통일된 폰트/스타일 | 'IBM Plex Sans KR' 단일 폰트, 카드/테이블/버튼 등 관리자 기준 UI 통일, 공통 CSS(`common.css`) 적용 |
| UI/UX | 관리자 페이지 고도화 | 탭 기반 대시보드, 키워드/포스트/크롤링/시스템 관리 등 실무 중심 UI 제공 |
| 데이터 | 생성 기록 관리 | 생성된 포스트 전체/검색/정렬/상세 모달/삭제 등 실시간 관리 |
| 데이터 | 대량 일괄 관리 | 포스트/키워드 선택 삭제, 전체선택, 검색, 필터, 복원(가져오기), 백업(내보내기), 엑셀 내보내기 지원 |
| 데이터 | 엑셀 내보내기 | openpyxl 기반, 선택/전체 포스트를 xlsx로 다운로드, ImportError 발생 시 pip 안내 |
| API | FastAPI 기반 REST | 포스트 생성/검색/일괄 삭제/내보내기/복원 등 RESTful API 제공 |
| API | 대량 데이터 최적화 | Pydantic v2 대응, 직렬화/성능/타입/None 처리 보완, 대량 데이터 환경 대응 |
| 크롤링 | 사이트별 크롤러 | 주요 해외 SEO 사이트별 맞춤 크롤러 및 구글 스타일 크롤러 지원 |
| 번역 | DeepL/Gemini 지원 | DeepL, Gemini API 기반 번역, 키워드 추출, AI 콘텐츠 생성 |
| 통계 | API/크롤링/포스트 통계 | 일자별/누적 API 호출, 크롤링, 포스트 작성 통계 대시보드 제공 |
| 기타 | 관리자 인증/보안 | 관리자 로그인, 세션 기반 인증, API Key 관리 등 |

---

## 2024년 주요 변경 이력

- **2024.06**
  - UI/UX 전면 통일: 네비게이션, 푸터, 폰트, 카드/테이블/버튼 등 모든 페이지 일관화
  - 공통 CSS(`common.css`), 공통 네비(`_navbar.html`) 도입
  - 관리자 페이지 탭별 대시보드, 키워드/포스트/크롤링/시스템 관리 고도화
  - 생성 기록 페이지: 가상 스크롤 제거, 전체 스크롤/전체 리스트 항상 표시로 변경
  - 상세 모달 내 ```html 문구 자동 제거
  - 포스트 일괄 삭제/내보내기/복원/엑셀 내보내기(선택/전체) 프론트/백엔드/DB 레이어 완비
  - openpyxl 기반 xlsx 내보내기, 미설치 시 pip 안내
  - Pydantic v2 마이그레이션, field_serializer 등 직렬화/타입/None 처리 보완
  - 대량 데이터 환경에서의 성능 최적화 및 버그 수정
  - JS 함수/이벤트/검색/정렬/삭제 등 실시간 반영 및 반복 개선 구조

---

## 이전 주요 업데이트 이력

- **2023.12**
  - 프로젝트 초기화, FastAPI 기반 기본 구조 설계
  - OpenAI/DeepL API 연동, 기본 크롤러/번역/포스트 생성 기능 구현

- **2024.01**
  - 관리자 로그인/세션 인증, API Key 관리 기능 추가
  - 키워드 블랙/화이트리스트 관리, 키워드 통계 대시보드 추가

- **2024.02**
  - 사이트별 크롤러 패턴 관리, 크롤링 실패 리포트/모니터링 도구 추가
  - 포스트 생성 기록(히스토리) 페이지, 상세 모달, 검색/정렬 기능 구현

- **2024.03**
  - 대량 데이터 환경 대응: 일괄 삭제/내보내기/복원 API, 프론트엔드 UI 추가
  - Pydantic v2 마이그레이션, 직렬화/타입/None 처리 보완

- **2024.04**
  - 엑셀(xlsx) 내보내기(openpyxl), 관리자 대시보드 UI 고도화
  - 공통 CSS/폰트/네비게이션/푸터 통일, 전체 UI/UX 리뉴얼

- **2024.05**
  - 실시간 통계(일자별 API/크롤링/포스트), 크롤링 현황판, 문제 사이트 자동 식별
  - JS/이벤트/검색/정렬/삭제 등 실시간 반영 및 반복 개선 구조

---

## 📋 요구사항

- Python 3.8+
- OpenAI API 키
- DeepL API 키

## 🛠️ 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd ai-seo-blogger
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp .env.example .env
```

`.env` 파일을 편집하여 API 키를 설정하세요:
```env
OPENAI_API_KEY=your_openai_api_key_here
DEEPL_API_KEY=your_deepl_api_key_here
```

### 5. 데이터베이스 초기화
```bash
cd app
python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"
```

## 🚀 실행 방법

### 개발 서버 실행
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 프로덕션 서버 실행
```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000
```

브라우저에서 `http://localhost:8000`으로 접속하세요.

## 📁 프로젝트 구조

```
ai-seo-blogger/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── config.py            # 설정 관리
│   ├── database.py          # 데이터베이스 연결
│   ├── models.py            # SQLAlchemy 모델
│   ├── crud.py              # 데이터베이스 CRUD 작업
│   ├── schemas.py           # Pydantic 스키마
│   ├── exceptions.py        # 커스텀 예외 클래스
│   ├── routers/
│   │   └── blog_generator.py # API 라우터
│   ├── services/
│   │   ├── crawler.py       # 웹 크롤링 서비스
│   │   ├── translator.py    # 번역 서비스
│   │   └── content_generator.py # AI 콘텐츠 생성
│   ├── utils/
│   │   └── logger.py        # 로깅 유틸리티
│   ├── templates/           # HTML 템플릿
│   └── static/              # 정적 파일
├── tests/                   # 테스트 코드
├── logs/                    # 로그 파일
├── requirements.txt         # Python 의존성
└── README.md
```
>>>>>>> 3e3405d (프로젝트 최초 커밋)
