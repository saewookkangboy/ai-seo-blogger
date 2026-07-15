# Dev Agent Kit — 상세 참조

## Spec-kit 템플릿

### 사양 문서 구조 (docs/specs/ 또는 .spec-kit/)

```markdown
# [사양 제목]

## 개요
- 목적, 범위, 대상 사용자

## 요구사항
### 기능 요구사항
- FR-001: ...
- FR-002: ...

### 비기능 요구사항
- NFR-001: ...
- NFR-002: ...

## 검증 기준
- [ ] 기준 1
- [ ] 기준 2

## 변경 이력
| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| YYYY-MM-DD | 0.1 | 초안 |
```

## To-do 스키마

### 마크다운 (TODO.md)

```markdown
# To-do

## Phase 1
- [ ] (high) 작업 A — 의존: 없음
- [ ] (medium) 작업 B — 의존: 작업 A

## Phase 2
- [ ] (low) 작업 C — 의존: Phase 1 완료
```

### JSON (.project-data/todos.json)

```json
{
  "todos": [
    {
      "id": "1",
      "title": "작업 A",
      "priority": "high",
      "milestone": "Phase 1",
      "status": "pending",
      "dependencies": []
    },
    {
      "id": "2",
      "title": "작업 B",
      "priority": "medium",
      "milestone": "Phase 1",
      "status": "pending",
      "dependencies": ["1"]
    }
  ]
}
```

- `status`: pending | in_progress | completed
- `priority`: high | medium | low

## Agent Role 체크리스트

### PM (Project Manager)
- 범위·일정·우선순위 명확화
- 스펙·To-do 정합성 검토
- 리스크·의존성 식별

### Frontend Developer
- UI/UX, 접근성(a11y), 반응형
- 컴포넌트·상태 관리 일관성
- 성능(번들, 렌더링)

### Backend Developer
- API 설계(REST/GraphQL), 버전·에러 형식
- 비동기·트랜잭션·재시도
- 인증·인가·입력 검증

### Server/DB Developer
- DB 스키마·마이그레이션·인덱스
- 인프라·배포·모니터링
- 백업·복구

### Security Manager
- OWASP Top 10, 입력 검증·이스케이프
- 시크릿·암호화·헤더
- 감사 로그

### UI/UX Designer
- 사용자 플로우·와이어프레임
- 디자인 시스템·토큰
- 접근성·다국어

### AI Marketing Researcher
- 키워드·경쟁 분석
- AI SEO·GEO 관점 콘텐츠
- 인용·신뢰도·스키마

## SEO 체크리스트

- [ ] title, meta description, Open Graph
- [ ] 시맨틱 HTML (h1~h6, article, section)
- [ ] sitemap.xml, robots.txt
- [ ] JSON-LD (Organization, Article, BreadcrumbList 등)
- [ ] canonical URL, 404/리다이렉트

## AI SEO 체크리스트

- [ ] 타겟 키워드·LSI 키워드
- [ ] 키워드 밀도·가독성
- [ ] 경쟁 키워드·제안 문구 반영
- [ ] 제목·헤딩·첫 문단 최적화

## GEO 체크리스트

- [ ] FAQ 스키마 (Question/Answer)
- [ ] HowTo 스키마 (단계별)
- [ ] Article 스키마 (headline, author, datePublished)
- [ ] 인용·출처·신뢰도 강화
- [ ] AI 엔진 친화 구조(명확한 문단·리스트)

## AIO 리포트 템플릿

```markdown
# AIO 종합 분석 — [대상 URL/도메인]

## Executive Summary
- SEO·AI SEO·GEO 요약, 핵심 권장사항

## SEO
- 메타·구조·sitemap·robots·JSON-LD 상태

## AI SEO
- 키워드·가독성·경쟁 분석 요약

## GEO
- 스키마·인용·생성형 엔진 친화도

## 성능·접근성·보안
- Core Web Vitals, a11y, 보안 헤더

## 권장사항 (우선순위)
1. ...
2. ...
```

## CLI 명령 참조 (dev-agent-kit 설치 시)

| 기능 | 예시 명령 |
|------|-----------|
| To-do | `dev-agent todo add "작업" -p high -m "Phase 1"`, `dev-agent todo list` |
| Role | `dev-agent role set --role frontend`, `dev-agent role list` |
| Spec | `dev-agent spec create "제목"`, `dev-agent spec list` |
| SEO | `dev-agent seo analyze URL`, `dev-agent seo sitemap -u URL ...` |
| AI SEO | `dev-agent ai-seo keywords "주제"`, `dev-agent ai-seo optimize "내용" -k 키워드` |
| GEO | `dev-agent geo analyze URL`, `dev-agent geo faq -q Q1 Q2` |
| AIO | `dev-agent aio analyze URL`, `dev-agent aio report -f markdown` |
| API | `dev-agent api:start`, `dev-agent api-key set openai -k "sk-..."` |

원본: https://github.com/saewookkangboy/dev-agent-kit
