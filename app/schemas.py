from pydantic import BaseModel, HttpUrl, validator, field_serializer
from typing import Optional, List
from datetime import datetime

class PostRequest(BaseModel):
    """블로그 포스트 생성 요청 모델"""
    url: Optional[str] = None
    text: Optional[str] = None
    rules: Optional[List[str]] = None
    ai_mode: Optional[str] = None
    policy_auto: Optional[bool] = False
    
    @validator('url')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v
    
    @validator('text')
    def validate_text(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError('텍스트는 최소 10자 이상이어야 합니다.')
        return v

class PostResponse(BaseModel):
    """블로그 포스트 생성 응답 모델"""
    post: str
    keywords: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    word_count: Optional[int] = None

class BlogPostResponse(BaseModel):
    """블로그 포스트 조회 응답 모델"""
    id: int
    title: str
    original_url: Optional[str]
    keywords: Optional[str]
    content_html: str
    meta_description: Optional[str]
    word_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    detail: str
    error_code: Optional[str] = None

# API Key 관련 스키마
class APIKeyBase(BaseModel):
    service: str
    description: Optional[str] = None
    is_active: Optional[bool] = True

class APIKeyCreate(APIKeyBase):
    key: str

class APIKeyUpdate(BaseModel):
    key: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class APIKeyOut(APIKeyBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True
    @field_serializer('created_at', 'updated_at')
    def serialize_dt(v, info):
        if v is None:
            return None
        if isinstance(v, str):
            return v
        return v.isoformat()

# 키워드 블랙/화이트리스트 관련 스키마
class KeywordListBase(BaseModel):
    type: str  # blacklist, whitelist
    keyword: str

class KeywordListOut(KeywordListBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    naver_volume: Optional[int] = None  # 네이버 월간 검색량
    naver_rank: Optional[int] = None    # 네이버 순위
    class Config:
        from_attributes = True
    @field_serializer('created_at', 'updated_at')
    def serialize_dt(v, info):
        if v is None:
            return None
        if isinstance(v, str):
            return v
        return v.isoformat()

class KeywordListBulkIn(BaseModel):
    type: str
    keywords: list[str]

# 포스트 일괄 삭제/백업/복원 관련 스키마
class PostExport(BaseModel):
    id: int
    title: str
    original_url: Optional[str] = None
    keywords: Optional[str] = None
    content_html: str
    meta_description: Optional[str] = None
    word_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class PostImport(BaseModel):
    title: str
    original_url: Optional[str] = None
    keywords: Optional[str] = None
    content_html: str
    meta_description: Optional[str] = None
    word_count: int = 0

class BulkDeleteIn(BaseModel):
    post_ids: list[int] 