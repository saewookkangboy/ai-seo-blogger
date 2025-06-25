import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import subprocess
from datetime import date, datetime
from app.database import SessionLocal
from app.crud import upsert_update

def get_recent_commits(n=10):
    """
    최근 n개 커밋의 (날짜, 메시지) 리스트 반환
    """
    cmd = [
        'git', 'log', f'-{n}', "--pretty=format:%H|%ad|%s", '--date=short'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    commits = []
    for line in lines:
        parts = line.split('|', 2)
        if len(parts) == 3:
            _, d, msg = parts
            commits.append((d, msg.strip()))
    return commits

def main():
    db = SessionLocal()
    for d, msg in get_recent_commits():
        # 날짜 형식 변환 (YYYY-MM-DD)
        try:
            d_obj = date.fromisoformat(d)
        except Exception:
            continue
        upsert_update(db, d_obj, msg)
    db.close()
    print("최근 git 커밋 메시지 기반 기능 업데이트 이력 자동 등록 완료!")

if __name__ == "__main__":
    main() 