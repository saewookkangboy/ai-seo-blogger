import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import date
import re
from app.database import SessionLocal
from app.crud import upsert_update

README_PATH = os.path.join(os.path.dirname(__file__), '..', 'README.md')

def parse_feature_updates():
    """
    README.md에서 날짜별 기능 업데이트 이력을 파싱하여 dict로 반환
    { '2024-06-01': '내용', ... }
    """
    with open(README_PATH, encoding='utf-8') as f:
        text = f.read()
    # 날짜별 구간 추출 (예: - **2024.06** ...)
    pattern = re.compile(r'- \*\*(\d{4})\.(\d{2})\*\*\n((?:  - .+\n?)+)', re.MULTILINE)
    updates = {}
    for m in pattern.finditer(text):
        y, mth, content = m.group(1), m.group(2), m.group(3)
        d = f"{y}-{mth}-01"
        # 각 항목 앞의 '  - ' 제거
        content = re.sub(r'^  - ', '', content, flags=re.MULTILINE).strip()
        updates[d] = content
    return updates

def main():
    updates = parse_feature_updates()
    db = SessionLocal()
    for d, content in updates.items():
        upsert_update(db, date.fromisoformat(d), content)
    db.close()
    print("README.md 기반 기능 업데이트 이력 자동 등록 완료!")

if __name__ == "__main__":
    main() 