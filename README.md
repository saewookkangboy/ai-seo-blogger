# AI-Powered SEO Blog Post Generator

AI를 활용하여 특정 키워드에 대한 해외 자료를 수집, 번역, 요약하고 SEO에 최적화된 블로그 초안을 생성하는 프로젝트입니다.

## 🚀 주요 기능

- **AI 콘텐츠 생성**: OpenAI GPT-4, Gemini 2.0 Flash 기반 블로그 포스트 생성
- **자동 번역**: DeepL, Gemini, OpenAI API 기반 다중 번역 시스템
- **웹 크롤링**: 주요 SEO 사이트 자동 크롤링 및 자료 수집
- **SEO 최적화**: AI SEO, AEO, GEO, AIO 등 최신 SEO 가이드라인 적용
- **관리자 대시보드**: 포스트 관리, 키워드 관리, 통계 모니터링
- **Google Drive 통합**: 자동 백업 및 Google Docs Archive 기능

## 📋 요구사항

### 시스템 요구사항
- **Python**: 3.13+ (권장: Python 3.13.5)
- **운영체제**: Windows, macOS, Linux
- **메모리**: 최소 4GB RAM (권장: 8GB+)
- **저장공간**: 최소 1GB 여유 공간
- **네트워크**: 인터넷 연결 필수 (API 호출용)

### API 키 요구사항
- **OpenAI API 키**: GPT-4 모델 사용을 위한 유효한 API 키
- **Google Gemini API 키**: Gemini 2.0 Flash 모델 사용을 위한 API 키
- **DeepL API 키**: 번역 서비스용 API 키 (선택사항)
- **Google Drive API**: Google Cloud Console에서 OAuth 2.0 클라이언트 ID 및 시크릿 설정 (선택사항)

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
cp env.example .env
```

`.env` 파일을 편집하여 API 키를 설정하세요:
```env
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
DEEPL_API_KEY=your_deepl_api_key_here

# Google Drive API 설정 (선택사항)
GOOGLE_DRIVE_CLIENT_ID=your_google_drive_client_id_here
GOOGLE_DRIVE_CLIENT_SECRET=your_google_drive_client_secret_here

# Google Docs Archive 설정 (선택사항)
GOOGLE_DOCS_ARCHIVE_ENABLED=true
GOOGLE_DOCS_ARCHIVE_FOLDER=AI_SEO_Blogger_Archive
GOOGLE_DOCS_AUTO_ARCHIVE=true
```

### 5. 데이터베이스 초기화
```bash
python init_db.py
```

## 🚀 실행 방법

### 개발 서버 실행
```bash
python run.py
```

또는 직접 실행:
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

브라우저에서 `http://localhost:8000`으로 접속하세요.

