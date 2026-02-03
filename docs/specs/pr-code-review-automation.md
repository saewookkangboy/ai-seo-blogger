# PR 및 코드리뷰 자동화 (Dev Agent Kit 다중 역할)

## 개요

- **목적**: dev-agent-kit의 7가지 Agent Role(PM, Frontend, Backend, Server/DB, Security, UI/UX, AI Marketing Researcher)을 활용해 PR 및 코드리뷰를 자동화한다.
- **범위**: GitHub PR 생성/업데이트 시 변경된 파일을 역할별 체크리스트에 따라 검토하고, 통합 리뷰 코멘트를 생성한다.
- **대상 사용자**: 개발자, 리뷰어, PM

## 요구사항

### 기능 요구사항

- FR-001: PR diff를 분석하여 변경된 파일 목록·유형을 추출한다.
- FR-002: 변경 파일 유형에 따라 적용할 역할(PM, Frontend, Backend, Server/DB, Security, UI/UX, AI Marketing Researcher)을 매핑한다.
- FR-003: 각 역할별 dev-agent-kit 체크리스트(reference.md)를 기반으로 리뷰 템플릿을 생성한다.
- FR-004: GitHub Actions 또는 로컬 스크립트로 PR 리뷰를 자동 실행할 수 있다.
- FR-004-1: `--all` 옵션으로 전체 서비스 파일(Git 추적 파일) 대상 리뷰를 실행할 수 있다 (PR 불필요).
- FR-005: gh CLI를 사용해 PR 코멘트·리뷰 스레드를 조회·처리할 수 있다.
- FR-006: (선택) AI API를 사용해 체크리스트 기반 상세 리뷰를 생성할 수 있다.

### 비기능 요구사항

- NFR-001: gh 인증 후 동작하며, 네트워크 권한이 필요하다.
- NFR-002: CI 환경에서는 API 키 없이 템플릿 기반 리뷰만 생성 가능하다.
- NFR-003: 스크립트는 Python 3.11+ 호환이어야 한다.

## 역할별 적용 범위

| Role | 적용 파일 패턴 | 초점 |
|------|----------------|------|
| **PM** | 전체, `docs/`, `.spec-kit/`, `TODO.md`, `CHANGELOG.md`, `tests/`, `*.md` | 범위·일정·우선순위·리스크, 스펙·To-do 정합성 |
| **Frontend** | `*.html`, `*.js`, `*.css`, `app/static/`, `app/templates/` | UI/UX, 접근성, 반응형, 컴포넌트·상태 관리 |
| **Backend** | `app/`, `routers/`, `services/`, `*.py` | API 설계, 비동기, 보안, 확장성 |
| **Server/DB** | `*.sql`, `migrate*`, `init_db*`, `Dockerfile`, `*.yml`, `aws/`, `Makefile`, `requirements.txt` | 인프라, DB 스키마, 마이그레이션, 성능 |
| **Security** | 전체, `config.py`, `.env`, `env.example` | OWASP, 입력 검증, 시크릿, 암호화 |
| **UI/UX** | `templates/`, `static/`, `*.html`, `*.css` | 사용자 플로우, 디자인 시스템, 접근성 |
| **AI Marketing Researcher** | `content_generator*`, `seo*`, `target_analyzer`, `keyword_manager`, `crawler*`, `*.md` | SEO, AI SEO, GEO, 인용·신뢰도 |

## 검증 기준

- [ ] PR diff 기반으로 변경 파일→역할 매핑이 정확하다.
- [ ] 7가지 역할의 체크리스트가 리뷰 출력에 반영된다.
- [ ] GitHub Actions에서 `pull_request` 트리거 시 워크플로우가 실행된다.
- [ ] gh CLI로 현재 브랜치 PR의 리뷰·코멘트를 조회·처리할 수 있다.

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2025-02-03 | 0.1 | 초안 작성 |
