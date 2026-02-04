# 콘텐츠 생성 사양 (Content Creation)

**버전 0.1 (구현 반영)** — 요구사항은 코드베이스에 반영되어 있으며, 아래 검증 기준으로 확인함.

## 개요

- **목적**: AI 기반 블로그 포스트 생성 시 품질·일관성·SEO/AI SEO/GEO/AIO 요구사항을 충족하도록 요구사항과 검증 기준을 정의한다.
- **범위**: `create_blog_post`, `_create_blog_post_with_gemini`, `_create_blog_post_with_openai`, `create_enhanced_blog_post` 및 관련 프롬프트·가이드라인 주입 로직.
- **대상**: 콘텐츠 생성 파이프라인, AI SEO 블로그 작가 역할(Agent Role: AI Marketing Researcher 관점), 생성형 엔진(GEO) 친화 콘텐츠.
- **참조**: `app/services/content_generator.py`, `app/seo_guidelines.py`, `app/services/rules.py`, `.cursor/skills/dev-agent-kit/reference.md`, `02-seo-geo-aio.md`.

## 요구사항

### 기능 요구사항 (콘텐츠 생성)

| ID | 요구사항 | 상태 |
|----|----------|------|
| FR-C01 | 프롬프트에 **AI SEO 체크리스트** 반영: 타겟 키워드·LSI 키워드, 키워드 밀도·가독성, 제목·헤딩·첫 문단 최적화 | ✅ |
| FR-C02 | 프롬프트에 **GEO 체크리스트** 반영: FAQ/HowTo/Article 스키마 친화 구조, 인용·출처·신뢰도, 명확한 문단·리스트 | ✅ |
| FR-C03 | 메타 설명 **160자 이내** 명시 및 JSON 출력 스키마에 반영 | ✅ |
| FR-C04 | **시맨틱 HTML** 요구: h1~h6 계층, article/section 의미 구조, 리스트·테이블 활용 | ✅ |
| FR-C05 | **Responsible AI**: 균형 잡힌 관점, 편향 방지, 윤리적 서술 유지 (기존 유지·강화) | ✅ |
| FR-C06 | `ai_mode`별 구조 가이드라인: ai_seo(Schema/헤딩), aeo(FAQ/Q&A), geo(비교·HowTo·출처) | ✅ |
| FR-C07 | 최신 `seo_guidelines`(E-E-A-T, AEO, GEO) 자동 주입 및 규칙 텍스트 병합 | ✅ |
| FR-C08 | 출력 JSON에 `title`, `meta_description`, `content`, `keywords`, `metrics`, `score`, `evaluation`, `ai_analysis`(trust_score, seo_score, ai_summary) 포함 | ✅ |
| FR-C09 | 콘텐츠 생성 사양 버전·체크리스트 출처를 코드 또는 로그에서 추적 가능 | ✅ |

### 비기능 요구사항

| ID | 요구사항 | 상태 |
|----|----------|------|
| NFR-C01 | 프롬프트 길이·토큰을 고려한 가이드라인 압축, 중복 문구 최소화 | ✅ |
| NFR-C02 | Gemini/OpenAI 양쪽 프롬프트에 동일한 품질·체크리스트 기준 적용 (일관성) | ✅ |
| NFR-C03 | API 실패 시 기본 템플릿이 시맨틱 구조(h1, h2, 리스트)를 최소한 유지 | ✅ |

## 콘텐츠 품질 체크리스트 (프롬프트 반영용)

다음 항목은 `content_generator` 프롬프트의 **[콘텐츠 품질 및 최적화]** 섹션에 반영한다.

### AI SEO

- [x] 타겟 키워드·LSI 키워드를 제목·헤딩·첫 문단에 자연스럽게 포함
- [x] 키워드 밀도·가독성 유지 (과도한 키워드 삽입 금지)
- [x] 제목 60자 이내, 메타 설명 160자 이내

### GEO

- [x] FAQ 스키마 친화: 질문-답변 블록 또는 `faq-section` 구조 포함 가능
- [x] HowTo/단계별 가이드: 적절한 경우 번호 리스트·단계 구분
- [x] Article 스키마 친화: headline, 명확한 본문·리스트
- [x] 인용·출처·신뢰도 강화 (주장 시 근거·출처 언급)
- [x] AI 엔진 친화: 명확한 문단·리스트·소제목 구조

### 공통

- [x] 시맨틱 HTML: h1 1회, h2/h3 계층, `<p>`, `<ul>/<ol>`, `<section>` 등
- [x] E-E-A-T: 경험·전문성·권위·신뢰성 신호 (seo_guidelines와 연동)

## 검증 기준

- [x] `content_generator.py` 내 Gemini/OpenAI 프롬프트에 위 체크리스트에 대응하는 문구가 포함되어 있음 (`_get_content_quality_checklist()` → `content_checklist`, 양쪽 프롬프트에 주입)
- [x] 생성 결과 JSON의 `meta_description` 길이가 160자 이내로 검증 가능(후처리 또는 모델 지시): 프롬프트에 "160자 이내" 명시 및 JSON 스키마에 반영됨
- [x] `ai_mode`가 aeo/geo일 때 주입되는 HTML 구조 가이드라인(FAQ, HowTo, 비교 등)이 실제 프롬프트에 포함됨 (`create_blog_post`에서 `structure_guidelines`로 `rule_guidelines`에 추가 후 Gemini/OpenAI에 전달)
- [x] `get_seo_guidelines()` 기반 가이드라인 주입이 `create_blog_post`에서 동작함 (E-E-A-T, AEO, GEO 활성 가이드라인을 `rule_guidelines`에 병합)
- [x] 02-seo-geo-aio.md의 SEO/AI SEO/GEO 항목과 본 사양의 체크리스트가 정합성 유지

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2025-02-03 | 0.1 | dev-agent-kit 콘텐츠 생성 보완: 03-content-creation 사양 신규 작성, AI SEO/GEO/AIO 체크리스트 정의 |

