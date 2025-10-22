from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from .config import settings
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy 엔진 생성 (성능 최적화)
if settings.database_url.startswith("sqlite"):
    # SQLite를 사용할 때의 설정 (성능 최적화)
    engine = create_engine(
        settings.database_url,
        connect_args={
            "check_same_thread": False,
            "timeout": 30,
            "isolation_level": None  # autocommit 모드로 성능 향상
        },
        poolclass=StaticPool,
        pool_pre_ping=True,  # 연결 상태 확인
        echo=settings.debug
    )
else:
    # PostgreSQL 등 다른 데이터베이스를 사용할 때의 설정 (성능 최적화)
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=20,  # 연결 풀 크기 증가
        max_overflow=30,  # 최대 오버플로우 연결 수
        pool_recycle=3600,  # 연결 재사용 시간 (1시간)
        pool_timeout=30,  # 연결 타임아웃
        echo=settings.debug
    )

# 데이터베이스 세션 생성을 위한 클래스
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 모델(테이블)을 정의할 때 상속받을 기본 클래스
Base = declarative_base()

# models.py에서 Base.metadata.create_all(bind=engine) 호출 필요 (main.py에서 이미 호출 중)

# 데이터베이스 세션 생성을 위한 의존성 함수 (성능 최적화)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 비동기 데이터베이스 세션 (성능 최적화)
async def get_db_async():
    """비동기 데이터베이스 세션을 제공합니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 데이터베이스 연결 풀 상태 확인
def get_db_pool_status():
    """데이터베이스 연결 풀 상태를 반환합니다."""
    try:
        return {
            "pool_size": getattr(engine.pool, '_pool', {}).get('size', 0),
            "checked_in": getattr(engine.pool, '_pool', {}).get('checkedin', 0),
            "checked_out": getattr(engine.pool, '_pool', {}).get('checkedout', 0),
            "overflow": getattr(engine.pool, '_pool', {}).get('overflow', 0),
            "invalid": getattr(engine.pool, '_pool', {}).get('invalid', 0)
        }
    except Exception as e:
        logger.error(f"데이터베이스 풀 상태 확인 오류: {e}")
        return {
            "pool_size": 0,
            "checked_in": 0,
            "checked_out": 0,
            "overflow": 0,
            "invalid": 0
        }

# 데이터베이스 인덱스 생성 함수
def create_indexes():
    """데이터베이스 성능 최적화를 위한 인덱스를 생성합니다."""
    try:
        with engine.connect() as conn:
            # blog_posts 테이블 인덱스
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blog_posts_created_at 
                ON blog_posts(created_at DESC)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blog_posts_title 
                ON blog_posts(title)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blog_posts_keywords 
                ON blog_posts(keywords)
            """))
            
            # keyword_list 테이블 인덱스
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_keyword_list_type 
                ON keyword_list(type)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_keyword_list_keyword 
                ON keyword_list(keyword)
            """))
            
            # api_keys 테이블 인덱스
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_service 
                ON api_keys(service)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_active 
                ON api_keys(is_active)
            """))
            
            conn.commit()
            logger.info("데이터베이스 인덱스 생성 완료")
            
    except Exception as e:
        logger.error(f"인덱스 생성 중 오류: {e}")

# 애플리케이션 시작 시 인덱스 생성
create_indexes()