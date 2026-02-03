from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from .config import settings
from sqlalchemy import text
import logging
import os

logger = logging.getLogger(__name__)

# Vercel 서버리스: 파일시스템이 읽기 전용이므로 SQLite는 /tmp 사용
_database_url = settings.database_url
if os.environ.get("VERCEL") == "1" and _database_url.startswith("sqlite"):
    if _database_url.startswith("sqlite:///./") or _database_url == "sqlite:///./blog.db":
        _database_url = "sqlite:////tmp/blog.db"
    elif _database_url.startswith("sqlite:///"):
        _database_url = "sqlite:////tmp/blog.db"
else:
    _database_url = settings.database_url

# SQLAlchemy 엔진 생성 (성능 최적화)
if _database_url.startswith("sqlite"):
    # SQLite를 사용할 때의 설정 (성능 최적화)
    engine = create_engine(
        _database_url,
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
            # blog_posts 테이블 인덱스 (최적화)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blog_posts_created_at_desc 
                ON blog_posts(created_at DESC)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blog_posts_title_lower 
                ON blog_posts(LOWER(title))
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blog_posts_keywords 
                ON blog_posts(keywords) WHERE keywords IS NOT NULL
            """))
            
            # 복합 인덱스 추가 (자주 함께 사용되는 컬럼)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blog_posts_status_created 
                ON blog_posts(status, created_at DESC)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blog_posts_category_status 
                ON blog_posts(category, status) WHERE category IS NOT NULL
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blog_posts_content_length 
                ON blog_posts(content_length) WHERE content_length IS NOT NULL
            """))
            
            # keyword_list 테이블 인덱스 (최적화)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_keyword_list_type_keyword 
                ON keyword_list(type, keyword)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_keyword_list_keyword_lower 
                ON keyword_list(LOWER(keyword))
            """))
            
            # api_keys 테이블 인덱스 (최적화)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_service_active 
                ON api_keys(service, is_active) WHERE is_active = 1
            """))
            
            # feature_updates 테이블 인덱스 추가
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_feature_updates_date 
                ON feature_updates(date DESC)
            """))
            
            conn.commit()
            logger.info("✅ 데이터베이스 인덱스 생성 완료 (최적화됨)")
            
    except Exception as e:
        logger.error(f"❌ 인덱스 생성 중 오류: {e}")

# 애플리케이션 시작 시 인덱스 생성
create_indexes()