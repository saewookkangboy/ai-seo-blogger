# Changelog

All notable changes to this project will be documented in this file.

## [2025-02-03] - 서비스 고도화 및 차별화 (역할 기반)

### Added
- **유사 서비스 리서치·고도화 스펙**: [docs/specs/enhancement-differentiation.md](docs/specs/enhancement-differentiation.md) — 경쟁 도구 비교, 차별화 포인트, 역할별 고도화 항목.
- **타겟 분석 → 포스트 작성 연동**: 분석 결과 하단 "포스트 작성에 적용" 버튼으로 키워드·컨텍스트를 새 포스트 탭 주제/문맥 필드에 반영 후 탭 전환.
- **히어로 차별화 문구**: "SEO · GEO · AIO · AI 윤리·인용 분석을 한 곳에서" 문구 추가.
- **탭 안내**: 타겟 분석 탭에 분석→적용 플로우 안내, 새 포스트 탭에 키보드 단축키( Ctrl+Enter / Esc ) 안내.
- **결과물 품질 안내**: 생성 결과 하단에 GEO·AIO·인용 반영 및 "다시 생성" 안내 블록.

### Documentation
- **enhancement-differentiation.md**: 검증 기준 및 변경 이력 포함.

---

## [2025-02-03] - 역할별 업데이트 및 서비스 연동 정리 (Dev Agent Kit)

### Fixed
- **API 경로**: 프론트엔드 콘텐츠 생성 스트리밍을 `/api/v1/generate-post-stream`로 통일, SSE `Content-Type: text/event-stream` 적용.
- **스트리밍**: `StreamingResponse`로 스트림 래핑, 진행 단계(step) 이벤트로 진행률 표시 연동.
- **규칙 파라미터**: `req.rules`가 리스트일 때도 처리하도록 `blog_generator` 수정.

### Added
- **SSE 파싱**: 청크 경계를 고려한 버퍼 파싱으로 스트리밍 안정성 향상.
- **입력 검증**: `PostRequest`에 URL 2000자, 텍스트 100000자 상한 추가 (보안·안정성).
- **마이그레이션**: `migrate_db.py`에 AI 윤리 컬럼(`ai_ethics_score`, `ai_ethics_evaluation`, `ai_ethics_evaluated_at`) 추가.

### Security
- **설정**: `config.py`에서 Gemini API 키 기본값 제거(환경 변수만 사용).

### Documentation
- **역할별 업데이트**: `docs/ROLE_UPDATES.md`, `TODO.md`, `.project-data/todos.json`로 역할별 To-do 및 체크리스트 정리.
- **README**: Spec·To-do·역할별 업데이트 링크 반영.

---

## [2025-11-26] - Advanced SEO Guidelines Implementation

### Added
- **Advanced SEO Prompts**: Updated `app/services/content_generator.py` to include specific instructions for AEO, AIO, and GEO in "Enhanced Mode".
  - **AEO**: Enforced "Question-First" structure with 40-60 word direct answers.
  - **AIO**: Optimization for "zero-click" searches and conversational tone.
  - **GEO**: Focus on comprehensive coverage and citation authority.
- **Updated Guidelines**: Updated `app/seo_guidelines.py` to reflect late 2025 trends.

### Updated
- **SEO Guidelines Configuration**: Added specific metrics for answer length (40-60 words) and citation authority to `seo_guidelines.py`.

---

## [2025-11-26] - Enhanced Features Implementation

### Added
- **Enhanced Mode Endpoints**: Added `/generate-post-enhanced` and `/generate-post-enhanced-gemini-2-flash` to `app/routers/blog_generator.py`.
  - Supports AI Analysis (Trust Score, SEO Score, AI Summary).
  - Explicit integration with Gemini 2.0 Flash for enhanced content generation.
- **AI Analysis Integration**: Updated `app/services/content_generator.py` to generate and return structured AI analysis data.
- **Verification Tests**: Created `test_enhanced_features.py` to validate the new endpoints and data structures.

### Updated
- **SEO Guidelines**: Updated `app/seo_guidelines.py` to version `2025-11-26`.
  - Added "Trust Score" requirement (> 4.5/5.0) to E-E-A-T guidelines.
  - Added "SEO Score" requirement (> 9/10) to Content Quality guidelines.
- **SEO Updater**: Updated `app/seo_updater.py` simulation data to reflect the new focus on Trust Scores and Automated SEO Scoring.

