from sqlalchemy import Column, Integer, String, Text, DateTime, Index, Boolean, Date
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime

class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), index=True, nullable=False)
    original_url = Column(String(1000))
    keywords = Column(String(500))
    content_html = Column(Text, nullable=False)
    meta_description = Column(String(300))
    word_count = Column(Integer, default=0)
    content_length = Column(String(10), default="3000")
    category = Column(String(50), default="기타")
    status = Column(String(20), default="draft")  # draft, published, archived
    description = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_title_keywords', 'title', 'keywords'),
        Index('idx_content_length', 'content_length'),
        Index('idx_created_at', 'created_at'),
        Index('idx_category', 'category'),
        Index('idx_status', 'status'),
    )

# API Key 관리 테이블
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(50), index=True, nullable=False)  # openai, deepl, gemini 등
    key = Column(String(200), nullable=False)
    description = Column(String(200))  # 용도/설명
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_service_active', 'service', 'is_active'),
    )

# 키워드 블랙/화이트리스트 테이블
class KeywordList(Base):
    __tablename__ = "keyword_list"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), index=True, nullable=False)  # blacklist, whitelist
    keyword = Column(String(200), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_type_keyword', 'type', 'keyword'),
    )

class FeatureUpdate(Base):
    __tablename__ = 'feature_updates'
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)