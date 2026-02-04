# 역할별 업데이트 항목 (Dev Agent Kit)

이 문서는 **각 업무 역할(Agent Role)별로** 이 프로젝트에서 진행·검토할 업데이트 항목을 정리한 것입니다.  
To-do 상세는 [TODO.md](../TODO.md) 및 [.project-data/todos.json](../.project-data/todos.json)을 참고하세요.  
**서비스 고도화·차별화** 스펙: [docs/specs/enhancement-differentiation.md](specs/enhancement-differentiation.md)

---

## 1. PM (Project Manager)

| 초점 | 업데이트 항목 | 참고 |
|------|----------------|------|
| 범위·일정·우선순위 | 신규 기능(AI 윤리, 인용 분석) 스펙과 To-do 정합성 검토 | AI_ETHICS_FEATURE.md, CITATION_ANALYSIS_FEATURE.md |
| 스펙·To-do 정합성 | CHANGELOG·README에 범위·일정 반영, 마일스톤 정리 | CHANGELOG.md, README.md |
| 리스크·의존성 | AI 윤리/인용 평가 실패 시 플로우, API 의존성 식별 | blog_generator 라우터, 서비스 의존성 |

**체크리스트**
- [ ] AI 윤리·인용 분석 기능이 스펙 문서와 일치하는지 검토
- [ ] CHANGELOG에 최근 변경사항 반영
- [ ] Phase 1 마일스톤과 역할별 To-do 매핑 확인

---

## 2. Frontend Developer

| 초점 | 업데이트 항목 | 참고 |
|------|----------------|------|
| UI/UX, 접근성(a11y), 반응형 | 결과 표시에 AI 윤리·인용 점수 UI 반영 | _result_display.html, generator.js, index.js |
| 컴포넌트·상태 관리 | generator.js·index.js 접근성·반응형 점검 | app/static/js/ |
| 성능(번들, 렌더링) | 결과 로딩·표시 시 불필요 리렌더 방지 | components/generator.js, pages/index.js |

**체크리스트**
- [ ] AI 윤리 점수·인용 분석 결과를 결과 패널에 표시
- [ ] 키보드·스크린리더 접근성(a11y) 점검
- [ ] 모바일/태블릿 반응형 레이아웃 확인

---

## 3. Backend Developer

| 초점 | 업데이트 항목 | 참고 |
|------|----------------|------|
| API 설계·에러 형식 | blog_generator 라우터와 AI 윤리·타겟 분석 서비스 연동 검토 | routers/blog_generator.py, services/ai_ethics_evaluator.py, target_analyzer.py |
| 비동기·재시도 | API 응답 시간·타임아웃, 재시도 정책 | blog_generator 엔드포인트 |
| 인증·입력 검증 | API 에러 형식·버전·입력 검증 일관성 | schemas, 라우터 검증 |

**체크리스트**
- [ ] 블로그 생성 플로우에 AI 윤리·인용 평가 호출이 올바르게 연동되는지 확인
- [ ] 에러 응답 형식 통일(HTTP 상태·메시지·코드)
- [ ] 요청 바디·쿼리 입력 검증(Pydantic) 적용 여부 점검

---

## 4. Server/DB Developer

| 초점 | 업데이트 항목 | 참고 |
|------|----------------|------|
| DB 스키마·마이그레이션 | BlogPost에 ai_ethics_score, ai_ethics_evaluation 등 컬럼 마이그레이션·인덱스 | models.py, migrate_db.py, init_db.py |
| 인프라·배포 | run_server.py·ECS/Docker 설정 검토 | run_server.py, Dockerfile, aws/ |
| 백업·복구 | DB 백업·복구 절차 문서화 | AWS_DEPLOYMENT_GUIDE.md 등 |

**체크리스트**
- [ ] ai_ethics_score, ai_ethics_evaluation, ai_ethics_evaluated_at 등 스키마 반영 및 마이그레이션 실행
- [ ] 조회 성능을 위한 인덱스 필요 시 추가
- [ ] run_server.py와 기존 run.py·uvicorn 실행 방식 정리

---

## 5. Security Manager

| 초점 | 업데이트 항목 | 참고 |
|------|----------------|------|
| 시크릿·API 키 | API 키·환경변수 노출 검사, PRODUCTION_SECURITY_ANALYSIS 반영 | .env.example, config, PRODUCTION_SECURITY_ANALYSIS.md |
| 입력 검증·이스케이프 | 사용자 입력 검증·XSS 등 OWASP 점검 | 라우터, 템플릿 렌더링 |
| 감사 로그 | 민감 API 호출 로깅 여부 | comprehensive_logger, 라우터 |

**체크리스트**
- [ ] 코드·커밋에 API 키/시크릿 없음 확인, .env·시크릿 매니저 사용만 사용
- [ ] 사용자 입력(키워드, 설정 등) 검증·이스케이프 적용
- [ ] PRODUCTION_SECURITY_ANALYSIS 권장사항 적용 여부 검토

---

## 6. UI/UX Designer

| 초점 | 업데이트 항목 | 참고 |
|------|----------------|------|
| 사용자 플로우 | 생성 → 윤리/인용 결과 표시 플로우 정리 | index.html, _result_display.html, generator.js |
| 디자인 시스템 | 네비게이션·버튼·카드 등 컴포넌트 일관성 | _navbar.html, static/css, 템플릿 |
| 접근성·다국어 | 라벨·안내 문구, 필요 시 다국어 고려 | 템플릿, static |

**체크리스트**
- [ ] 블로그 생성 완료 후 윤리·인용 점수가 자연스럽게 노출되는 플로우 확인
- [ ] 네비게이션·결과 영역 시각적 계층·일관성 점검
- [ ] 중요 액션에 대한 라벨·피드백 메시지 명확성 확인

---

## 7. AI Marketing Researcher

| 초점 | 업데이트 항목 | 참고 |
|------|----------------|------|
| 키워드·경쟁 분석 | AI_SEO_AEO_GEO_GUIDELINES, seo_guidelines 반영 여부 검토 | AI_SEO_AEO_GEO_GUIDELINES_REPORT.md, app/seo_guidelines.py |
| AI SEO·GEO | 생성 콘텐츠의 GEO(FAQ/HowTo/Article 스키마)·인용 신뢰도 강화 | 구조화 데이터, 인용 분석 로직 |
| 인용·신뢰도·스키마 | 인용 분석 결과를 콘텐츠 품질·출처 표기에 반영 | ai_ethics_evaluator, target_analyzer, CITATION_ANALYSIS_FEATURE.md |

**체크리스트**
- [ ] SEO·GEO 가이드라인 문서와 실제 생성 파이프라인 정합성 검토
- [ ] FAQ/HowTo/Article 스키마 출력·노출 여부 확인
- [ ] 출처 신뢰도(도메인 기반)가 생성 프롬프트·후처리에 반영되는지 확인

---

## 진행 방법

1. **역할 지정**: "PM 역할로 To-do 검토해줘", "Frontend 역할로 결과 화면 점검해줘" 등으로 요청하면 해당 역할 체크리스트와 용어로 응답합니다.
2. **To-do 추적**: [TODO.md](../TODO.md) 또는 `.project-data/todos.json`에서 항목을 Phase·우선순위별로 관리합니다.
3. **스펙 문서**: 새 기능 사양은 `docs/specs/` 아래 마크다운으로 추가할 수 있습니다. (참고: [reference.md](../.cursor/skills/dev-agent-kit/reference.md))

---

*Dev Agent Kit — Agent Role 기반 개발 워크플로우*
