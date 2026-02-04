# 블로그 생성 API 사양

## 개요

- **목적**: 키워드/URL 기반 블로그 포스트 생성·스트리밍·파이프라인 제공
- **범위**: `/api/v1` 하위 generate-post*, pipeline*, archive, improve-content, ai-ethics, keyword-statistics 등
- **참조**: `app/routers/blog_generator.py`, `app/services/content_generator.py`, `app/services/content_pipeline.py`

## 요구사항

### 기능 요구사항

- **모델 선택**: 생성·스트리밍·고급 생성 엔드포인트는 경로에 모델명을 두지 않고, 쿼리 파라미터 `?model=gemini-2-flash` 또는 요청 본문 필드 `"model": "gemini-2-flash"`로 모델을 지정한다. 미지정 시 서버 기본 모델 사용.

- FR-B01: `POST /generate-post` — 단일 요청 생성. 모델은 쿼리 `model` 또는 본문 `model`로 선택 (예: `model=gemini-2-flash`, `model=gemini`).
- FR-B02: `POST /generate-post-stream`, `POST /generate-post-pipeline-stream`, `POST /generate-post-pipeline-robust-stream` — 스트리밍. 모델은 쿼리/본문 `model`로 지정.
- FR-B03: `POST /generate-post-pipeline`, `POST /generate-post-pipeline-robust` — 파이프라인 동기
- FR-B04: `GET /pipeline-status/{id}`, `DELETE /pipeline/{id}` — 파이프라인 상태/취소
- FR-B05: `POST /generate-post-enhanced`, `POST /generate-post-improved` — 고급 생성. 모델은 쿼리/본문 `model`로 선택 (예: `model=gemini-2-flash`).
- FR-B06: `POST /posts/{id}/evaluate-ai-ethics`, `GET /posts/{id}/ai-ethics`, `GET /posts/ai-ethics/stats` — AI 윤리
- FR-B07: `POST /posts/generate-from-keyword` — 키워드 기반 생성
- FR-B08: `POST /improve-content`, `POST /improve-content-suggestion` — 콘텐츠 개선
- **FR-B09**: 아카이브
  - `POST /archive/create`, `DELETE /archive/documents/{id}` — 생성·삭제
  - **`GET /archive/documents`** — 문서 목록 조회 (페이지네이션 필수)
    - **페이지네이션 전략**: offset/page 기반. `page`와 `limit` 쿼리 파라미터로 제어.
    - **쿼리 파라미터**:
      - `page` (optional, integer ≥ 1): 요청할 페이지 번호. 기본값 **1**.
      - `limit` (optional, integer 1..max): 페이지당 항목 수. 기본값 **20**, 최대 **100**. **초과 시 반드시 100으로 클램프한다.** 클램프가 발생한 경우(`limit` > 100) 서버는 요청값을 100으로 제한하고, 클라이언트가 조정된 값을 감지할 수 있도록 응답에 경고 헤더를 포함한다: 헤더 이름 **`X-Archive-Limit-Clamped`**, 값 형식 **`requested=<요청값>, used=100`** (예: `X-Archive-Limit-Clamped: requested=150, used=100`).
    - **응답 메타데이터** (목록과 함께 반환할 필드):
      - `total_count` (integer): 전체 문서 개수.
      - `page` (integer): 현재 페이지 번호.
      - `limit` (integer): 현재 요청에 사용된 limit.
      - `total_pages` (integer): 전체 페이지 수 (ceil(total_count / limit), 0일 때 0).
      - `has_next` (boolean): 다음 페이지 존재 여부.
      - `has_previous` (boolean): 이전 페이지 존재 여부.
      - `next_page` (integer | null): 다음 페이지 번호. 없으면 null.
      - `prev_page` (integer | null): 이전 페이지 번호. 없으면 null.
      - (선택) `next_link`, `prev_link`: 다음/이전 페이지의 전체 URL. 제공 시 클라이언트가 그대로 사용 가능.
    - 구현 시 동작: `page`·`limit`으로 offset을 계산(offset = (page - 1) * limit)하고, 동일 정렬(예: 최신순)을 보장하여 목록과 위 메타데이터를 반환.

