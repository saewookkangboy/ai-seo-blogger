# To-do — 역할별 업데이트 (Dev Agent Kit)

역할별 상세 항목은 [docs/ROLE_UPDATES.md](docs/ROLE_UPDATES.md)를 참고하세요.  
JSON 형식 To-do: [.project-data/todos.json](.project-data/todos.json)

---

## Phase 1 — 역할별 업데이트

### PM (Project Manager)
- [ ] (high) 신규 기능(AI 윤리·인용 분석) 스펙·To-do 정합성 검토 — 의존: 없음
- [ ] (medium) CHANGELOG·README 범위·일정 반영 및 마일스톤 정리 — 의존: PM 1

### Frontend Developer
- [ ] (high) 결과 표시 컴포넌트 AI 윤리·인용 점수 UI 반영 — 의존: 없음
- [ ] (medium) generator.js·index.js 접근성(a11y)·반응형 점검 — 의존: Frontend 1

### Backend Developer
- [ ] (high) blog_generator 라우터 AI 윤리·타겟 분석 API 연동 검토 — 의존: 없음
- [ ] (medium) API 에러 형식·버전·입력 검증 일관성 점검 — 의존: Backend 1

### Server/DB Developer
- [ ] (high) BlogPost 스키마(ai_ethics_score 등) 마이그레이션·인덱스 확인 — 의존: 없음
- [ ] (medium) run_server.py·배포(ECS/Docker) 설정 검토 — 의존: Server/DB 1

### Security Manager
- [ ] (high) API 키·환경변수 노출 검사 및 PRODUCTION_SECURITY 반영 — 의존: 없음
- [ ] (medium) 사용자 입력 검증·이스케이프(OWASP) 점검 — 의존: Security 1

### UI/UX Designer
- [x] (high) **전체 디자인 리뉴얼 — 모노크롬·미니멀** (`.spec-kit/03-ui-ux-renewal.md`) — 완료
- [ ] (medium) 결과 플로우(생성→윤리/인용 표시) 사용자 플로우 정리 — 의존: Frontend 1
- [ ] (low) 네비게이션·디자인 시스템 일관성 점검 — 의존: UI/UX 1

### AI Marketing Researcher
- [ ] (high) AI_SEO_AEO_GEO_GUIDELINES·seo_guidelines 반영 여부 검토 — 의존: 없음
- [ ] (medium) 생성 콘텐츠 GEO(FAQ/HowTo/Article 스키마)·인용 신뢰도 강화 — 의존: AI Marketing 1

---

## Vercel 배포 (Server/DB) — P0 안정화

- [x] (high) **Vercel 배포 사양·진입점·vercel.json 적용** (`.spec-kit/04-vercel-deployment.md`) — 완료
- [x] (P0) **main.py _register_routers() 문법 오류 수정** — 라우터 등록 정상화
- [x] (P0) **SESSION_SECRET 환경변수 적용** — 프로덕션 보안 (config.session_secret, SESSION_SECRET)
- [x] (P0) **Vercel comprehensive_logger 더미** — LogLevel, LogCategory export 추가
- [ ] (high) Vercel 환경 변수(DB, API 키, SESSION_SECRET) 설정 및 문서화 — 의존: Vercel 1
- [ ] (medium) vercel deploy 또는 CLI/Claim URL로 실제 배포 및 /health 검증 — 의존: Vercel 2

---

## 진행 방법

- 역할을 지정해 작업 시: "PM 역할로 To-do 검토해줘", "Frontend 역할로 결과 화면 점검해줘" 등으로 요청
- 항목 완료 시 위 체크박스 `[ ]` → `[x]` 로 변경하고, `.project-data/todos.json`의 `status`를 `completed`로 업데이트

*마지막 업데이트: 2025-02-03*
