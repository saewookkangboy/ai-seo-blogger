# Vercel 배포 사양

## 개요

- **목적**: AI SEO Blogger FastAPI 앱을 Vercel 서버리스 플랫폼에 배포하여 프리뷰/프로덕션 URL 제공
- **범위**: 진입점 설정, vercel.json, 정적 자원, 환경 변수 가이드, 배포 절차
- **대상 사용자**: 개발자, DevOps, CI/CD

## 요구사항

### 기능 요구사항

| ID | 요구사항 | 상태 |
|----|----------|------|
| FR-V01 | Vercel이 인식하는 FastAPI 진입점 제공 (app/index.py 또는 pyproject.toml) | 목표 |
| FR-V02 | vercel.json으로 빌드/출력/rewrites 설정 | 목표 |
| FR-V03 | 정적 파일(app/static) 서빙 방식 정의 (public 또는 앱 마운트) | 목표 |
| FR-V04 | 환경 변수(.env) 문서화 및 Vercel 대시보드 연동 가이드 | 목표 |
| FR-V05 | 배포 후 Preview URL / Claim URL 확인 절차 | 목표 |

### 비기능 요구사항

| ID | 요구사항 | 상태 |
|----|----------|------|
| NFR-V01 | Vercel Functions 번들 250MB 제한 이내 (의존성·캐시 제외) | 목표 |
| NFR-V02 | DB(PostgreSQL 등) 연결 정보는 환경 변수로만 주입, 코드에 미포함 | 목표 |
| NFR-V03 | SessionMiddleware 시크릿은 환경 변수 사용 (프로덕션) | 목표 |

## 검증 기준

- [ ] `vercel dev` 또는 `vercel deploy` 후 Preview URL에서 앱 접근 가능
- [ ] `/health` 등 핵심 API 응답 정상
- [ ] `/static/*` 정적 자원 로드 가능
- [ ] 환경 변수는 Vercel 프로젝트 설정에서만 설정, 저장소에 시크릿 미포함

## 환경 변수 (Vercel 대시보드)

Vercel 프로젝트 설정 → Environment Variables에서 다음을 설정한다. 저장소에는 넣지 않는다.

| 변수명 | 설명 | 필수 |
|--------|------|------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 (또는 SQLite 경로) | 권장 |
| `OPENAI_API_KEY` | OpenAI API 키 | 콘텐츠 생성 시 |
| `SESSION_SECRET` | 세션 암호화용 시크릿 (프로덕션 필수) | 권장 |
| 기타 | `.env.example` 참고 (ANTHROPIC, DEEPL, Google 등) | 기능별 |

## 250MB 제한 대응

- **requirements-vercel.txt** 사용: `vercel.json`의 `installCommand`가 `pip install -r requirements-vercel.txt`를 사용하도록 설정됨.
- **제외 패키지**: selenium, webdriver-manager, pandas, openpyxl, redis, psycopg2-binary (Vercel에서는 SQLite 사용 권장).
- **선택적 기능**: 엑셀 내보내기(openpyxl), Google Drive DataFrame 내보내기(pandas)는 미설치 시 503/에러 메시지로 대체. Selenium 크롤러는 미설치 시 기존 try/except로 비활성화.
- **데이터베이스** (`psycopg2-binary`가 `requirements-vercel.txt`에서 제외됨):
  - **SQLite (기본)**: `requirements-vercel.txt`만 사용 시 `DATABASE_URL`을 SQLite로 두거나 미설정(기본값 `sqlite:///./blog.db`).
  - **PostgreSQL 사용 시**:
    - **방법 A**: 별도 `requirements.txt`를 사용하는 빌드로 전환—`vercel.json`의 `installCommand`를 `pip install -r requirements.txt`로 변경. `requirements.txt`에 `psycopg2-binary`를 포함 (번들 크기 증가·250MB 제한에 주의).
    - **방법 B**: Vercel Postgres 또는 외부 관리형 Postgres(Neon, Supabase, Railway 등) 사용—해당 서비스의 연결 문자열을 `DATABASE_URL`에 설정. **주의**: Python에서 연결하려면 여전히 `psycopg2-binary`가 필요하므로, 방법 A처럼 `requirements.txt` 기반 빌드로 전환해야 함. 즉, PostgreSQL 사용 시 결국 `requirements.txt` + `DATABASE_URL` 설정이 필요.
  - **권장**: 250MB 제한을 지키려면 SQLite 사용. PostgreSQL이 필수면 `requirements.txt` 기반 빌드로 전환 후 `DATABASE_URL`에 외부 Postgres 연결 문자열 설정.

### Vercel 서버리스 제한 사항

`requirements-vercel.txt` / `vercel.json` 방식 사용 시 아래 tradeoff를 인지해야 함.

- **함수 타임아웃**: Hobby 플랜 10초, Pro 플랜 60초. 장시간 요청은 실패할 수 있음.
- **콜드 스타트**: 의존성(import)이 많을수록 첫 요청 지연이 커짐. 250MB 제한 대응으로 경량화했지만 여전히 주의.
- **영구 저장소 없음**: 함수 실행 간 로컬 디스크·메모리 상태가 유지되지 않음. SQLite `./blog.db`도 엣지 함수 환경에서는 쓰기·유지가 보장되지 않을 수 있으므로, 프로덕션 DB는 외부 관리형 DB 권장.
- **백그라운드·크론**: 장시간 작업·주기적 배치가 필요하면 Vercel Cron 또는 외부 스케줄러(예: GitHub Actions, Upstash QStash) 사용.

## 구현 노트 (Server/DB 역할)

- **진입점**: Vercel은 `app/app.py`, `app/index.py`, `app/server.py` 중 하나에서 `app` 인스턴스를 찾음. 현재 앱은 `app/main.py`에 있으므로 `app/index.py`에서 `from app.main import app`로 재노출.
- **정적 파일**: Vercel 권장은 `public/**`이지만, FastAPI 단일 함수 배포 시 앱 내 `app.mount("/static", ...)`로 처리 가능. 필요 시 나중에 `public` 복사 빌드 추가.
- **제한 사항**: Python 런타임 Beta, 250MB 번들 제한. Redis/로컬 파일 등 일부 기능은 Vercel 환경에서 제한될 수 있음.

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2025-02-03 | 0.1 | 초안 (dev-agent-kit 워크플로우) |
| 2025-02-03 | 0.2 | PostgreSQL 설정 명확화, Vercel 서버리스 제한 사항 섹션 추가 |
| 2025-02-04 | 0.3 | P0 안정화: main.py 라우터 수정, SESSION_SECRET env, comprehensive_logger 더미(LogLevel/LogCategory), pyproject.toml |
