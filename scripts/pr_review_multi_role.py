#!/usr/bin/env python3
"""
Dev Agent Kit 다중 역할 기반 PR 코드리뷰

- gh CLI로 현재 브랜치 PR의 diff 및 메타데이터 조회
- 변경 파일을 역할(PM, Frontend, Backend, Server/DB, Security, UI/UX, AI Marketing Researcher)에 매핑
- 각 역할별 체크리스트 기반 리뷰 템플릿 생성
- (선택) GitHub PR 코멘트로 게시

사용법:
  python scripts/pr_review_multi_role.py                    # PR diff 기반 리뷰 (stdout)
  python scripts/pr_review_multi_role.py --post             # PR에 코멘트 게시
  python scripts/pr_review_multi_role.py --pr 42            # 특정 PR 지정
  python scripts/pr_review_multi_role.py --all              # 전체 서비스 파일 리뷰 (PR 불필요)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

# dev-agent-kit 역할별 체크리스트 (reference.md 기반)
ROLE_CHECKLISTS = {
    "PM": [
        "범위·일정·우선순위 명확화",
        "스펙·To-do 정합성 검토",
        "리스크·의존성 식별",
    ],
    "Frontend": [
        "UI/UX, 접근성(a11y), 반응형",
        "컴포넌트·상태 관리 일관성",
        "성능(번들, 렌더링)",
    ],
    "Backend": [
        "API 설계(REST/GraphQL), 버전·에러 형식",
        "비동기·트랜잭션·재시도",
        "인증·인가·입력 검증",
    ],
    "Server/DB": [
        "DB 스키마·마이그레이션·인덱스",
        "인프라·배포·모니터링",
        "백업·복구",
    ],
    "Security": [
        "OWASP Top 10, 입력 검증·이스케이프",
        "시크릿·암호화·헤더",
        "감사 로그",
    ],
    "UI/UX": [
        "사용자 플로우·와이어프레임",
        "디자인 시스템·토큰",
        "접근성·다국어",
    ],
    "AI Marketing Researcher": [
        "키워드·경쟁 분석",
        "AI SEO·GEO 관점 콘텐츠",
        "인용·신뢰도·스키마",
    ],
}

# 파일 패턴 → 적용 역할 (ai-seo-blogger 전체 서비스 커버리지)
FILE_ROLE_MAP = [
    # Frontend / UI
    (r"\.(html|js|ts|jsx|tsx|css)$", ["Frontend", "UI/UX"]),
    (r"^app/static/", ["Frontend", "UI/UX"]),
    (r"^app/templates/", ["Frontend", "UI/UX"]),
    (r"static/|templates/", ["Frontend", "UI/UX"]),
    # Backend - app
    (r"^app/main\.py", ["Backend", "Security"]),
    (r"^app/config\.py", ["Backend", "Security"]),
    (r"^app/crud\.py", ["Backend", "Server/DB"]),
    (r"^app/models\.py", ["Backend", "Server/DB"]),
    (r"^app/schemas\.py", ["Backend"]),
    (r"^app/exceptions\.py", ["Backend"]),
    (r"^app/scheduler\.py", ["Backend", "Server/DB"]),
    (r"^app/routers/", ["Backend", "Security"]),
    (r"^app/services/", ["Backend", "Security"]),
    (r"^app/utils/", ["Backend"]),
    (r"^app/database", ["Backend", "Server/DB"]),
    # SEO / AI SEO / GEO
    (r"content_generator|seo_|target_analyzer|keyword_manager", ["Backend", "AI Marketing Researcher"]),
    (r"ai_ethics|translator|crawler|readme_updater", ["Backend", "AI Marketing Researcher"]),
    (r"^app/seo_guidelines\.py", ["AI Marketing Researcher"]),
    (r"^app/seo_updater\.py", ["AI Marketing Researcher"]),
    (r"^custom_crawlers/", ["Backend", "AI Marketing Researcher"]),
    # Server / DB / 인프라
    (r"\.(sql)$", ["Server/DB"]),
    (r"migrate|init_db|create_tables", ["Server/DB"]),
    (r"Dockerfile|\.dockerignore", ["Server/DB"]),
    (r"\.(yml|yaml)$", ["Server/DB"]),
    (r"^aws/|aws-deploy|terraform", ["Server/DB"]),
    (r"^\.github/", ["Server/DB"]),
    (r"Makefile|requirements\.txt|run\.py|run_server\.py", ["Server/DB"]),
    (r"pytest\.ini", ["Server/DB", "PM"]),
    # Security
    (r"\.env\.|env\.example", ["Security"]),
    (r"config\.py|secrets", ["Security"]),
    # PM / 문서 / 스펙
    (r"^docs/|^\.spec-kit/", ["PM", "AI Marketing Researcher"]),
    (r"\.project-data/|TODO\.md|CHANGELOG\.md", ["PM"]),
    (r"^[A-Z_]+.*\.md$", ["PM", "AI Marketing Researcher"]),  # 루트 리포트/가이드
    (r"\.md$", ["PM", "AI Marketing Researcher"]),
    # Tests
    (r"^tests/|test_.*\.py", ["PM", "Backend"]),
    # Python (공통)
    (r"\.py$", ["Backend"]),
    # JSON 설정
    (r"\.(json)$", ["Backend"]),
]


def _run(cmd: list[str], capture: bool = True, check: bool = True) -> str:
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout if capture else ""


def gh_pr_view(pr: int | None = None) -> dict:
    cmd = ["gh", "pr", "view"]
    if pr is not None:
        cmd.extend([str(pr)])
    cmd.extend(["--json", "number,title,url,body,changedFiles"])
    out = _run(cmd)
    return json.loads(out)


def gh_pr_diff(pr: int | None = None) -> str:
    cmd = ["gh", "pr", "diff"]
    if pr is not None:
        cmd.extend([str(pr)])
    return _run(cmd)


def get_changed_files(pr: int | None = None) -> list[str]:
    """PR diff에서 변경된 파일 경로 목록 추출."""
    diff = gh_pr_diff(pr)
    files: list[str] = []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/(.+?) b/.+", line)
            if m:
                files.append(m.group(1))
    return list(dict.fromkeys(files))  # 중복 제거, 순서 유지


def get_all_tracked_files() -> list[str]:
    """Git 추적 중인 전체 서비스 파일 목록 (제외: .git, node_modules, __pycache__ 등)."""
    out = _run(["git", "ls-files"])
    exclude = {
        ".git", "node_modules", "__pycache__", ".pyc",
        ".env.backup", ".cursor/projects",
    }
    files = []
    for line in out.strip().splitlines():
        path = line.strip()
        if not path:
            continue
        if any(ex in path for ex in exclude):
            continue
        files.append(path)
    return sorted(files)


def map_files_to_roles(files: list[str]) -> dict[str, list[str]]:
    """변경 파일 → 적용할 역할 매핑."""
    role_to_files: dict[str, list[str]] = {}
    for f in files:
        roles_for_file: set[str] = {"PM", "Security"}  # PM, Security는 항상 적용
        for pattern, roles in FILE_ROLE_MAP:
            if re.search(pattern, f, re.IGNORECASE):
                roles_for_file.update(roles)
        for r in roles_for_file:
            role_to_files.setdefault(r, []).append(f)
    return role_to_files


def build_review_markdown(
    role_to_files: dict[str, list[str]],
    changed_files: list[str],
    pr_meta: dict | None = None,
) -> str:
    """다중 역할 기반 리뷰 마크다운 생성."""
    lines = [
        "## Dev Agent Kit — 다중 역할 코드리뷰",
        "",
    ]
    if pr_meta:
        lines.append(f"**PR #{pr_meta.get('number', '?')}**: {pr_meta.get('title', '')}")
    else:
        lines.append("**전체 서비스 파일**")
    lines.extend(["", "### 대상 파일", ""])
    for f in changed_files:
        lines.append(f"- `{f}`")
    lines.extend(["", "---", ""])

    for role in [
        "PM",
        "Frontend",
        "Backend",
        "Server/DB",
        "Security",
        "UI/UX",
        "AI Marketing Researcher",
    ]:
        files = role_to_files.get(role, [])
        if not files:
            continue
        lines.append(f"### {role}")
        lines.append("")
        lines.append(f"*관련 파일: {', '.join(f'`{x}`' for x in files[:5])}"
                    + (f" 외 {len(files)-5}개" if len(files) > 5 else ""))
        lines.append("")
        for item in ROLE_CHECKLISTS.get(role, []):
            lines.append(f"- [ ] {item}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "*이 리뷰는 [dev-agent-kit](https://github.com/saewookkangboy/dev-agent-kit) 역할별 체크리스트를 기반으로 생성되었습니다.*",
    ])
    return "\n".join(lines)


def post_pr_comment(body: str, pr: int | None = None) -> None:
    """PR에 코멘트 게시."""
    cmd = ["gh", "pr", "comment"]
    if pr is not None:
        cmd.extend([str(pr)])
    proc = subprocess.run(
        cmd,
        input=body,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to post comment: {proc.stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dev Agent Kit 다중 역할 PR 코드리뷰")
    parser.add_argument("--pr", type=int, default=None, help="PR 번호 (미지정 시 현재 브랜치 PR)")
    parser.add_argument("--all", action="store_true", help="전체 서비스 파일 대상 리뷰 (PR 불필요)")
    parser.add_argument("--post", action="store_true", help="리뷰를 PR 코멘트로 게시")
    parser.add_argument("--json", action="store_true", help="JSON 형식으로 출력")
    args = parser.parse_args()

    if args.post and args.all:
        print("Error: --post는 PR 모드에서만 사용 가능합니다. --all과 함께 사용할 수 없습니다.", file=sys.stderr)
        return 1

    try:
        if args.all:
            changed_files = get_all_tracked_files()
            pr_meta = None
        else:
            pr_meta = gh_pr_view(args.pr)
            changed_files = get_changed_files(args.pr)

        role_to_files = map_files_to_roles(changed_files)
        review = build_review_markdown(role_to_files, changed_files, pr_meta)

        if args.json:
            out = {
                "pr": pr_meta,
                "changed_files": changed_files,
                "role_to_files": role_to_files,
                "review_markdown": review,
            }
            print(json.dumps(out, indent=2, ensure_ascii=False))
        else:
            print(review)

        if args.post and pr_meta:
            post_pr_comment(review, args.pr)
            print("\n✅ PR 코멘트가 게시되었습니다.", file=sys.stderr)

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
