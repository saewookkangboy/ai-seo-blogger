# API 키 설정 가이드

## 개요
AI SEO Blog Generator는 다음 API들을 사용합니다:
- **OpenAI API**: AI 콘텐츠 생성 및 키워드 추출
- **Google Gemini API**: 텍스트 번역 및 콘텐츠 생성

## 현재 상태
- ✅ **Google Gemini API**: 기본 제공 (무료)
- ❌ **OpenAI API**: 설정 필요

## API 키 설정 방법

### 1. OpenAI API 키 설정

#### 1.1 API 키 발급
1. [OpenAI Platform](https://platform.openai.com/)에 접속
2. 계정 생성 또는 로그인
3. API Keys 메뉴에서 "Create new secret key" 클릭
4. API 키 복사

#### 1.2 환경 변수 설정
`.env` 파일에 다음 내용 추가:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```



## API 키 없이 사용하기

### 현재 구현된 기능
1. **번역**: Google Gemini API 사용
2. **콘텐츠 생성**: OpenAI 실패 시 → 기본 템플릿 생성
3. **키워드 추출**: OpenAI 실패 시 → 기본 키워드 추출

### 사용 가능한 기능
- ✅ **Gemini API**: 무료로 사용 가능 (번역)
- ✅ **기본 템플릿**: API 키 없이도 콘텐츠 생성 가능
- ✅ **기본 키워드**: 텍스트 분석을 통한 키워드 추출

## 권장 설정

### 최소 설정 (무료)
```bash
# .env 파일
OPENAI_API_KEY=your_openai_api_key_here
```

### 최적 설정 (유료)
```bash
# .env 파일
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here  # 선택사항
```

## API 사용량 및 비용

### OpenAI API
- **GPT-4**: $0.03/1K input tokens, $0.06/1K output tokens
- **GPT-3.5-turbo**: $0.0015/1K input tokens, $0.002/1K output tokens



### Google Gemini API
- **무료 플랜**: 15 requests/minute, 1500 requests/day
- **유료 플랜**: $0.00025/1K characters

## 문제 해결

### 1. API 키 오류
```
OpenAI API 오류: Authorization failure, check auth_key
```
**해결방법**: `.env` 파일에서 API 키 확인

### 2. 할당량 초과
```
Gemini API 할당량이 초과되었습니다
```
**해결방법**: 
- 무료 플랜 사용량 확인
- 유료 플랜으로 업그레이드

### 3. 네트워크 오류
```
OpenAI API 오류: Network error
```
**해결방법**:
- 인터넷 연결 확인
- 방화벽 설정 확인
- VPN 사용 중인 경우 해제

## 테스트 방법

### 1. API 키 테스트
```bash
# OpenAI 테스트
curl -X POST -H "Content-Type: application/json" \
  -d '{"text":"Hello world"}' \
  http://localhost:8000/api/v1/generate-post


```

### 2. 기능 테스트
다음 기능들이 작동합니다:
- 기본 템플릿 생성
- 기본 키워드 추출
- Gemini API 번역

## 지원 및 문의

API 키 설정에 문제가 있으시면:
1. 이 가이드를 다시 확인
2. API 제공업체의 공식 문서 참조
3. 개발자에게 문의: chunghyo@troe.kr 