### API Request/Response Schemas

참조: `app/schemas.py` (PostRequest, PostResponse, ErrorResponse, BlogPostResponse, GenerateFromKeywordRequest, ImproveContentRequest, ImproveContentSuggestionRequest)

#### 공통 모델

| 모델 | 파일 | 설명 |
|------|------|------|
| PostRequest | app/schemas.py | 블로그 생성 요청 (url, text, keywords 등) |
| PostResponse | app/schemas.py | 블로그 생성 응답 (success, message, data) |
| ErrorResponse | app/schemas.py | 에러 응답 — **표준 에러 봉투(Standard Error Envelope)** 준수, 아래 스키마 참조 |

#### 표준 에러 응답 스키마 (Standard Error Envelope)

모든 API 에러 응답은 아래 **단일 JSON 에러 봉투(Standard Error Envelope)**를 사용한다. NFR-B01.1 Security, NFR-B01.2 Performance, NFR-B01.3 Reliability, NFR-B01.4 Scalability, NFR-B01.5 Observability에서 언급하는 에러 코드·HTTP 상태는 본 스키마를 따른다.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| error.code | string | 예 | 기계 판독용 코드 (대문자 스네이크) |
| error.message | string | 예 | 사용자/개발자용 요약 메시지 |
| error.details | object \| array \| null | 아니오 | 추가 상세(검증 오류 목록 등) |
| request_id | string | 예 | 요청 추적용 ID (응답 헤더에도 포함 권장) |
| timestamp | string | 예 | ISO 8601 형식 (예: 2025-02-04T12:00:00Z) |

**HTTP 상태 → error.code 매핑** (주요 코드; 공통 에러 응답 표에 404/500 포함):

| HTTP 상태 | error.code |
|-----------|------------|
| 400 | VALIDATION_ERROR |
| 401 | UNAUTHORIZED |
| 403 | FORBIDDEN |
| 404 | NOT_FOUND |
| 429 | RATE_LIMIT_EXCEEDED |
| 500 | INTERNAL_ERROR |
| 503 | SERVICE_UNAVAILABLE |

**응답 요구사항**:
- 모든 에러 응답 본문에 **request_id** 포함 (필수).
- **429** 응답 시 **Retry-After** 헤더 포함 (필수). 값은 재시도 가능 시각까지의 초 단위 또는 HTTP-date.
- request_id는 응답 헤더 **X-Request-Id**(또는 동일 의미의 헤더)로도 제공하는 것을 권장(SHOULD)한다.

**429 Rate Limit — 표준 에러 봉투 예시**:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-Request-Id: req-abc-12345
Content-Type: application/json
```

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "요청 한도를 초과했습니다. Retry-After 초 후 재시도하세요.",
    "details": { "limit": 60, "window_seconds": 60 }
  },
  "request_id": "req-abc-12345",
  "timestamp": "2025-02-04T12:00:00Z"
}
```

(공통 에러 응답 표 및 엔드포인트별 에러 설명은 위 스키마를 따름.)

---

**PostRequest 검증 규칙**: url ≤ 2000자; text 5~100000자; keywords ≥ 2자 (입력 시).

---

#### FR-B01: POST /generate-post

**요청**: `PostRequest` (app/schemas.py)

| 필드 | 타입 | 필수 | 검증 | 설명 |
|------|------|------|------|------|
| url | string | 아니오* | 1~2000자, http(s):// | 소스 URL (*url 또는 text 중 하나 필수) |
| text | string | 아니오* | 5~100000자 | 직접 입력 텍스트 |
| keywords | string | 아니오 | ≥2자 | SEO 키워드 (미입력 시 자동 추출) |
| rules | string[] | 아니오 | - | 가이드라인 ID 목록 |
| ai_mode | string | 아니오 | - | AI 모드 (예: 블로그, gemini) |
| content_length | string | 아니오 | - | 목표 길이 (기본 "3000") |
| policy_auto | boolean | 아니오 | - | 정책 자동 적용 (기본 false) |

