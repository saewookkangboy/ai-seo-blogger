# 출처 및 인용 분석 기능

## 개요

AI 윤리 평가 시스템에 출처 및 인용에 대한 체크 포인트와 URL 검증 알고리즘이 추가되었습니다. 생성된 콘텐츠의 출처 신뢰도, 인용 형식, URL 유효성을 종합적으로 분석합니다.

## 주요 기능

### 1. URL 추출 및 검증

#### URL 패턴 감지
- HTTP/HTTPS URL 패턴 감지
- www로 시작하는 URL 감지
- HTML 링크(`<a href>`)에서 URL 추출
- 중복 제거 및 정규화

#### URL 유효성 검사
- URL 파싱 검증 (scheme, netloc 확인)
- 형식 유효성 검사
- 유효/무효 URL 분류 및 통계

### 2. 출처 신뢰도 평가

#### 도메인 기반 신뢰도 평가
신뢰도는 다음 3단계로 분류됩니다:

**높은 신뢰도 (High)**
- `.edu`, `.gov` 도메인
- `.ac.kr`, `.go.kr` 도메인
- Wikipedia, PubMed, IEEE, ACM
- Nature, Science, NEJM, BMJ 등 학술지

**중간 신뢰도 (Medium)**
- `.org`, `.net` 도메인
- 주요 뉴스 미디어 (BBC, Reuters, Forbes, Bloomberg, WSJ, NYTimes)

**낮은 신뢰도 (Low)**
- 블로그 플랫폼 (Blogspot, WordPress, Tumblr)
- `.xyz`, `.info` 도메인

**알 수 없음 (Unknown)**
- 위 카테고리에 해당하지 않는 도메인

### 3. 인용 형식 검증

다음 표준 인용 형식을 감지합니다:

- **APA 형식**: `(Author, 2024)` 또는 `Author (Author, 2024)`
- **MLA 형식**: `(Author 123)` 또는 `"Title" (Author)`
- **Chicago 형식**: `1. Author, "Title"` 또는 `(Author 2024: 123)`
- **URL 형식**: HTTP/HTTPS URL, www URL

### 4. 출처 완전성 검사

다음 항목을 검사합니다:

1. **URL 존재 여부**: 출처 URL이 있는지 확인
2. **인용 형식 사용**: 표준 인용 형식 사용 여부
3. **출처 키워드**: "출처", "참고", "참조" 등 키워드 사용
4. **URL-텍스트 연관성**: URL과 출처 명시의 연관성

### 5. 출처 및 인용 종합 점수

다음 요소를 종합하여 점수를 계산합니다:

- **URL 존재** (최대 30점): URL 개수에 따라 점수 부여
- **URL 유효성** (최대 20점): 유효한 URL 비율
- **출처 신뢰도** (최대 25점): 평균 신뢰도 점수
- **인용 형식** (최대 10점): 표준 인용 형식 사용 여부
- **출처 완전성** (최대 15점): 완전성 점수

## API 응답 구조

### 출처 분석 결과 예시

```json
{
  "citation_score": 75.5,
  "urls_found": [
    "https://example.com/article",
    "https://www.wikipedia.org/wiki/Topic"
  ],
  "url_count": 2,
  "url_validation": {
    "valid_count": 2,
    "invalid_count": 0,
    "valid_urls": ["https://example.com/article", "https://www.wikipedia.org/wiki/Topic"],
    "invalid_urls": [],
    "details": [
      {
        "url": "https://example.com/article",
        "valid": true,
        "domain": "example.com"
      }
    ]
  },
  "citation_formats": ["url", "apa"],
  "citation_keywords": {
    "korean": 2,
    "english": 1
  },
  "source_credibility": {
    "distribution": {
      "high": 1,
      "medium": 1,
      "low": 0,
      "unknown": 0
    },
    "average_score": 66.67,
    "details": {
      "high": [
        {
          "url": "https://www.wikipedia.org/wiki/Topic",
          "domain": "www.wikipedia.org",
          "score": 3
        }
      ],
      "medium": [
        {
          "url": "https://example.com/article",
          "domain": "example.com",
          "score": 2
        }
      ]
    }
  },
  "html_links": [
    {
      "url": "https://example.com/article",
      "link_text": "참고 자료",
      "has_text": true
    }
  ],
  "citation_completeness": {
    "score": 100.0,
    "issues": [],
    "has_urls": true,
    "has_citation_format": true,
    "has_citation_keywords": true
  },
  "recommendations": [
    "출처 및 인용이 적절하게 표시되어 있습니다."
  ]
}
```

