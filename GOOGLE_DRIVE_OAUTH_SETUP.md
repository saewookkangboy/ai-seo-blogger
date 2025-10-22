# Google Drive API 403 오류 해결 가이드

## 🚨 **403 access_denied 오류 해결**

### **원인**
- OAuth 동의 화면 설정이 완료되지 않음
- 테스트 사용자가 올바르게 설정되지 않음
- Google Drive API가 활성화되지 않음

---

## 📋 **단계별 해결 방법**

### **1단계: Google Cloud Console 접속**
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 선택: `ai-seo-blogger` (또는 해당 프로젝트)

### **2단계: Google Drive API 활성화**
1. 왼쪽 메뉴 → "API 및 서비스" → "라이브러리"
2. 검색창에 "Google Drive API" 입력
3. "Google Drive API" 클릭
4. "사용" 버튼 클릭

### **3단계: OAuth 동의 화면 설정**
1. 왼쪽 메뉴 → "API 및 서비스" → "OAuth 동의 화면"
2. **사용자 유형**: "외부" 선택
3. **앱 정보**:
   - 앱 이름: `AI SEO Blogger`
   - 사용자 지원 이메일: `pakseri@gmail.com`
   - 개발자 연락처 정보: `pakseri@gmail.com`
4. **범위**:
   - "범위 추가 또는 삭제" 클릭
   - "Google Drive API ../auth/drive.file" 선택
   - "업데이트" 클릭
5. **테스트 사용자**:
   - "테스트 사용자 추가" 클릭
   - **중요**: `pakseri@gmail.com` 추가
   - "저장" 클릭

### **4단계: 사용자 인증 정보 확인**
1. 왼쪽 메뉴 → "API 및 서비스" → "사용자 인증 정보"
2. OAuth 2.0 클라이언트 ID 클릭
3. 다음 정보 확인:
   - 클라이언트 ID: `1050278621988-s7bg1k15tm114icvq2ad8aa49ohj2q5t.apps.googleusercontent.com`
   - 클라이언트 시크릿: `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`

### **5단계: OAuth 동의 화면 상태 확인**
- **게시 상태**: "테스트" 모드여야 함
- **테스트 사용자**: `pakseri@gmail.com`이 목록에 있어야 함

---

## 🔍 **문제 진단**

### **체크리스트**
- [ ] Google Drive API가 활성화됨
- [ ] OAuth 동의 화면이 "외부" 사용자 유형으로 설정됨
- [ ] 테스트 사용자에 `pakseri@gmail.com`이 추가됨
- [ ] 범위에 "Google Drive API ../auth/drive.file"이 포함됨
- [ ] 클라이언트 ID와 시크릿이 올바름

### **오류 메시지별 해결책**

#### **403 access_denied**
- 테스트 사용자 확인
- OAuth 동의 화면 설정 확인

#### **401 invalid_client**
- 클라이언트 ID/시크릿 확인
- credentials.json 파일 확인

#### **400 invalid_request**
- 리디렉션 URI 확인
- 범위 설정 확인

---

## 🧪 **테스트 방법**

### **1. 브라우저에서 직접 테스트**
```
https://accounts.google.com/o/oauth2/auth
?response_type=code
&client_id=1050278621988-s7bg1k15tm114icvq2ad8aa49ohj2q5t.apps.googleusercontent.com
&redirect_uri=http://localhost:8080
&scope=https://www.googleapis.com/auth/drive.file
&access_type=offline
```

### **2. 간단한 테스트 스크립트**
```bash
python3 test_google_drive_simple.py
```

### **3. 전체 통합 테스트**
```bash
python3 tests/development/test_google_drive_integration.py
```

---

## 📞 **추가 지원**

문제가 지속되면 다음 정보를 확인해주세요:

1. **Google Cloud Console 스크린샷**
   - OAuth 동의 화면 설정
   - 사용자 인증 정보
   - API 라이브러리

2. **오류 로그**
   - 전체 오류 메시지
   - 브라우저 콘솔 로그

3. **설정 파일**
   - credentials.json 내용
   - 환경 변수 설정

---

## ✅ **성공 시 확인 사항**

인증이 성공하면 다음이 생성됩니다:
- `token.json` 파일
- Google Drive API 접근 권한
- 테스트 파일 업로드 가능

**마지막 업데이트**: 2025-01-27 