* `url` 또는 `text` 중 하나는 반드시 존재해야 함.

**응답 (성공 200)**: `PostResponse`

```json
{
  "success": true,
  "message": "블로그 포스트가 성공적으로 생성되었습니다.",
  "data": {
    "id": 1,
    "title": "생성된 포스트 제목",
    "content": "<p>HTML 콘텐츠...</p>",
    "keywords": "키워드1, 키워드2",
    "source_url": "https://example.com",
    "created_at": "2025-02-03T12:00:00",
    "ai_mode": "블로그",
    "metrics": {},
    "score": 0,
    "evaluation": "",
    "ai_analysis": {}
  }
}
```

**에러 응답**: `ErrorResponse` — **표준 에러 응답 스키마** (400 → VALIDATION_ERROR 등)

```json
{
  "error": { "code": "VALIDATION_ERROR", "message": "URL 또는 텍스트를 입력해야 합니다.", "details": null },
  "request_id": "req-...",
  "timestamp": "2025-02-04T12:00:00Z"
}
```

---

#### FR-B01 (Gemini): POST /generate-post-gemini, POST /generate-post-gemini-2-flash

**요청**: `PostRequest` (동일)

**응답 (성공 200)**: `PostResponse` — `data` 내 `ai_mode`가 `gemini` 또는 `gemini-2-flash` 반영.

---

#### FR-B02: POST /generate-post-stream, POST /generate-post-pipeline-stream, POST /generate-post-pipeline-robust-stream

**요청**: `PostRequest` (동일)

**응답**: `StreamingResponse` — `Content-Type: text/event-stream` (SSE)

**SSE 이벤트 예시**:
- 진행: `data: {"step": 1, "message": "웹 크롤링을 시작합니다...", "progress": 25}`
- 최종: `data: {"success": true, "message": "...", "data": {...}}`
- 에러: `data: {"error": "오류 메시지"}`

---

#### FR-B03: POST /generate-post-pipeline, POST /generate-post-pipeline-robust

**요청**: `PostRequest` (동일)

**응답 (성공 200)**: `PostResponse`

```json
{
  "success": true,
  "message": "블로그 포스트가 성공적으로 생성되었습니다.",
  "data": {
    "content": "<p>HTML 콘텐츠...</p>",
    "title": "제목",
    "keywords": "키워드1, 키워드2",
    "seo_analysis": {},
    "guidelines_analysis": {},
    "pipeline_id": "abc123",
    "metadata": {
      "content_length": 4000,
      "generated_at": "2025-02-03T12:00:00",
      "pipeline_steps": 5
    }
  }
}
```

---

#### FR-B04: GET /pipeline-status/{pipeline_id}, DELETE /pipeline/{pipeline_id}

**GET /pipeline-status/{pipeline_id}**

| 파라미터 | 타입 | 위치 | 설명 |
|----------|------|------|------|
| pipeline_id | string | path | 파이프라인 ID |

**응답 (성공 200)**:
```json
{ "pipeline_id": "abc123", "status": "completed" }
```
`status`: `pending`, `in_progress`, `completed`, `failed`, `cancelled` (ContentPipelineConfig 참조)

---

**DELETE /pipeline/{pipeline_id}**

**응답 (성공 200)**:
```json
{ "message": "파이프라인이 취소되었습니다.", "pipeline_id": "abc123" }
```
**에러**: 404 (파이프라인 없음), 500 (서버 오류)

---

#### FR-B05: POST /generate-post-enhanced, POST /generate-post-improved

**요청**: `PostRequest` (동일)

**응답 (성공 200)**: `PostResponse` — `data`에 `word_count`, `ai_analysis`, `guidelines_analysis` 포함 가능.

---

#### FR-B06: AI 윤리

**POST /posts/{post_id}/evaluate-ai-ethics**

| 파라미터 | 타입 | 위치 | 설명 |
|----------|------|------|------|
| post_id | integer | path | 포스트 ID |

