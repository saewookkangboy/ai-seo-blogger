# AI SEO Blogger — Agent 가이드

이 프로젝트는 [dev-agent-kit](https://github.com/saewookkangboy/dev-agent-kit)과 통합되어 역할 기반 개발 및 PR 코드리뷰 자동화를 지원합니다.

## PR 및 코드리뷰 자동화

PR 리뷰 요청 시 **7가지 역할**(PM, Frontend, Backend, Server/DB, Security, UI/UX, AI Marketing Researcher)을 모두 활용한다.

### 로컬 실행

```bash
# PR 기반 (gh 인증 필요: gh auth login)
python scripts/pr_review_multi_role.py           # PR diff 리뷰 stdout 출력
python scripts/pr_review_multi_role.py --post    # PR에 코멘트 게시
python scripts/pr_review_multi_role.py --pr 42   # 특정 PR 지정

# 전체 서비스 (PR 불필요)
python scripts/pr_review_multi_role.py --all     # Git 추적 전체 파일 리뷰
```

### CI 자동화

- PR 생성/업데이트 시 `.github/workflows/pr-review.yml`이 자동 실행
- dev-agent-kit 역할별 체크리스트 기반 리뷰가 PR 코멘트로 게시됨

### 참고

- 사양: `docs/specs/pr-code-review-automation.md`
- dev-agent-kit 예시: `.cursor/skills/dev-agent-kit/examples.md` (예시 8)
- 역할별 업데이트: `docs/ROLE_UPDATES.md`
