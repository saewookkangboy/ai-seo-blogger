# AI 윤리 및 Responsible AI 평가 기능

## 개요

마케팅 도구로 활용되는 AI 기반 콘텐츠 생성 시스템에 AI 윤리 및 Responsible AI 측정 기능이 추가되었습니다. 생성된 모든 콘텐츠는 자동으로 윤리적 측면을 평가받으며, 평가 결과는 데이터베이스에 저장되고 사용자에게 표시됩니다.

## 주요 기능

### 1. AI 윤리 평가 항목

다음 7가지 Responsible AI 원칙에 따라 콘텐츠를 평가합니다:

1. **편향성 (Bias)** - 특정 그룹에 대한 부정적/긍정적 편향 검사
2. **공정성 (Fairness)** - 다양한 관점과 그룹에 대한 공정한 표현 검사
3. **투명성 (Transparency)** - AI 사용 여부 명시 및 생성 과정 투명성
4. **프라이버시 (Privacy)** - 개인정보 보호 및 민감 정보 노출 검사
5. **해로운 콘텐츠 (Harmful Content)** - 폭력, 혐오 표현, 허위 정보 등 검사
6. **정확성 (Accuracy)** - 사실 확인 가능성 및 출처 명시
7. **설명 가능성 (Explainability)** - AI 결정 과정의 설명 가능성

### 2. 평가 점수 시스템

- 각 항목별 점수: 0-100점
- 종합 점수: 가중 평균으로 계산
  - 해로운 콘텐츠: 25% (가장 중요)
  - 프라이버시: 20%
  - 편향성: 15%
  - 공정성: 15%
  - 투명성: 10%
  - 정확성: 10%
  - 설명 가능성: 5%

### 3. 데이터베이스 스키마 변경

`BlogPost` 모델에 다음 필드가 추가되었습니다:

- `ai_ethics_score`: Float - 종합 점수 (0-100)
- `ai_ethics_evaluation`: JSON - 전체 평가 결과
- `ai_ethics_evaluated_at`: DateTime - 평가 일시

## API 엔드포인트

### 1. AI 윤리 평가 결과 조회
```
GET /api/posts/{post_id}/ai-ethics
```

특정 포스트의 AI 윤리 평가 결과를 조회합니다.

### 2. AI 윤리 평가 수행
```
POST /api/posts/{post_id}/evaluate-ai-ethics
```

특정 포스트에 대해 AI 윤리 평가를 수행합니다.

### 3. AI 윤리 평가 통계
```
GET /api/posts/ai-ethics/stats
```

전체 포스트의 AI 윤리 평가 통계를 조회합니다.

## 사용 방법

### 자동 평가

콘텐츠 생성 시 자동으로 AI 윤리 평가가 수행됩니다:

1. 콘텐츠 생성 요청
2. 콘텐츠 생성 완료
3. 자동으로 AI 윤리 평가 수행
4. 평가 결과를 데이터베이스에 저장
5. 프론트엔드에 평가 결과 표시

### 수동 평가

기존 포스트에 대해 수동으로 평가를 수행할 수 있습니다:

```python
POST /api/posts/{post_id}/evaluate-ai-ethics
```

## 프론트엔드 UI

생성된 콘텐츠 결과 화면에 "Responsible AI 평가 결과" 섹션이 표시됩니다:

- 종합 점수 (진행 바와 배지)
- 세부 평가 항목별 점수
- 개선 권장사항

## 평가 세부 사항

### 편향성 평가
- 성별, 연령, 인종, 종교, 정치적 편향 검사
- 성별 표현의 균형 검사
- 부정적 맥락에서의 편향 표현 감지

### 공정성 평가
- 배제적 표현 vs 포괄적 표현 검사
- 다양한 관점 제시 여부
- 균형 잡힌 의견 표현

### 투명성 평가
- AI 사용 명시 여부
- 생성 메타데이터 제공
- 출처 명시

### 프라이버시 평가
- 개인정보 패턴 검사 (이메일, 전화번호 등)
- 민감 정보 노출 검사

### 해로운 콘텐츠 평가
- 폭력 관련 콘텐츠
- 혐오 표현
- 허위 정보
- 교육적 맥락 고려

### 정확성 평가
- 출처 명시 여부
- 날짜/통계 정보 포함
- 불확실성 인정 표현

### 설명 가능성 평가
- 구조화된 형식 (HTML 구조)
- 메타데이터 제공
- 키워드 명시

## 데이터베이스 마이그레이션

새로운 필드를 추가하기 위해 데이터베이스 마이그레이션이 필요합니다:

```sql
ALTER TABLE blog_posts 
ADD COLUMN ai_ethics_score FLOAT DEFAULT NULL,
ADD COLUMN ai_ethics_evaluation JSON DEFAULT NULL,
ADD COLUMN ai_ethics_evaluated_at TIMESTAMP DEFAULT NULL;
```

또는 Python 마이그레이션 스크립트 실행:

```bash
python migrate_db.py
```

## 파일 구조

### 새로 추가된 파일
- `app/services/ai_ethics_evaluator.py` - AI 윤리 평가 서비스

### 수정된 파일
- `app/models.py` - BlogPost 모델에 평가 필드 추가
- `app/routers/blog_generator.py` - 평가 통합 및 API 엔드포인트 추가
- `app/templates/components/_result_display.html` - UI 추가
- `app/static/js/pages/index.js` - 평가 결과 표시 로직 추가

## 향후 개선 사항

1. **고급 편향성 검사**: 머신러닝 기반 편향성 감지
2. **실시간 피드백**: 생성 중 실시간 윤리 검사
3. **커스텀 규칙**: 사용자 정의 윤리 규칙 설정
4. **평가 이력**: 평가 결과 변경 이력 추적
5. **다국어 지원**: 다양한 언어에 대한 평가 개선

## 참고 자료

- [Microsoft Responsible AI](https://www.microsoft.com/en-us/ai/responsible-ai)
- [Google AI Principles](https://ai.google/principles/)
- [Partnership on AI](https://partnershiponai.org/)

