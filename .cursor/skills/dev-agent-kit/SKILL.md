---
name: dev-agent-kit
description: Spec-kit 사양 문서, To-do 관리, Agent Role 기반 개발, SEO/AI SEO/GEO/AIO 최적화, API 키 관리 등 dev-agent-kit 워크플로우를 Cursor에서 수행. 사용자가 사양 문서화, 작업 관리, 역할 기반 개발, SEO·GEO 분석, 키워드 최적화를 요청할 때 적용.
---

# Dev Agent Kit (Cursor 서브에이전트)

[dev-agent-kit](https://github.com/saewookkangboy/dev-agent-kit) 기능을 Cursor 에이전트에서 수행하기 위한 스킬. Spec-kit, To-do, Agent Roles, SEO/GEO/AIO 최적화를 워크플로우로 적용한다.

## 적용 시점 (Trigger)

- 사양 문서 작성·관리, 요구사항 문서화
- To-do/작업 목록 생성·추적·마일스톤 관리
- 역할 기반 개발(PM, Frontend, Backend, Security, UI/UX 등)
- **PR·코드리뷰 자동화** — 모든 역할을 활용한 PR 리뷰 (예: `scripts/pr_review_multi_role.py --post`)
- SEO·AI SEO·GEO·AIO 분석·최적화 요청
- API 키·토큰 관리·보안 가이드
- 프로젝트 초기화·개발 워크플로우 설계

## 1. Spec-kit (사양 문서)

- **목적**: 요구사항·사양 문서 관리, 버전·검증 일관성 유지
- **동작**:
  - 새 사양이 요청되면 `docs/specs/` 또는 `.spec-kit/` 하위에 마크다운 문서 생성
  - 문서 구조: 제목, 개요, 요구사항(기능/비기능), 검증 기준, 변경 이력
  - 기존 사양 수정 시 변경 이력 섹션 갱신
- **검증**: 요구사항이 테스트/체크리스트와 매핑 가능한지 확인

자세한 템플릿·규칙은 [reference.md](reference.md)의 Spec-kit 섹션 참고.

## 2. To-do 및 단계별 진행

- **목적**: 작업 항목 생성·우선순위·마일스톤·의존성 관리
- **동작**:
  - 작업 요청 시 `TODO.md` 또는 `.project-data/todos.json` 형식으로 항목 추가
  - 우선순위: `high` / `medium` / `low`, 마일스톤(Phase 1, 2 등) 표기
  - 의존 작업이 있으면 명시
- **형식 예** (마크다운):

```markdown
## Phase 1
- [ ] (high) 작업 A — 의존: 없음
- [ ] (medium) 작업 B — 의존: 작업 A
```

JSON 사용 시 reference.md의 To-do 스키마 참고.

## 3. Agent Role 시스템

요청·컨텍스트에 따라 아래 역할의 관점으로 응답한다.

| Role | 초점 |
|------|------|
| **PM** | 범위·일정·우선순위·리스크, 스펙·To-do 정합성 |
| **Frontend** | UI/UX, 접근성, 반응형, 컴포넌트·상태 관리 |
| **Backend** | API 설계, 비동기, 보안, 확장성 |
| **Server/DB** | 인프라, DB 스키마, 마이그레이션, 성능 |
| **Security** | 인증/인가, 입력 검증, 시크릿, OWASP |
| **UI/UX** | 사용자 플로우, 와이어프레임, 디자인 시스템 |
| **AI Marketing Researcher** | 키워드, 경쟁 분석, AI SEO·GEO 관점 |

- 사용자가 역할을 지정하면 해당 역할의 체크리스트와 용어를 사용한다.
- 역할 미지정 시 작업 유형(사양/프론트/백엔드/SEO 등)으로 역할을 추론해 적용한다.

## 4. SEO / AI SEO / GEO / AIO 최적화

- **SEO**: 메타 태그, 제목·설명, 시맨틱 HTML, sitemap/robots.txt, 구조화 데이터(JSON-LD) 검증
- **AI SEO**: 키워드 리서치, 키워드 밀도·가독성, 경쟁 키워드 분석, 제안 문구 반영
- **GEO**: 생성형 엔진(ChatGPT, Claude, Perplexity, Gemini 등) 친화 구조 — FAQ, HowTo, Article 스키마, 인용·신뢰도 강화
- **AIO**: SEO + AI SEO + GEO 종합, 성능·접근성·보안 요약, 단일 리포트 템플릿 제안

요청이 “SEO 분석”, “GEO 맞춤”, “키워드 최적화” 등이면 해당 영역 체크리스트를 reference.md 기준으로 적용하고, 필요 시 프로젝트 내 기존 문서(예: AI_SEO_AEO_GEO_GUIDELINES_REPORT.md)를 참조한다.

## 5. API 키·토큰

- 코드/커밋에 API 키를 넣지 않는다. `.env`·환경 변수·시크릿 매니저 사용
- 문서화 시 `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` 등은 placeholder만 기술
- 사용량·비용 모니터링이 필요하면 “API 키 사용량 추적” 요청 시 로깅·캐싱 전략을 제안

## 6. 프로젝트 초기화·워크플로우

- “dev-agent-kit 스타일로 프로젝트 셋업” 요청 시:
  - `docs/specs/` 또는 `.spec-kit/`, To-do용 `TODO.md` 또는 `.project-data/` 구조 제안
  - README에 Spec·To-do·Role·SEO/GEO 참조 링크 추가
  - (선택) FastAPI 백엔드 사용 시 `api/` 구조·엔드포인트 설계 제안

## CLI와의 관계

사용자 환경에 [dev-agent-kit](https://github.com/saewookkangboy/dev-agent-kit) CLI가 설치되어 있으면:

- `dev-agent todo add/list`, `dev-agent spec create/list`, `dev-agent role set`, `dev-agent seo/ai-seo/geo/aio` 등 CLI 명령을 실행하도록 안내하거나, 터미널 명령을 대신 실행할 수 있다.
- CLI가 없으면 위 1~6 워크플로우를 파일 편집·문서 생성·체크리스트로 동일하게 수행한다.

## 추가 자료

- 상세 템플릿·스키마·역할별 체크리스트: [reference.md](reference.md)
- 사용 예시: [examples.md](examples.md)
- 원본 저장소: https://github.com/saewookkangboy/dev-agent-kit
