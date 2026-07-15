# 서비스 고도화 — 전체 역할 기반 (Dev Agent Kit)

## 개요

- **목적**: PM, Frontend, Backend, Server/DB, Security, UI/UX, AI Marketing Researcher 7개 역할 관점에서 현재 서비스를 고도화하고, 스펙·To-do·검증 기준을 일원화한다.
- **적용**: 역할별 체크리스트와 자동화 가능 항목을 정의하고, 단계별로 실행한다.

---

## 1. PM (Project Manager)

| 항목 | 우선순위 | 내용 | 검증 |
|------|----------|------|------|
| 스펙·To-do 정합성 | high | docs/specs·TODO.md·todos.json 간 요구사항 매핑 유지 | 스펙 변경 시 To-do/CHANGELOG 반영 |
| CHANGELOG·README | medium | 고도화·배포·역할별 업데이트 반영 | README에 docs/specs 링크, CHANGELOG 최신화 |
| 마일스톤 정리 | low | Phase 1/2 구분 및 의존성 명시 | TODO.md Phase 구분 명확 |

---

## 2. Frontend

| 항목 | 우선순위 | 내용 | 검증 |
|------|----------|------|------|
| 메타·시맨틱 | high | 페이지별 title, description, lang, role/aria | 검색·접근성 도구 점검 |
| 접근성(a11y) | medium | 포커스·키보드·대체 텍스트·대비 | 키보드만으로 플로우 가능 |
| 반응형·터치 | medium | 768px 브레이크포인트, 44px 터치 영역 | 모바일·데스크톱 레이아웃 확인 |
| 에러·로딩 UI | low | API 실패·타임아웃 시 사용자 메시지 일관 | 에러 시 안내 문구 노출 |

---

## 3. Backend

| 항목 | 우선순위 | 내용 | 검증 |
|------|----------|------|------|
| API 에러 형식 | high | 4xx/5xx 시 JSON 형식 일관 (detail, code) | 동일 스키마로 에러 응답 |
| 입력 검증 | high | Pydantic·길이·타입 검증 유지 | 잘못된 입력 시 422·메시지 |
| 스트리밍·SSE | medium | generate-post-stream 안정성·타임아웃 | 스트림 중단 시 클라이언트 복구 가능 |
| Health·모니터링 | medium | /health, /health/readiness, /health/liveness | 배포 환경에서 헬스 체크 통과 |

---

## 4. Server/DB

| 항목 | 우선순위 | 내용 | 검증 |
|------|----------|------|------|
| 스키마·마이그레이션 | high | BlogPost 등 AI 윤리·인용 컬럼 반영 | migrate_db.py 실행 시 오류 없음 |
| 인덱스·쿼리 | medium | 자주 조회하는 컬럼 인덱스 검토 | 기록·검색 응답 시간 적정 |
| 환경·배포 | medium | run_server.py·Docker·Vercel 설정 문서화 | 배포 가이드와 실제 설정 일치 |

---

## 5. Security

| 항목 | 우선순위 | 내용 | 검증 |
|------|----------|------|------|
| API 키·환경변수 | high | 코드 내 하드코딩 없음, .env·시크릿만 사용 | grep 결과 노출 키 없음 |
| 입력·이스케이프 | high | URL·텍스트 길이·XSS 방지 | 스키마 검증·템플릿 이스케이프 |
| 세션·인증 | medium | 관리자 로그인·SESSION_SECRET 환경변수 | 프로덕션 시 HTTPS·Secure 쿠키 |

---

## 6. UI/UX

| 항목 | 우선순위 | 내용 | 검증 |
|------|----------|------|------|
| 디자인 시스템 | high | 변수·카드·버튼·폼 일관성 | main.css·sanity_style·common 일원화 |
| 사용자 플로우 | medium | 타겟 분석 → 적용 → 생성 → 결과 | 한 화면에서 플로우 완결 |
| 빈 상태·에러 상태 | medium | 데이터 없음·오류 시 안내·CTA | 명확한 다음 행동 유도 |
| 푸터·네비 | low | 연결 서비스·저작권·필수 링크 하단 배치 | 푸터에 GAEO·프롬프트·연락처 |

---

## 7. AI Marketing Researcher

| 항목 | 우선순위 | 내용 | 검증 |
|------|----------|------|------|
| SEO·GEO 가이드라인 | high | seo_guidelines.py·AI_SEO_AEO_GEO 반영 | 생성 프롬프트에 GEO·AIO 반영 |
| 타겟 분석 연동 | high | 키워드·오디언스·경쟁자 → 포스트 적용 | "포스트 작성에 적용" 동작 |
| 인용·신뢰도 | medium | 출처·인용 분석·점수 UI | 결과 화면에 인용 점수 노출 |
| 키워드 밀도·구조 | low | 헤딩·FAQ·HowTo 구조 제안 | 생성물에 구조화 데이터 고려 |

---

## 8. 검증 기준 (통합)

- [x] 모든 역할별 high 항목이 스펙·코드·문서에 반영되었는지 확인
- [x] TODO.md·.project-data/todos.json과 본 스펙의 항목이 매핑 가능
- [x] CHANGELOG에 고도화·역할별 변경 이력 기록
- [x] /health·/health/readiness·/health/liveness JSON 응답, 메인·기록·로그인 페이지 메타·접근성 적용

---

## 9. 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2026-02-03 | 0.2 | 역할별 To-do 실행: Security(translator API 키 제거), Frontend(login 메타·aria), Phase 2 전 항목 완료 처리 |
| 2026-02-03 | 0.1 | 초안: 7역할 고도화 항목·검증 기준 정의 |