### 프로덕션 서버 실행
```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🛠️ Makefile 명령어

```bash
make install     # 의존성 패키지 설치
make run         # 개발 서버 실행
make run-prod    # 프로덕션 서버 실행
make optimize    # 시스템 최적화
make clean       # 빠른 정리 (캐시 파일만)
make test        # 테스트 실행
make test-api    # API Key 정상작동 확인
make test-drive  # Google Drive API 테스트
make init-db     # 데이터베이스 초기화
make setup       # 전체 설정 (install + init-db)
make help        # 도움말 표시
```

## 📁 프로젝트 구조

```
ai-seo-blogger/
├── .spec-kit/                    # dev-agent-kit 사양 문서
│   ├── 00-ai-seo-blogger-overview.md
│   ├── 01-blog-generation-api.md
│   └── 02-seo-geo-aio.md
├── .project-data/                # dev-agent-kit To-do (JSON)
│   └── todos.json
├── app/                          # 메인 애플리케이션 디렉토리
│   ├── main.py                   # FastAPI 애플리케이션 진입점
│   ├── config.py                 # 설정 관리
│   ├── database.py               # 데이터베이스 연결
│   ├── models.py                 # SQLAlchemy 모델
│   ├── crud.py                   # 데이터베이스 CRUD 작업
│   ├── schemas.py                # Pydantic 스키마
│   ├── routers/                  # API 라우터
│   │   ├── blog_generator.py     # 블로그 생성 API
│   │   ├── feature_updates.py    # 기능 업데이트 API
│   │   ├── news_archive.py       # 뉴스 아카이브 API
│   │   └── google_drive.py      # Google Drive API
│   ├── services/                 # 비즈니스 로직 서비스
│   │   ├── content_generator.py # AI 콘텐츠 생성
│   │   ├── translator.py        # 번역 서비스
│   │   ├── seo_analyzer.py      # SEO 분석
│   │   ├── crawler.py           # 웹 크롤러
│   │   └── ...                  # 기타 서비스
│   ├── templates/                # HTML 템플릿
│   │   ├── index.html           # 메인 페이지
│   │   ├── admin.html           # 관리자 페이지
│   │   └── ...
│   └── static/                   # 정적 파일
├── tests/                        # 테스트 코드
├── TODO.md                       # dev-agent-kit To-do (마크다운)
├── requirements.txt              # Python 의존성
├── Dockerfile                    # Docker 설정
├── docker-compose.yml            # Docker Compose 설정
├── Makefile                      # 빌드 스크립트
└── README.md                     # 프로젝트 문서
```

## 🤖 Cursor Dev Agent Kit 스킬

이 프로젝트에는 [dev-agent-kit](https://github.com/saewookkangboy/dev-agent-kit) 기능을 Cursor에서 사용할 수 있는 **프로젝트 스킬**이 포함되어 있습니다.

- **위치**: `.cursor/skills/dev-agent-kit/`
- **기능**: Spec-kit 사양 문서, To-do 관리, Agent Role 기반 개발, SEO/AI SEO/GEO/AIO 최적화, API 키 관리
- **사용법**: 채팅에서 "사양 문서 만들어줘", "To-do 추가해줘", "Backend 역할로 API 리뷰해줘", "SEO·GEO 분석해줘" 등으로 요청하면 해당 워크플로우가 적용됩니다.

### dev-agent-kit 참조 링크

| 항목 | 경로/문서 |
|------|-----------|
| **역할별 업데이트** | [docs/ROLE_UPDATES.md](docs/ROLE_UPDATES.md) — PM, Frontend, Backend, Server/DB, Security, UI/UX, AI Marketing 역할별 진행 항목 |
| **To-do** | [TODO.md](TODO.md), [.project-data/todos.json](.project-data/todos.json) |
| **Spec (사양)** | [.spec-kit/](.spec-kit/), [docs/specs/](docs/specs/) — 사양 문서 |
| **Role (역할)** | [.cursor/skills/dev-agent-kit/reference.md](.cursor/skills/dev-agent-kit/reference.md) — PM, Frontend, Backend, Security, UI/UX, AI Marketing Researcher |
| **SEO / GEO** | [AI_SEO_AEO_GEO_GUIDELINES_REPORT.md](AI_SEO_AEO_GEO_GUIDELINES_REPORT.md), [.spec-kit/02-seo-geo-aio.md](.spec-kit/02-seo-geo-aio.md) |
| **상세 템플릿·예시** | [.cursor/skills/dev-agent-kit/reference.md](.cursor/skills/dev-agent-kit/reference.md), [examples.md](.cursor/skills/dev-agent-kit/examples.md) |

각 업무 역할별로 진행할 업데이트는 [docs/ROLE_UPDATES.md](docs/ROLE_UPDATES.md)를 참고하고, 채팅에서 "PM 역할로 To-do 검토해줘", "Frontend 역할로 결과 화면 점검해줘"처럼 **역할을 지정**해 요청하면 해당 관점으로 진행할 수 있습니다.

## 📚 추가 문서

- [CHANGELOG.md](CHANGELOG.md) - 상세한 변경 이력
- [HISTORY.md](HISTORY.md) - 프로젝트 주요 업데이트 이력
- [API_SETUP_GUIDE.md](API_SETUP_GUIDE.md) - API 설정 가이드
- [AI_SEO_BLOGGER_ARCHITECTURE.md](AI_SEO_BLOGGER_ARCHITECTURE.md) - 아키텍처 문서
- [GOOGLE_DRIVE_OAUTH_SETUP.md](GOOGLE_DRIVE_OAUTH_SETUP.md) - Google Drive OAuth 설정 가이드

## 📝 라이선스

이 프로젝트는 개인 사용 목적으로 개발되었습니다.

## 🤝 기여

이슈나 개선 사항이 있으면 이슈를 등록해주세요.