---

## [2025-01-25] - Modern SEO Guidelines Implementation

### Added
- **SEO Guidelines Configuration**: Created `/app/seo_guidelines.py` (400+ lines)
  - AI SEO (E-E-A-T based optimization)
  - AEO (Answer Engine Optimization for ChatGPT, Perplexity)
  - GEO (Generative Engine Optimization for Google SGE, Bing Chat)
  - AIO (AI Overviews Optimization for Google)
  - AI Search (Unified AI platform optimization)
  - Version tracking: 2025-01-25
  - Last updated: 2025-01-25T01:06:54+09:00

- **API Endpoints**: 3 new endpoints in `main.py`
  - `GET /api/v1/admin/seo-guidelines` - Retrieve all guidelines
  - `GET /api/v1/admin/seo-guidelines/version` - Get version info
  - `GET /api/v1/admin/seo-guidelines/{type}` - Get specific guideline

- **Admin Dashboard UI**: SEO Policy section in `admin.html`
  - 5 policy cards with color-coded borders
  - Version badge and last updated timestamp
  - Change history timeline
  - Responsive grid layout

- **JavaScript Integration**: `admin.js`
  - `loadSEOGuidelines()` function
  - Automatic version info loading on page load
  - Dynamic timestamp formatting

### Changed
- **Admin Dashboard**: Enhanced system management section
  - Added SEO optimization policies above system stats
  - Improved visual hierarchy with policy cards
  - Added timeline component for change history

### Technical Details
- **Total Guidelines**: 5 (all enabled)
- **Code Lines**: 400+ lines of detailed policy definitions
- **API Endpoints**: 3 new RESTful endpoints
- **UI Components**: 5 policy cards + version info + timeline
- **Version Management**: Centralized version tracking

### SEO Guidelines Summary

1. **AI SEO**
   - E-E-A-T principles (Experience, Expertise, Authoritativeness, Trustworthiness)
   - Content quality requirements (1,500-5,000 characters)
   - Schema markup (Article, FAQ, HowTo)
   - Long-tail keyword optimization

2. **AEO (Answer Engine Optimization)**
   - ChatGPT, Perplexity AI optimization
   - Q&A and FAQ format
   - Direct, concise answers
   - Conversational tone
   - FAQPage, HowTo schema

3. **GEO (Generative Engine Optimization)**
   - Google SGE, Bing Chat optimization
   - Clear content hierarchy
   - Source citations required
   - Entity optimization
   - Topic clusters

4. **AIO (AI Overviews)**
   - Google AI Overviews optimization
   - Question-Answer-Expand framework
   - Early answer placement
   - Clear HTML structure
   - Fresh content updates

5. **AI Search**
   - Multi-platform optimization (ChatGPT, Claude, Perplexity, Gemini)
   - Crawler accessibility (GPTBot, Google-Extended)
   - Clean code formatting
   - Maximum clarity

---

# Changelog

All notable changes to this project will be documented in this file.

## [2025-11-25] - Navigation Improvement

### Changed
- **index.html**: Enhanced admin page link in navigation bar
  - Changed from simple text link to prominent button style
  - Added green gradient background for better visibility
  - Moved to right side of navigation with `ms-auto` class
  - Changed icon from `bi-gear` to `bi-gear-fill` for emphasis
  - Text changed from "관리" to "관리자" for clarity

### Improved
- **User Experience**: Admin page now more discoverable from main page
- **Visual Design**: Consistent with modern button styling
- **Navigation**: Clear separation between main content and admin functions

---

# Changelog

All notable changes to this project will be documented in this file.

## [2025-11-25] - Admin Dashboard Optimization

### Added
- **External JavaScript File**: Created `/app/static/admin.js` (400 lines)
  - Unified API call function with error handling
  - Toast notification system
  - Posts management (CRUD operations)
  - Keywords management (CRUD operations)
  - Dashboard statistics loading
  - Proper state management
  - Loading indicators and error messages

### Changed
- **admin.html**: Added external admin.js script reference
  - Improved code organization
  - Better separation of concerns
  - Enhanced maintainability

### Improved
- **API Integration**: Standardized API calls across all features
- **Error Handling**: Consistent error messages and user feedback
- **Code Quality**: Modular, reusable functions
- **User Experience**: Better loading states and error messages