**요청 본문**: 없음

**응답 (성공 200)**:
```json
{
  "success": true,
  "message": "AI 윤리 평가가 완료되었습니다.",
  "post_id": 1,
  "ai_ethics_score": 85.5,
  "evaluation": { "overall_score": 85.5, "..." },
  "evaluated_at": "2025-02-03T12:00:00"
}
```

---

**GET /posts/{post_id}/ai-ethics**

**응답 (성공 200)**:
```json
{
  "success": true,
  "post_id": 1,
  "title": "포스트 제목",
  "ai_ethics_score": 85.5,
  "evaluation": {},
  "evaluated_at": "2025-02-03T12:00:00"
}
```

---

**GET /posts/ai-ethics/stats**

**응답 (성공 200)**:
```json
{
  "success": true,
  "total_posts": 100,
  "evaluated_posts": 50,
  "average_score": 82.3,
  "message": null
}
```

---

#### FR-B07: POST /posts/generate-from-keyword

**요청**: `GenerateFromKeywordRequest` (app/schemas.py)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| keyword_id | integer | 예 | 키워드 ID |

**예시 요청**:
```json
{ "keyword_id": 42 }
```

**응답 (성공 200)**:
```json
{
  "success": true,
  "message": "키워드에서 포스트가 성공적으로 생성되었습니다.",
  "data": { "success": true, "message": "...", "data": { "id": 1, "title": "...", ... } }
}
```

---

#### FR-B08: POST /improve-content, POST /improve-content-suggestion

**POST /improve-content**

**요청**: `ImproveContentRequest` (app/schemas.py)

| 필드 | 타입 | 필수 | 검증 | 설명 |
|------|------|------|------|------|
| original_content | string | 예 | 비어있지 않음 | 원본 HTML 콘텐츠 |
| suggestions | array | 아니오 | - | 개선 제안 목록 |
| improvement_prompt | string | 아니오 | - | 추가 개선 지시 |

**예시 요청**:
```json
{
  "original_content": "<p>원본 콘텐츠...</p>",
  "suggestions": [{"category": "structure", "issue": "...", "suggestion": "..."}],
  "improvement_prompt": ""
}
```

**응답 (성공 200)**:
```json
{
  "success": true,
  "improved_content": "<p>개선된 콘텐츠...</p>",
  "original_length": 1000,
  "improved_length": 1200,
  "improvements_applied": 2,
  "original_analysis": {},
  "improved_analysis": {},
  "improvements": [],
  "fallback": false
}
```

---

**POST /improve-content-suggestion**

**요청**: `ImproveContentSuggestionRequest` (현재 `dict`, Pydantic 모델 권장)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| content | string | 예 | HTML 콘텐츠 |
| action | string | 아니오 | addHeadings, addFAQ, addSources, expandContent, addBalance, addStructuredData |
| suggestion | object | 아니오 | { category, issue, suggestion } |
| keywords | string | 아니오 | SEO 키워드 |

**예시 요청**:
```json
{
  "content": "<p>콘텐츠...</p>",
  "action": "addFAQ",
  "suggestion": {"category": "FAQ", "issue": "FAQ 없음", "suggestion": "FAQ 추가"},
  "keywords": "키워드1, 키워드2"
}
```

**응답 (성공 200)**:
```json
{
  "success": true,
  "improved_content": "<p>개선된 콘텐츠...</p>",
  "action": "addFAQ",
  "category": "FAQ",
  "original_length": 800,
  "improved_length": 1100
}
```

---

#### FR-B09: 아카이브

**GET /archive/documents**

| 파라미터 | 타입 | 필수 | 검증 | 기본값 |
|----------|------|------|------|--------|
| limit | integer | 아니오 | 1~100 | 10 (현재) / 20 (권장) |
| page | integer | 아니오 | ≥1 | 1 (권장: 페이지네이션 도입 시) |

