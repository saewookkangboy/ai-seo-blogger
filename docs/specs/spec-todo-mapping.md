# 스펙 · To-do 매핑 (정합성 검토)

## 목적

docs/specs·TODO.md·.project-data/todos.json 간 요구사항 매핑을 유지하고, 신규 기능(AI 윤리·인용 분석·타겟 분석)이 스펙과 To-do에 반영되었는지 검증한다.

---

## 1. 스펙 문서 ↔ To-do 매핑

| 스펙 문서 | 관련 To-do (Phase) | 비고 |
|-----------|---------------------|------|
| [service-enhancement-all-roles.md](service-enhancement-all-roles.md) | Phase 2 전 항목 (phase2-pm ~ phase2-ai-mkt) | 7역할 고도화·검증 기준 |
| [enhancement-differentiation.md](enhancement-differentiation.md) | Phase 1 UI/UX, AI Marketing, Frontend | 타겟 분석→포스트 연동, GEO·인용 |
| [history-page-ux.md](history-page-ux.md) | Phase 2 UI/UX, Frontend | 기록 페이지 디자인 시스템 |
| [responsive-seamless-ux.md](responsive-seamless-ux.md) | Phase 2 Frontend, UI/UX | 반응형·접근성 |
| [pr-code-review-automation.md](pr-code-review-automation.md) | — | PR 리뷰 자동화 (참고) |

---

## 2. 신규 기능 ↔ 스펙·To-do

### AI 윤리·인용 분석

| 요구사항 | 스펙 반영 | To-do | 구현 위치 |
|----------|-----------|--------|-----------|
| AI 윤리 평가 결과 저장 | service-enhancement-all-roles (Backend) | server-db-1, backend-1 | BlogPost.ai_ethics_*, blog_generator.evaluate_and_save_ai_ethics |
| AI 윤리·인용 점수 UI | enhancement-differentiation, service-enhancement | frontend-1 | _result_display.html (ai-ethics-evaluation, citation-analysis) |
| API: 윤리 평가 조회/재평가 | — | backend-1 | /api/v1/posts/{id}/ai-ethics, evaluate-ai-ethics |

### 타겟 분석

| 요구사항 | 스펙 반영 | To-do | 구현 위치 |
|----------|-----------|--------|-----------|
| 타겟 분석 API | enhancement-differentiation | backend-1 | /api/v1/target/analyze (main.py), target_analyzer.py |
| 타겟 분석 → 포스트 적용 | enhancement-differentiation | frontend-1, uiux-1 | index.js applyTargetToPost, _work_tabs |

---

## 3. 검증 체크

- [x] AI 윤리·인용 분석 기능이 스펙(enhancement-differentiation, service-enhancement-all-roles)에 명시됨
- [x] 해당 기능이 TODO.md Phase 1·2 및 todos.json에 항목으로 존재함
- [x] 구현(blog_generator, _result_display, target_analyzer, main.py)과 스펙·To-do 일치
- [ ] 스펙 변경 시 본 매핑·TODO·CHANGELOG 갱신 (운영 규칙)

---

## 4. 변경 이력

| 날짜 | 변경 내용 |
|------|-----------|
| 2026-02-03 | 초안: 스펙–To-do 매핑, AI 윤리·인용·타겟 분석 검증 |
