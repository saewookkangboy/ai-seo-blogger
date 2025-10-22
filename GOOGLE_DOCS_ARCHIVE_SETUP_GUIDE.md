# Google Docs Archive 설정 가이드

## 📋 개요

AI SEO Blogger에서 생성되는 블로그 포스트를 자동으로 Google Docs로 Archive 저장하는 기능입니다. 이 기능을 통해 생성된 콘텐츠를 체계적으로 관리하고 백업할 수 있습니다.

## 🔧 설정 방법

### 1. Google Cloud Console 설정

#### 1.1 Google Docs API 활성화
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 선택: `ai-seo-blogger` (또는 해당 프로젝트)
3. "API 및 서비스" → "라이브러리"로 이동
4. "Google Docs API" 검색 후 활성화
5. "Google Drive API"도 함께 활성화 (이미 활성화되어 있을 수 있음)

#### 1.2 OAuth 동의 화면 설정
1. "API 및 서비스" → "OAuth 동의 화면"으로 이동
2. **사용자 유형**: "외부" 선택
3. **앱 정보**:
   - 앱 이름: `AI SEO Blogger`
   - 사용자 지원 이메일: `pakseri@gmail.com`
   - 개발자 연락처 정보: `pakseri@gmail.com`
4. **범위**:
   - "범위 추가 또는 삭제" 클릭
   - 다음 범위들을 추가:
     - `https://www.googleapis.com/auth/documents` (Google Docs API)
     - `https://www.googleapis.com/auth/drive.file` (Google Drive API)
   - "업데이트" 클릭
5. **테스트 사용자**:
   - "테스트 사용자 추가" 클릭
   - `pakseri@gmail.com` 추가
   - "저장" 클릭

#### 1.3 사용자 인증 정보 확인
1. "API 및 서비스" → "사용자 인증 정보"로 이동
2. OAuth 2.0 클라이언트 ID 클릭
3. 다음 정보 확인:
   - 클라이언트 ID: `1050278621988-s7bg1k15tm114icvq2ad8aa49ohj2q5t.apps.googleusercontent.com`
   - 클라이언트 시크릿: `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`

### 2. 환경 설정

#### 2.1 환경 변수 설정
`.env` 파일에 다음 설정을 추가하거나 확인:

```bash
# Google Docs Archive 설정
GOOGLE_DOCS_ARCHIVE_ENABLED=true
GOOGLE_DOCS_ARCHIVE_FOLDER=AI_SEO_Blogger_Archive
GOOGLE_DOCS_AUTO_ARCHIVE=true

# Google Drive API 설정 (기존)
GOOGLE_DRIVE_CLIENT_ID=1050278621988-s7bg1k15tm114icvq2ad8aa49ohj2q5t.apps.googleusercontent.com
GOOGLE_DRIVE_CLIENT_SECRET=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
GOOGLE_DRIVE_CREDENTIALS_PATH=credentials.json
GOOGLE_DRIVE_TOKEN_PATH=token.json
```

#### 2.2 필요한 패키지 설치
다음 패키지들이 이미 설치되어 있는지 확인:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 3. 초기 인증

#### 3.1 첫 번째 실행
애플리케이션을 처음 실행하면 브라우저가 열리며 Google 계정 인증을 요청합니다.

#### 3.2 권한 부여
1. Google 계정으로 로그인
2. 다음 권한 요청 승인:
   - Google Docs API 권한
   - Google Drive API 권한
3. 인증 완료 후 `token.json` 파일이 자동 생성됨

## 🚀 사용 방법

### 1. 자동 Archive (기본 설정)

블로그 포스트 생성 시 자동으로 Google Docs로 Archive 저장됩니다:

```bash
# 향상된 블로그 포스트 생성 (자동 Archive 포함)
POST /api/v1/blog-generation/generate-post-enhanced
{
    "url": "https://example.com/article",
    "content_length": "3000",
    "ai_mode": "enhanced"
}
```

응답에 `archive_url` 필드가 포함됩니다:

```json
{
    "success": true,
    "data": {
        "id": 123,
        "title": "생성된 블로그 포스트 제목",
        "content": "...",
        "archive_url": "https://docs.google.com/document/d/1ABC.../edit"
    }
}
```

### 2. 수동 Archive

기존 블로그 포스트를 Google Docs로 Archive 저장:

```bash
POST /api/v1/blog-generation/archive/create
{
    "blog_post_id": 123
}
```

### 3. Archive 문서 관리