**응답 (성공 200)**:
```json
{
  "success": true,
  "message": "Archive 문서 5개를 조회했습니다.",
  "data": {
    "documents": [
      {"id": "doc_id", "name": "문서명", "webViewLink": "https://...", "createdTime": "..."}
    ],
    "total_count": 5,
    "folder_name": "AI_SEO_Blogger_Archive"
  }
}
```
*페이지네이션 적용 시: `page`, `limit`, `total_pages`, `has_next`, `has_previous`, `next_page`, `prev_page` 포함 권장.*

---

**POST /archive/create**

| 파라미터 | 타입 | 위치 | 설명 |
|----------|------|------|------|
| blog_post_id | integer | query | 블로그 포스트 ID |

**응답 (성공 200)**:
```json
{
  "success": true,
  "message": "블로그 포스트가 Google Docs로 Archive 저장되었습니다.",
  "data": {
    "blog_post_id": 1,
    "archive_url": "https://docs.google.com/document/d/...",
    "title": "포스트 제목"
  }
}
```

---

**DELETE /archive/documents/{doc_id}**

| 파라미터 | 타입 | 위치 | 설명 |
|----------|------|------|------|
| doc_id | string | path | Google Docs 문서 ID |

**응답 (성공 200)**:
```json
{
  "success": true,
  "message": "Archive 문서가 삭제되었습니다.",
  "data": { "doc_id": "abc123xyz" }
}
```

---

#### 공통 에러 응답

**표준 에러 응답 스키마**를 따른다. 본문 필수: `error.code`, `error.message`, `request_id`, `timestamp`; 429 시 `Retry-After` 헤더 필수.

| HTTP | 상황 | error.code | 응답 예시 (표준 봉투) |
|------|------|------------|------------------------|
| 400 | 잘못된 입력 | VALIDATION_ERROR | `{"error":{"code":"VALIDATION_ERROR","message":"원본 콘텐츠가 필요합니다.","details":null},"request_id":"...","timestamp":"..."}` |
| 401 | 미인증 | UNAUTHORIZED | `{"error":{"code":"UNAUTHORIZED","message":"인증이 필요합니다.","details":null},"request_id":"...","timestamp":"..."}` |
| 403 | 권한 없음 | FORBIDDEN | `{"error":{"code":"FORBIDDEN","message":"권한이 없습니다.","details":null},"request_id":"...","timestamp":"..."}` |
| 404 | 리소스 없음 | NOT_FOUND | `{"error":{"code":"NOT_FOUND","message":"포스트 ID 999를 찾을 수 없습니다.","details":null},"request_id":"...","timestamp":"..."}` |
| 429 | Rate limit | RATE_LIMIT_EXCEEDED | 본문: 표준 봉투 + `Retry-After` 헤더 필수 — 상단 "429 Rate Limit — 표준 에러 봉투 예시" 참조 |
| 500 | 서버 오류 | INTERNAL_ERROR | `{"error":{"code":"INTERNAL_ERROR","message":"서버 내부 오류가 발생했습니다.","details":null},"request_id":"...","timestamp":"..."}` |

### 비기능 요구사항

