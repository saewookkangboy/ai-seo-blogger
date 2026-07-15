# Vercel 배포 환경 변수

Vercel에 배포할 때 설정해야 할 환경 변수 목록입니다. 값은 Vercel 대시보드 **Settings → Environment Variables**에서 설정하세요.

## 필수 (프로덕션 동작)

| 변수명 | 설명 | 비고 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API 키 | GPT 콘텐츠 생성·타겟 분석 |
| `GEMINI_API_KEY` | Google Gemini API 키 | Gemini 콘텐츠 생성·번역·타겟 분석 |
| `SESSION_SECRET` | 세션 암호화용 비밀 키 | 관리자 로그인·세션 (강한 랜덤 문자열 권장) |

## 데이터베이스

| 변수명 | 설명 | 비고 |
|--------|------|------|
| `DATABASE_URL` | DB 연결 문자열 | Vercel Postgres 사용 시 해당 URL 입력. SQLite 사용 시 기본값 가능 |

## 선택 (기능별)

| 변수명 | 설명 | 비고 |
|--------|------|------|
| `DEEPL_API_KEY` | DeepL 번역 API | 없으면 Gemini/OpenAI 번역 사용 |
| `NAVER_CLIENT_ID` | 네이버 검색광고 API | 키워드 도구 연동 시 |
| `NAVER_CLIENT_SECRET` | 네이버 검색광고 API 시크릿 | 키워드 도구 연동 시 |
| `GOOGLE_DRIVE_CLIENT_ID` | Google Drive OAuth 클라이언트 ID | Drive 백업 사용 시 |
| `GOOGLE_DRIVE_CLIENT_SECRET` | Google Drive OAuth 시크릿 | Drive 백업 사용 시 |

## 애플리케이션

| 변수명 | 설명 | 비고 |
|--------|------|------|
| `DEBUG` | 디버그 모드 | 프로덕션에서는 `False` 권장 |
| `LOG_LEVEL` | 로그 레벨 | `INFO` 또는 `WARNING` |

## 참고

- 로컬 템플릿: [env.example](../env.example) (실제 키는 넣지 말고 placeholder만 사용)
- 배포 사양: [.spec-kit/04-vercel-deployment.md](../.spec-kit/04-vercel-deployment.md) (있는 경우)
