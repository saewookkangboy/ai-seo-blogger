"""
Vercel 진입점: FastAPI 앱을 app.main에서 노출합니다.
Vercel은 app/app.py, app/index.py, app/server.py 중 하나에서 `app` 인스턴스를 찾습니다.
"""
from app.main import app

__all__ = ["app"]
