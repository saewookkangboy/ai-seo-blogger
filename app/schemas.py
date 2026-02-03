from pydantic import BaseModel, HttpUrl, validator, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime

class PostRequest(BaseModel):
    """블로그 포스트 생성 요청 모델"""
    url: Optional[str] = None
    text: Optional[str] = None
    keywords: Optional[str] = None  # 키워드 필드 추가
    rules: Optional[List[str]] = None
    ai_mode: Optional[str] = None
    content_length: Optional[str] = "3000"
    policy_auto: Optional[bool] = False
    
    @validator('url')
    def validate_url(cls, v):
        if not v:
            return v
        if len(v) > 2000:
            raise ValueError('URL은 2000자 이하여야 합니다.')
        if not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v

    @validator('text')
    def validate_text(cls, v):
        if not v:
            return v
        s = v.strip()
        if len(s) < 5:
            raise ValueError('텍스트는 최소 5자 이상이어야 합니다.')
        if len(s) > 100000:
            raise ValueError('텍스트는 100000자 이하여야 합니다.')
        return v

    @validator('keywords')
    def validate_keywords(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('키워드는 최소 2자 이상이어야 합니다.')
        return v

class SEOAnalysisResult(BaseModel):
    """SEO 분석 결과 모델"""
    content_structure_score: int
    content_structure_analysis: dict
    eeat_score: int
    eeat_analysis: dict
    technical_optimization_score: int
    technical_analysis: dict
    external_mentions_score: int
    external_analysis: dict
    ai_citation_score: int
    ai_citation_analysis: dict
    geo_optimization_score: int
    geo_analysis: dict
    structured_data_score: int
    structured_data_analysis: dict
    improvement_recommendations: List[str]
    overall_score: int

class PostResponse(BaseModel):
    """블로그 포스트 생성 응답 모델"""
    success: bool
    message: str
    data: dict

class BlogPostResponse(BaseModel):
    """블로그 포스트 조회 응답 모델"""
    id: int
    title: str
    original_url: Optional[str]
    keywords: Optional[str]
    content_html: str
    meta_description: Optional[str]
    word_count: Optional[int] = 0
    content_length: Optional[str] = "3000"
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    detail: str
    error_code: Optional[str] = None


# 콘텐츠 개선 / 키워드 생성 관련 스키마
class GenerateFromKeywordRequest(BaseModel):
    """키워드 기반 포스트 생성 요청 모델 (FR-B07)"""
    keyword_id: int


class ImproveContentRequest(BaseModel):
    """콘텐츠 개선 요청 모델 (FR-B08)"""
    original_content: str
    suggestions: Optional[List[Dict[str, Any]]] = []
    improvement_prompt: Optional[str] = ""


class ImproveContentSuggestionRequest(BaseModel):
    """개별 제안사항 적용 요청 모델 (FR-B08)"""
    content: str
    action: Optional[str] = None  # addHeadings, addFAQ, addSources, expandContent, addBalance, addStructuredData
    suggestion: Optional[Dict[str, Any]] = None
    keywords: Optional[str] = ""


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
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        return str(v)

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
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        return str(v)

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

# Google Drive API 관련 스키마
class GoogleDriveExportRequest(BaseModel):
    """Google Drive 내보내기 요청 모델"""
    folder_name: Optional[str] = None
    include_content: Optional[bool] = True
    include_stats: Optional[bool] = True

class GoogleDriveBackupRequest(BaseModel):
    """Google Drive 백업 요청 모델"""
    schedule_type: str = "daily"  # daily, weekly, monthly
    folder_name: Optional[str] = None

class GoogleDriveResponse(BaseModel):
    """Google Drive 응답 모델"""
    success: bool
    message: str
    folder_id: Optional[str] = None
    folder_name: Optional[str] = None
    files_count: Optional[int] = None
    timestamp: str

class GoogleDriveFileInfo(BaseModel):
    """Google Drive 파일 정보 모델"""
    name: str
    id: str
    count: int
    mime_type: Optional[str] = None
    size: Optional[int] = None
    created_time: Optional[str] = None

class GoogleDriveExportResult(BaseModel):
    """Google Drive 내보내기 결과 모델"""
    success: bool
    folder_id: str
    folder_name: str
    files: List[GoogleDriveFileInfo]
    error: Optional[str] = None 