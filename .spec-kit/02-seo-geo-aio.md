# SEO / AI SEO / GEO / AIO 최적화 사양

## 개요

- **목적**: 생성 콘텐츠 및 사이트의 SEO·AI SEO·GEO·AIO 요구사항 충족
- **범위**: 메타·시맨틱·스키마·키워드·인용·성능·접근성
- **참조**: `AI_SEO_AEO_GEO_GUIDELINES_REPORT.md`, `app/services/seo_analyzer.py`, `app/seo_guidelines.py`, `.cursor/skills/dev-agent-kit/reference.md`, **생성 콘텐츠 적용**: `.spec-kit/03-content-creation.md`, `app/services/content_generator.py`

## 요구사항 (체크리스트 반영)

### SEO

- [ ] title, meta description, Open Graph
- [ ] 시맨틱 HTML (h1~h6, article, section)
- [ ] sitemap.xml, robots.txt
- [ ] JSON-LD (Organization, Article, BreadcrumbList 등)
- [ ] canonical URL, 404/리다이렉트

### AI SEO

- [ ] 타겟 키워드·LSI 키워드
- [ ] 키워드 밀도·가독성
- [ ] 경쟁 키워드·제안 문구 반영
- [ ] 제목·헤딩·첫 문단 최적화

### GEO

- [ ] FAQ 스키마 (Question/Answer)
- [ ] HowTo 스키마 (단계별)
- [ ] Article 스키마 (headline, author, datePublished)
- [ ] 인용·출처·신뢰도 강화
- [ ] AI 엔진 친화 구조(명확한 문단·리스트)

### AIO (종합)

- [ ] SEO·AI SEO·GEO 요약, 성능·접근성·보안 요약
- [ ] 단일 리포트 템플릿 적용 가능(reference.md AIO 리포트 템플릿)

## 검증 기준

- [ ] 생성 포스트에 메타·헤딩·키워드 분석이 적용됨
- [ ] 출처/인용 분석(ai_ethics, citation)과 GEO 요구사항 정합성
- [ ] 프로젝트 내 가이드라인 문서와 스펙 버전 일치
- [ ] 콘텐츠 생성 시 03-content-creation.md 체크리스트(AI SEO·GEO·시맨틱 HTML)가 프롬프트에 반영됨

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2025-02-03 | 0.1 | dev-agent-kit SEO/GEO/AIO 체크리스트 사양화 |
| 2025-02-03 | 0.2 | 생성 콘텐츠 참조(03-content-creation) 및 검증 기준 보강 |
