# 🔧 크롤링 문제 완벽 대처 가이드

## 📋 목차
1. [문제 진단 도구 사용법](#문제-진단-도구-사용법)
2. [사이트별 크롤링 설정](#사이트별-크롤링-설정)
3. [크롤링 성공률 모니터링](#크롤링-성공률-모니터링)
4. [일반적인 문제 해결](#일반적인-문제-해결)
5. [고급 문제 해결](#고급-문제-해결)

## 🔍 문제 진단 도구 사용법

### 1. 사이트 구조 분석
```bash
# 특정 사이트의 HTML 구조 분석
python tools/crawler_debug.py https://example.com/article
```

이 도구는 다음을 분석합니다:
- ✅ 페이지 로드 상태
- 📋 기본 정보 (제목, 메타 설명)
- 🔍 본문 관련 요소 검색
- 🏷️ 모든 CSS 클래스 분석
- 📄 텍스트 블록 분석
- 💡 추천 선택자 생성
- 🧪 실제 크롤링 테스트

### 2. 크롤링 성공률 리포트
```bash
# 전체 크롤링 성공률 리포트
python tools/crawler_report.py report

# 특정 사이트 테스트
python tools/crawler_report.py test https://example.com/article
```

## ⚙️ 사이트별 크롤링 설정

### 설정 파일 구조
`site_crawler_configs.json` 파일에서 사이트별 설정을 관리합니다:

```json
{
  "example.com": {
    "selectors": [
      ".entry-content",
      ".post-content",
      ".article-content"
    ],
    "exclude_selectors": [
      ".advertisement",
      ".sidebar",
      ".comments"
    ],
    "text_filters": [
      "^\\s*$",
      "^Advertisement$",
      "^Related.*$"
    ]
  }
}
```

### 새 사이트 추가 방법
1. **사이트 분석**: `python tools/crawler_debug.py <URL>`
2. **결과 확인**: 추천 선택자와 클래스 목록 확인
3. **설정 추가**: `site_crawler_configs.json`에 새 도메인 추가
4. **테스트**: `python tools/crawler_report.py test <URL>`

## 📊 크롤링 성공률 모니터링

### 자동 모니터링
- 모든 크롤링 시도가 자동으로 기록됩니다
- 성공/실패 통계가 실시간으로 업데이트됩니다
- 문제 사이트가 자동으로 식별됩니다

### 모니터링 데이터
- `crawling_stats.json`: 크롤링 통계 데이터
- 사이트별 성공률 추적
- 오류 패턴 분석
- 최근 시도 기록

## 🚨 일반적인 문제 해결

### 1. "본문을 찾을 수 없음" 오류

**원인**: 사이트의 HTML 구조가 일반적인 선택자와 다름

**해결 방법**:
```bash
# 1. 사이트 구조 분석
python tools/crawler_debug.py <문제_URL>

# 2. 분석 결과에서 추천 선택자 확인
# 3. site_crawler_configs.json에 추가
```

### 2. "네트워크 오류" 문제

**원인**: 
- 사이트 차단
- 타임아웃
- 잘못된 User-Agent

**해결 방법**:
```python
# EnhancedCrawler는 자동으로 다음을 시도합니다:
# - 3회 재시도
# - 지수 백오프
# - 다양한 User-Agent
# - 타임아웃 조정
```

### 3. "텍스트가 너무 짧음" 문제

**원인**: 
- 광고나 사이드바만 추출됨
- JavaScript로 콘텐츠 로드
- 잘못된 선택자

**해결 방법**:
```bash
# 1. exclude_selectors 확인
# 2. 사이트별 설정 조정
# 3. text_filters 추가
```

## 🔧 고급 문제 해결

### 1. JavaScript 렌더링 필요 사이트

**문제**: 콘텐츠가 JavaScript로 동적 로드

**해결 방법**:
```python
# Selenium 또는 Playwright 사용 고려
# 현재는 정적 HTML만 지원
```

### 2. CAPTCHA 또는 차단

**문제**: 사이트에서 봇 차단

**해결 방법**:
```python
# 1. User-Agent 다양화
# 2. 요청 간격 조정
# 3. 프록시 사용 고려
```

### 3. 복잡한 사이트 구조

**문제**: 여러 단계의 중첩된 요소

**해결 방법**:
```json
{
  "complex-site.com": {
    "selectors": [
      ".main-container .content-wrapper .article-body",
      ".post-container .entry-content .text-content"
    ]
  }
}
```

## 📈 성능 최적화

### 1. 선택자 최적화
- 구체적인 선택자 우선 사용
- 불필요한 중첩 제거
- 성능 좋은 CSS 선택자 사용

### 2. 캐싱 전략
- 동일 URL 재크롤링 방지
- 결과 캐싱 구현

### 3. 병렬 처리
- 여러 URL 동시 크롤링
- 적절한 동시성 제한

## 🛠️ 유지보수

### 정기적인 점검
```bash
# 주간 리포트 생성
python tools/crawler_report.py report

# 문제 사이트 확인
# crawling_stats.json에서 problem_sites 확인
```

### 데이터 정리
```python
# 30일 이상 된 데이터 정리
crawling_monitor.cleanup_old_data(days=30)
```

### 설정 업데이트
- 새로운 사이트 패턴 발견 시 설정 추가
- 실패하는 사이트 분석 후 설정 조정
- 성공률 개선을 위한 선택자 최적화

## 📞 문제 보고

크롤링 문제가 지속되면:

1. **진단 정보 수집**:
   ```bash
   python tools/crawler_debug.py <문제_URL>
   python tools/crawler_report.py report
   ```

2. **로그 확인**: `logs/` 디렉토리의 로그 파일

3. **설정 파일 백업**: `site_crawler_configs.json` 백업

4. **문제 상세 기록**:
   - URL
   - 오류 메시지
   - 예상 결과
   - 실제 결과

---

## 🎯 빠른 체크리스트

크롤링 문제 발생 시:

- [ ] `python tools/crawler_debug.py <URL>` 실행
- [ ] 추천 선택자 확인
- [ ] `site_crawler_configs.json` 설정 추가
- [ ] `python tools/crawler_report.py test <URL>` 테스트
- [ ] 성공률 리포트 확인
- [ ] 필요시 추가 설정 조정

이 가이드를 따라하면 대부분의 크롤링 문제를 해결할 수 있습니다! 🚀 