- **NFR-B01**: 요청 검증(Pydantic), DB 세션 의존성 주입, 에러 시 HTTP 상태 코드 일관

  - **NFR-B01.1 Security** (에러 형식: **표준 에러 응답 스키마** 참조)
    - **Authentication/Authorization**: OAuth2 또는 JWT 기반 인증 지원; 역할 규칙(예: 읽기/쓰기/관리자)으로 엔드포인트 접근 제어; 미인증 요청은 `401 Unauthorized` + `error.code: UNAUTHORIZED`, 권한 부족은 `403 Forbidden` + `error.code: FORBIDDEN` 반환.
    - **Rate limiting & API key**: 클라이언트별(IP 또는 API 키) 요청 제한. **분당 60회**: 짧은 생성·조회 엔드포인트 — FR-B01 (`POST /generate-post` 등), FR-B06 (AI 윤리), FR-B07 (`POST /posts/generate-from-keyword`), FR-B08 (improve-content·improve-content-suggestion), FR-B09 (`GET /archive/documents` 등 아카이브 조회·생성·삭제). **분당 10회**: 파이프라인·스트리밍 엔드포인트 — FR-B02 (스트리밍), FR-B03 (파이프라인 동기), FR-B05 (고급 생성 enhanced·improved). 초과 시 `429 Too Many Requests`, `error.code: RATE_LIMIT_EXCEEDED`, **Retry-After** 헤더 및 표준 에러 봉투 필수; API 키는 헤더(`X-API-Key` 또는 `Authorization: Bearer`)로 전달, 키 검증 실패 시 `401` + UNAUTHORIZED.
    - **Input sanitization**: 모든 사용자 입력(키워드, URL, 본문 필드)에 대해 길이·문자셋 제한 및 XSS/인젝션 방지(이스케이프·화이트리스트); 검증 실패 시 `400 Bad Request` + `error.code: VALIDATION_ERROR` 및 명시적 오류 메시지.

  - **NFR-B01.2 Performance** (에러 시 **표준 에러 응답 스키마** 사용)
    - **Latency**: 단일 생성·조회 API의 p95 응답 시간 ≤ 2초(외부 LLM/DB 제외한 앱 처리 구간); 스트리밍/파이프라인은 TTFB ≤ 1초.
    - **Timeouts**: 동기 생성·파이프라인 호출의 서버 측 타임아웃 ≤ 120초; 외부 LLM/다운스트림 호출은 재시도 정책과 연동된 타임아웃(예: 30초) 적용.

  - **NFR-B01.3 Reliability** (에러 응답: **표준 에러 응답 스키마**, request_id 포함)
    - **Uptime SLA**: 블로그 생성 API 가용성 목표 99.5%(월간); 계측은 헬스체크 엔드포인트(예: `/health`) 기반.
    - **Retries & backoff**: 외부 서비스(LLM, DB) 호출 실패 시 지수 백오프 재시도(최대 3회, 초기 대기 1초); 재시도 불가 오류(4xx, 정책 위반)는 재시도하지 않음.
    - **Circuit breaker**: 동일 외부 의존성에 대해 설정 가능한 임계치(권장: 연속 실패 5회, 에러율 50%) 초과 시 회로 차단; 복구 시도 간격(권장: 30초) 후 재시도.

  - **NFR-B01.4 Scalability** (에러 시 **표준 에러 응답 스키마**, 503 → error.code: SERVICE_UNAVAILABLE)
    - **Concurrency**: 서버당 동시 처리 요청 수 상한 정의(예: 50); 초과 시 `503 Service Unavailable` + `error.code: SERVICE_UNAVAILABLE` 또는 큐 대기.
    - **Pagination & data volume**: 목록/아카이브 API는 `limit`(기본 20, 최대 100) 및 `offset`/커서 기반 페이지네이션 필수. 단일 요청 본문 상한(예: 1MB)과 응답 본문 상한(예: 10MB)을 초과하면 서버는 반드시 HTTP 413 Payload Too Large를 반환하고, JSON 에러 본문(에러 코드, 메시지, pagination 사용 권고 등 선택)을 포함한다. 요청 본문 초과 시에도 동일하게 413을 적용한다. 서버는 적절한 경우 `Retry-After` 헤더 또는 페이지네이션 리소스 링크를 포함하는 것을 권장(SHOULD)한다. 클라이언트는 과도한 응답을 피하기 위해 기존 `limit`/`offset` 또는 커서 파라미터(기본 limit=20, max=100) 사용을 권장한다.

  - **NFR-B01.5 Observability** (에러 응답의 `request_id`·`error.code`는 **표준 에러 응답 스키마**와 동일 값 사용)
    - **Structured logging**: 로그는 JSON 구조화(필드: `timestamp`, `level`, `request_id`, `path`, `status`, `duration_ms`, `error_code` 등); 민감 정보(API 키, 토큰) 미포함.
    - **Metrics**: 요청 수(by path, method, status), 지연(histogram, p50/p95/p99), 에러율, 회로 차단 상태, 큐 길이 등 노출(Prometheus/StatsD 호환 형식 권장).
    - **Alert thresholds**: 에러율 > 5%(5분 창), p95 지연 > 5초(5분 창), 가용성 헬스 실패 연속 3회 시 알림 발생하도록 임계치 정의.