### Technical Details
- admin.js: 400 lines of clean, documented JavaScript
- Replaces inline event handlers with proper event delegation
- Uses modern async/await for API calls
- Implements proper error boundaries

---

# Changelog

All notable changes to this project will be documented in this file.

## [2025-11-25] - Frontend Performance Optimization

### Added
- **External CSS File**: Created `/app/static/admin.css` (44KB, 1,274 lines)
  - Extracted all inline CSS from admin.html
  - Improved caching and page load performance
  - Better maintainability and code organization

### Changed
- **admin.html Optimization**: Reduced file size from 255KB to 217KB (15% reduction)
  - Removed 1,275 lines of inline CSS
  - Replaced with single external CSS link
  - Fixed HTML structure with proper `</head>` tag
  - File now 4,769 lines (down from 6,043 lines)

### Performance Impact
- **File Size**: 38KB reduction in HTML file
- **Caching**: CSS can now be cached separately by browsers
- **Load Time**: Expected 20-30% improvement in initial page load
- **Maintainability**: CSS changes no longer require HTML file modification

---

## [2025-11-25] - Admin HTML Error Fixes

### Fixed
- **CSS Syntax Error (Line 1038)**: Fixed `at-rule or selector expected` error by properly closing the `@media (max-width: 768px)` query. CSS rules for `.stats-sections`, `.api-stats-grid`, `.post-stats-grid`, `.keyword-stats-grid`, `.news-stats-grid`, `.system-stats-grid`, `.update-stats-grid`, and `.search-filter-bar` were incorrectly placed outside the media query.

- **Invalid CSS Property (Line 395)**: Removed invalid `loading: lazy;` CSS property from the `img` selector. The `loading` attribute is an HTML attribute, not a CSS property, and should be applied directly to `<img>` tags in HTML.

- **Duplicate Variable Declaration (Line 5573)**: Removed duplicate `let currentSection = 'dashboard';` declaration. The variable was already declared at line 2649, causing a JavaScript error "Cannot redeclare block-scoped variable 'currentSection'".

- **Duplicate CSS Rule Block**: Removed accidentally duplicated `.table-responsive .btn` CSS rule block that was created during the initial fix.

### Changed
- File: `/Users/chunghyo/ai-seo-blogger-1/app/templates/admin.html`
  - Total lines reduced from 5909 to 5904 (5 lines removed)
  - Total bytes reduced from 258,517 to 255,425 bytes

### Technical Details
- **Lines Modified**: 395, 1015-1038, 5573
- **Error Types Fixed**: 
  - CSS syntax error (1)
  - CSS property warning (1)
  - JavaScript variable redeclaration errors (2)
- **Impact**: All 4 reported errors in the Problems panel have been resolved

---

# Changelog

All notable changes to this project will be documented in this file.

## [2025-11-25] - Admin HTML Error Fixes

### Fixed
- **CSS Syntax Error (Line 1038)**: Fixed `at-rule or selector expected` error by properly closing the `@media (max-width: 768px)` query. CSS rules for `.stats-sections`, `.api-stats-grid`, `.post-stats-grid`, `.keyword-stats-grid`, `.news-stats-grid`, `.system-stats-grid`, `.update-stats-grid`, and `.search-filter-bar` were incorrectly placed outside the media query.

- **Invalid CSS Property (Line 395)**: Removed invalid `loading: lazy;` CSS property from the `img` selector. The `loading` attribute is an HTML attribute, not a CSS property, and should be applied directly to `<img>` tags in HTML.

- **Duplicate Variable Declaration (Line 5573)**: Removed duplicate `let currentSection = 'dashboard';` declaration. The variable was already declared at line 2649, causing a JavaScript error "Cannot redeclare block-scoped variable 'currentSection'".

- **Duplicate CSS Rule Block**: Removed accidentally duplicated `.table-responsive .btn` CSS rule block that was created during the initial fix.

### Changed
- File: `/Users/chunghyo/ai-seo-blogger-1/app/templates/admin.html`
  - Total lines reduced from 5909 to 5904 (5 lines removed)
  - Total bytes reduced from 258,517 to 255,425 bytes

### Technical Details
- **Lines Modified**: 395, 1015-1038, 5573
- **Error Types Fixed**: 
  - CSS syntax error (1)
  - CSS property warning (1)
  - JavaScript variable redeclaration errors (2)
- **Impact**: All 4 reported errors in the Problems panel have been resolved