#### 3.1 Archive 문서 목록 조회
```bash
GET /api/v1/blog-generation/archive/documents?limit=10
```

#### 3.2 Archive 문서 삭제
```bash
DELETE /api/v1/blog-generation/archive/documents/{doc_id}
```

## 📁 Archive 폴더 구조

Google Drive에 다음과 같은 구조로 Archive가 저장됩니다:

```
AI_SEO_Blogger_Archive/
├── 블로그포스트제목_20241201_143022
├── 블로그포스트제목_20241201_150315
├── 블로그포스트제목_20241201_162045
└── ...
```

각 문서는 다음 정보를 포함합니다:
- 제목 (스타일링된 헤더)
- 키워드
- 생성일
- 출처 URL
- AI 모드
- 본문 내용 (HTML 태그 제거됨)
- 요약 (있는 경우)

## ⚙️ 설정 옵션

### config.py에서 설정 가능한 옵션:

```python
# Google Docs Archive 설정
google_docs_archive_enabled: bool = True          # Archive 기능 활성화/비활성화
google_docs_archive_folder: str = "AI_SEO_Blogger_Archive"  # Archive 폴더 이름
google_docs_auto_archive: bool = True             # 자동 Archive 활성화/비활성화
```

## 🧪 테스트

### 테스트 스크립트 실행
```bash
python test_google_docs_archive.py
```

이 스크립트는 다음을 테스트합니다:
1. Google Docs API 인증
2. Archive 폴더 생성
3. 테스트 문서 생성
4. 문서 목록 조회
5. API 엔드포인트 테스트

## 🔍 문제 해결

### 1. 인증 오류
- `token.json` 파일을 삭제하고 다시 인증
- Google Cloud Console에서 OAuth 동의 화면 설정 확인
- 테스트 사용자에 본인 이메일이 추가되어 있는지 확인

### 2. 권한 오류
- Google Docs API가 활성화되어 있는지 확인
- OAuth 2.0 클라이언트 ID가 올바른지 확인
- 필요한 범위가 추가되어 있는지 확인

### 3. 문서 생성 오류
- Google Drive 저장 공간 확인
- 파일 크기 제한 확인 (Google Drive 무료 계정: 15GB)
- 네트워크 연결 상태 확인

### 4. Archive 비활성화
Archive 기능을 일시적으로 비활성화하려면:

```python
# config.py에서
google_docs_archive_enabled = False
google_docs_auto_archive = False
```

또는 환경 변수로:

```bash
GOOGLE_DOCS_ARCHIVE_ENABLED=false
GOOGLE_DOCS_AUTO_ARCHIVE=false
```

## 📊 모니터링

### 로그 확인
Archive 관련 로그는 다음과 같이 확인할 수 있습니다:

```bash
# 애플리케이션 로그에서 Archive 관련 메시지 확인
grep "Archive" app.log
grep "Google Docs" app.log
```

### 성공적인 Archive 로그 예시:
```
INFO: 📄 7단계: Google Docs Archive 저장
INFO: ✅ Google Docs Archive 완료: https://docs.google.com/document/d/1ABC.../edit
```

## 🔒 보안 주의사항

1. **파일 보안**:
   - `credentials.json`과 `token.json` 파일을 Git에 커밋하지 마세요
   - `.gitignore`에 다음 항목이 포함되어 있는지 확인:
     ```
     credentials.json
     token.json
     .env
     ```

2. **권한 관리**:
   - Google Docs API는 최소한의 권한만 요청합니다
   - 필요시 Google Cloud Console에서 권한을 조정할 수 있습니다

3. **데이터 보호**:
   - Archive된 문서는 Google Drive의 개인 폴더에 저장됩니다
   - 필요에 따라 공유 설정을 조정할 수 있습니다

## 📈 성능 최적화

1. **비동기 처리**: Archive 저장은 비동기로 처리되어 블로그 생성 속도에 영향을 주지 않습니다.

2. **오류 처리**: Archive 저장 실패 시에도 블로그 생성은 계속 진행됩니다.

3. **캐싱**: 인증 토큰은 캐시되어 반복 인증을 방지합니다.

## 🎯 향후 개선 계획

1. **배치 Archive**: 여러 포스트를 한 번에 Archive
2. **템플릿 커스터마이징**: Archive 문서 형식 사용자 정의
3. **태그 시스템**: Archive 문서에 태그 추가
4. **검색 기능**: Archive 문서 내 검색 기능
5. **통계 대시보드**: Archive 사용 통계 제공
