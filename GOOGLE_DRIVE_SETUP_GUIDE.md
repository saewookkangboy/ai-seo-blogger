# Google Drive API 설정 가이드

## 1. Google Cloud Console 설정

### 1.1 프로젝트 생성
1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택

### 1.2 Google Drive API 활성화
1. "API 및 서비스" > "라이브러리"로 이동
2. "Google Drive API" 검색 후 활성화

### 1.3 OAuth 동의 화면 설정
1. "API 및 서비스" > "OAuth 동의 화면"으로 이동
2. 사용자 유형: "외부" 선택
3. 앱 정보 입력:
   - 앱 이름: "AI SEO Blogger"
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처 정보: 본인 이메일
4. 범위 추가: "Google Drive API ../auth/drive.file" 선택
5. 테스트 사용자: 본인 Google 계정 이메일 추가

### 1.4 사용자 인증 정보 생성
1. "API 및 서비스" > "사용자 인증 정보"로 이동
2. "사용자 인증 정보 만들기" > "OAuth 2.0 클라이언트 ID" 선택
3. 애플리케이션 유형: "데스크톱 앱" 선택
4. 이름 입력: "AI SEO Blogger Desktop Client"
5. 생성 후 클라이언트 ID와 클라이언트 시크릿 확인

### 1.5 credentials.json 다운로드
1. 생성된 OAuth 2.0 클라이언트 ID 클릭
2. "JSON 다운로드" 버튼 클릭
3. 다운로드된 파일을 `credentials.json`으로 이름 변경
4. 프로젝트 루트 디렉토리에 저장

## 2. 환경 설정

### 2.1 환경 변수 설정
```bash
# .env 파일에 추가
GOOGLE_DRIVE_CLIENT_ID=your_client_id_here
GOOGLE_DRIVE_CLIENT_SECRET=your_client_secret_here
GOOGLE_DRIVE_CREDENTIALS_PATH=credentials.json
GOOGLE_DRIVE_TOKEN_PATH=token.json
GOOGLE_DRIVE_BACKUP_FOLDER=AI_SEO_Blogger_Backups
GOOGLE_DRIVE_AUTO_BACKUP=true
GOOGLE_DRIVE_BACKUP_SCHEDULE=daily
```

### 2.2 필요한 패키지 설치
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client pandas
```

## 3. 초기 인증

### 3.1 첫 번째 실행
애플리케이션을 처음 실행하면 브라우저가 열리며 Google 계정 인증을 요청합니다.

### 3.2 권한 부여
1. Google 계정으로 로그인
2. "Google Drive API" 권한 요청 승인
3. 인증 완료 후 `token.json` 파일이 자동 생성됨

## 4. API 엔드포인트

### 4.1 데이터베이스 내보내기
```bash
POST /api/v1/google-drive/export-database
{
    "folder_name": "AI_SEO_Blogger_Export_20241201",
    "include_content": true,
    "include_stats": true
}
```

### 4.2 자동 백업
```bash
POST /api/v1/google-drive/backup-database
{
    "schedule_type": "daily",
    "folder_name": "AutoBackup_Daily"
}
```

### 4.3 연결 테스트
```bash
GET /api/v1/google-drive/test-connection
```

## 5. 보안 주의사항

### 5.1 파일 보안
- `credentials.json`과 `token.json` 파일을 Git에 커밋하지 마세요
- `.gitignore`에 다음 항목 추가:
```
credentials.json
token.json
.env.google_drive
```

### 5.2 권한 관리
- Google Drive API는 최소한의 권한만 요청합니다
- 필요시 Google Cloud Console에서 권한을 조정할 수 있습니다

## 6. 문제 해결

### 6.1 401 invalid_client 오류
**원인**: OAuth 2.0 클라이언트 설정이 완료되지 않음

**해결 방법**:
1. Google Cloud Console에서 OAuth 동의 화면 설정 확인
2. 테스트 사용자에 본인 이메일 추가
3. 클라이언트 ID와 클라이언트 시크릿이 올바른지 확인
4. credentials.json 파일이 올바른 형식인지 확인

**credentials.json 예시**:
```json
{
  "installed": {
    "client_id": "1050278621988-s7bg1k15tm114icvq2ad8aa49ohj2q5t.apps.googleusercontent.com",
    "project_id": "ai-seo-blogger",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "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",
    "redirect_uris": ["http://localhost"]
  }
}
```

**테스트 사용자**: pakseri@gmail.com

### 6.2 인증 오류
- `token.json` 파일을 삭제하고 다시 인증
- Google Cloud Console에서 OAuth 동의 화면 설정 확인

### 6.3 권한 오류
- Google Drive API가 활성화되어 있는지 확인
- OAuth 2.0 클라이언트 ID가 올바른지 확인

### 6.4 파일 업로드 오류
- Google Drive 저장 공간 확인
- 파일 크기 제한 확인 (Google Drive 무료 계정: 15GB)

## 7. 단계별 설정 체크리스트

- [ ] Google Cloud Console 프로젝트 생성
- [ ] Google Drive API 활성화
- [ ] OAuth 동의 화면 설정 (외부 사용자)
- [ ] 테스트 사용자 추가
- [ ] OAuth 2.0 클라이언트 ID 생성 (데스크톱 앱)
- [ ] credentials.json 다운로드
- [ ] 환경 변수 설정
- [ ] 패키지 설치
- [ ] 초기 인증 테스트