### 모델 파라미터 사용 예시

모델 선택은 경로가 아닌 파라미터로만 지정한다.

- **단일 생성 (FR-B01)**  
  `POST /api/v1/generate-post?model=gemini-2-flash`  
  또는 본문: `{"keyword": "...", "model": "gemini-2-flash", ...}`

- **스트리밍 (FR-B02)**  
  `POST /api/v1/generate-post-stream?model=gemini-2-flash`  
  또는 본문: `{"keyword": "...", "model": "gemini-2-flash", ...}`

- **고급 생성 (FR-B05)**  
  `POST /api/v1/generate-post-enhanced?model=gemini-2-flash`  
  또는 본문: `{"keyword": "...", "model": "gemini-2-flash", ...}`

지원 모델 예: `gemini`, `gemini-2-flash` (구체 값은 구현/설정 참조).

## 검증 기준

### 구현 검증

- [ ] 각 엔드포인트가 OpenAPI(/docs)에 노출됨
- [ ] 스트리밍 응답은 `StreamingResponse`/SSE 형식 유지
- [ ] AI 윤리 평가 결과가 DB 필드(ai_ethics_score, ai_ethics_evaluation)에 저장됨
- [ ] 생성·스트리밍·고급 생성 API는 경로가 아닌 `model` 쿼리/본문으로 모델 선택 가능

### 기능 테스트 (Functional Testing)

- [ ] 핵심 워크플로우: 단일 생성(generate-post), 스트리밍(generate-post-stream 등), 파이프라인 동기/취소(pipeline, pipeline-status, DELETE pipeline) 시나리오 검증 완료

### 통합 테스트 (Integration Testing)

- [ ] **LLM API 호출(모델 선택·요청/응답) 통합 검증 완료**  
  - 지원 모델별(gemini, gemini-2-flash 등) **모델당 요청/응답 검증**: 각 지원 모델에 대해 실제 호출 후 성공 응답 형상(스키마) 검증.  
  - **성공 케이스**: 응답 본문 구조·필수 필드·타입이 사양과 일치하는지 확인.  
  - **실패 케이스**: 미지원/잘못된 모델 식별자 전송 시 기대하는 오류 응답 본문 및 HTTP 상태 코드(예: 400/422) 반환 검증.  
  → 검증 시 모델별 정상 동작과 미지원 모델에 대한 오류 처리 모두 확인할 것.
- [ ] DB 트랜잭션(저장·조회·롤백) 검증 완료

### 성능 테스트 (Performance Testing)

- [ ] 부하 목표 충족: 예) 동시 사용자 100명 또는 동등 SLA; p95 응답 시간 ≤ 2초(또는 사양에 정의된 SLA) 검증 완료

### 보안 테스트 (Security Testing)

- [ ] 인증/인가 적용 검증: 미인증 401, 권한 부족 403 등 엔드포인트별 접근 제어 확인
- [ ] 입력 검증: 인젝션(XSS/SQL 등) 방지를 위한 검증·새니타이징 및 400 응답 확인

### 에러 처리 (Error Handling)

- [ ] 네트워크 장애·타임아웃·잘못된 입력에 대한 우아한 처리 검증(재시도·명시적 오류 메시지·적절한 HTTP 상태 코드)

### API 계약 검증 (API Contract)

- [ ] 요청/응답 스키마가 OpenAPI 사양과 일치함을 검증(스키마 매칭·필수 필드·타입)

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2025-02-03 | 0.1 | dev-agent-kit 사양 분리 |
| 2025-02-03 | 0.2 | 모델별 엔드포인트 통합: 단일 엔드포인트 + model 쿼리/본문 파라미터, FR-B01/FR-B02/FR-B05 및 예시 정리 |
