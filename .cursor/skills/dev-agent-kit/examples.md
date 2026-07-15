# Dev Agent Kit — 사용 예시

## 예시 1: 사양 문서 생성 요청

**사용자**: "사용자 인증 시스템 사양 문서 만들어줘"

**에이전트 동작**:
- `docs/specs/` 또는 `.spec-kit/` 아래 `user-auth-spec.md` 생성
- reference.md의 Spec-kit 템플릿 적용
- 기능 요구사항(로그인, 로그아웃, 비밀번호 재설정 등), 비기능(보안, 성능), 검증 기준·변경 이력 포함

## 예시 2: To-do 및 Phase 관리

**사용자**: "Phase 1에 컴포넌트 설계랑 API 연동 작업 추가해줘"

**에이전트 동작**:
- `TODO.md` 또는 `.project-data/todos.json`에 항목 추가
- 우선순위·마일스톤(Phase 1) 표기
- 의존성 있으면 명시

## 예시 3: 역할 기반 응답

**사용자**: "지금부터 Backend 역할로 답해줘. 이 API 설계 리뷰해줘"

**에이전트 동작**:
- Backend Developer 역할 체크리스트 적용
- API 설계(엔드포인트, 에러 형식, 인증·인가, 확장성) 관점으로 리뷰

## 예시 4: SEO·GEO 분석

**사용자**: "우리 블로그 URL SEO랑 GEO 관점으로 분석해줘"

**에이전트 동작**:
- SEO: 메타, 시맨틱, sitemap/robots, JSON-LD 검토
- GEO: FAQ/HowTo/Article 스키마, 인용·신뢰도 강화 여부 검토
- reference.md 체크리스트 기준으로 요약·권장사항 제시

## 예시 5: AIO 리포트

**사용자**: "이 사이트 AIO 종합 분석 리포트 만들어줘"

**에이전트 동작**:
- reference.md의 AIO 리포트 템플릿 사용
- SEO + AI SEO + GEO + 성능·접근성·보안 요약
- 우선순위별 권장사항 나열

## 예시 6: 프로젝트 초기화

**사용자**: "dev-agent-kit 스타일로 이 프로젝트 셋업해줘"

**에이전트 동작**:
- `docs/specs/`, To-do용 `TODO.md` 또는 `.project-data/` 구조 제안·생성
- README에 Spec·To-do·Role·SEO/GEO 참조 링크 추가
- (선택) FastAPI 사용 시 `api/` 구조 제안

## 예시 7: 콘텐츠 생성 보완·업데이트

**사용자**: "콘텐츠 생성에 대한 부분을 강력하게 보완/업데이트 해줘"

**에이전트 동작**:
- `.spec-kit/03-content-creation.md` 사양 확인·갱신 (기능/비기능 요구사항, AI SEO·GEO·AIO 체크리스트)
- `app/services/content_generator.py` 프롬프트에 콘텐츠 품질 체크리스트(`_get_content_quality_checklist`) 반영
- reference.md의 AI SEO·GEO 체크리스트와 02-seo-geo-aio.md 정합성 유지
- 메타 설명 160자, 시맨틱 HTML, FAQ/HowTo 친화 구조 등 생성 품질 요구사항 강화

## 예시 8: PR 및 코드리뷰 자동화 (모든 역할 활용)

**사용자**: "이 PR을 모든 역할로 리뷰해줘" / "PR 코드리뷰 자동화해줘"

**에이전트 동작**:
- `scripts/pr_review_multi_role.py` 실행 (`python scripts/pr_review_multi_role.py --post`)
- gh CLI로 현재 브랜치 PR diff·메타데이터 조회 (gh 인증 필요)
- 변경 파일을 7가지 역할(PM, Frontend, Backend, Server/DB, Security, UI/UX, AI Marketing Researcher)에 매핑
- 각 역할별 reference.md 체크리스트 기반 리뷰 마크다운 생성
- PR에 코멘트로 게시 (`--post`) 또는 stdout 출력
- GitHub Actions: PR 생성/업데이트 시 `.github/workflows/pr-review.yml`이 자동 실행되어 리뷰 코멘트 게시
- 상세 사양: `docs/specs/pr-code-review-automation.md`