## 프론트엔드 UI

출처 및 인용 분석 결과는 "출처 및 인용 분석" 섹션에 표시됩니다:

1. **출처 및 인용 점수**: 종합 점수와 진행 바
2. **발견된 URL**: 유효/무효 URL 목록 및 통계
3. **출처 신뢰도**: 높음/중간/낮음/알 수 없음 분포 및 평균 점수
4. **감지된 인용 형식**: 표준 인용 형식 표시
5. **출처 완전성**: 완전성 점수 및 이슈 목록
6. **출처 개선 권장사항**: 개선 사항 제안

## 사용 예시

### 콘텐츠 생성 시 자동 분석

콘텐츠 생성 시 자동으로 출처 및 인용 분석이 수행됩니다:

```python
# 콘텐츠 생성 후 자동으로 분석
evaluation = await ai_ethics_evaluator.evaluate_content(
    content=generated_content,
    title=title,
    metadata={'ai_mode': 'gemini_2_0_flash'}
)

# 출처 분석 결과 접근
citation_analysis = evaluation['details']['citations']
print(f"출처 점수: {citation_analysis['citation_score']}")
print(f"발견된 URL: {citation_analysis['url_count']}개")
print(f"평균 신뢰도: {citation_analysis['source_credibility']['average_score']}%")
```

### 수동 분석

기존 콘텐츠에 대해 수동으로 분석할 수 있습니다:

```python
citation_analysis = await ai_ethics_evaluator._analyze_citations_and_sources(
    content=html_content,
    text=plain_text
)
```

## 알고리즘 상세

### URL 추출 알고리즘

1. **정규식 패턴 매칭**
   - HTTP/HTTPS URL: `https?://[^\s<>"{}|\\^`\[\]]+`
   - www URL: `www\.[^\s<>"{}|\\^`\[\]]+`
   - HTML 링크: `<a\s+href=["\']([^"\']+)["\']`

2. **정규화**
   - URL 끝의 구두점 제거 (.,;:!?))
   - 중복 제거
   - www URL에 http:// 접두사 추가

### 신뢰도 평가 알고리즘

1. **도메인 추출**: URL에서 netloc 추출
2. **패턴 매칭**: 신뢰도 패턴과 매칭
3. **점수 부여**:
   - 높은 신뢰도: 3점
   - 중간 신뢰도: 2점
   - 낮은 신뢰도: 1점
   - 알 수 없음: 1점 (기본)
4. **평균 계산**: (총 점수 / 최대 점수) × 100

### 인용 형식 감지 알고리즘

1. **패턴 매칭**: 각 인용 형식의 정규식 패턴과 매칭
2. **형식 분류**: 감지된 형식을 리스트로 반환
3. **중복 제거**: 동일 형식 중복 제거

### 완전성 검사 알고리즘

1. **URL 존재**: URL 개수 확인 (2점)
2. **인용 형식**: 표준 형식 사용 여부 (1점)
3. **출처 키워드**: 관련 키워드 사용 여부 (1점)
4. **연관성**: URL과 출처 명시의 연관성 (1점)
5. **점수 계산**: (획득 점수 / 최대 점수) × 100

## 개선 권장사항

시스템은 다음 상황에서 개선 권장사항을 제공합니다:

1. **URL 없음**: "출처 URL을 추가하세요."
2. **무효 URL**: "유효하지 않은 URL N개를 수정하세요."
3. **낮은 신뢰도**: "신뢰할 수 있는 출처(교육기관, 정부기관, 학술지 등)를 사용하세요."
4. **인용 형식 없음**: "표준 인용 형식(APA, MLA, Chicago 등)을 사용하세요."
5. **완전성 부족**: 구체적인 이슈 목록 제공

## 향후 개선 사항

1. **실시간 URL 접근성 검사**: HTTP 요청을 통한 실제 접근 가능 여부 확인
2. **더 많은 인용 형식 지원**: IEEE, Vancouver 등 추가 형식
3. **학술 논문 DOI 검증**: DOI를 통한 논문 정보 확인
4. **출처 일관성 검사**: 동일 출처 반복 인용 검사
5. **인용 맥락 분석**: 인용이 적절한 맥락에서 사용되었는지 검사

## 참고 자료

- [APA Citation Style](https://apastyle.apa.org/)
- [MLA Citation Style](https://style.mla.org/)
- [Chicago Manual of Style](https://www.chicagomanualofstyle.org/)
- [URL Validation Best Practices](https://www.w3.org/TR/url/)

