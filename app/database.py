from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from .config import settings

# SQLAlchemy 엔진 생성
if settings.database_url.startswith("sqlite"):
    # SQLite를 사용할 때의 설정
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug
    )
else:
    # PostgreSQL 등 다른 데이터베이스를 사용할 때의 설정
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.debug
    )

# 데이터베이스 세션 생성을 위한 클래스
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 모델(테이블)을 정의할 때 상속받을 기본 클래스
Base = declarative_base()

# models.py에서 Base.metadata.create_all(bind=engine) 호출 필요 (main.py에서 이미 호출 중)

# 데이터베이스 세션 생성을 위한 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()