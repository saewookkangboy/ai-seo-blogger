from sqlalchemy.orm import Session
from sqlalchemy import desc
import re
from typing import List, Optional
from . import models
from .schemas import BlogPostResponse
from .utils.logger import setup_logger
from .models import APIKey, KeywordList, FeatureUpdate
from datetime import datetime

logger = setup_logger(__name__)

def create_blog_post(
    db: Session, 
    title: str, 
    original_url: str, 
    keywords: str, 
    content_html: str,
    meta_description: Optional[str] = None,
    word_count: Optional[int] = None,
    content_length: Optional[str] = "3000"
) -> models.BlogPost:
    """
    새로운 블로그 포스트를 데이터베이스에 저장합니다.
    """
    try:
        db_post = models.BlogPost(
            title=title,
            original_url=original_url,
            keywords=keywords,
            content_html=content_html,
            meta_description=meta_description,
            word_count=word_count or _count_words(content_html),
            content_length=content_length
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        logger.info(f"새로운 블로그 포스트가 생성되었습니다: {title}")
        return db_post
    except Exception as e:
        db.rollback()
        logger.error(f"블로그 포스트 생성 중 오류 발생: {e}")
        raise

def get_blog_posts(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.BlogPost]:
    """
    저장된 모든 블로그 포스트 목록을 가져옵니다. (최신순)
    """
    try:
        return db.query(models.BlogPost).order_by(
            desc(models.BlogPost.created_at)
        ).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"블로그 포스트 조회 중 오류 발생: {e}")
        raise

def get_posts(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: str = None,
    category: str = None
) -> List[models.BlogPost]:
    """
    포스트 목록을 가져옵니다. (검색 및 필터링 지원)
    """
    try:
        query = db.query(models.BlogPost)
        
        if search:
            query = query.filter(
                models.BlogPost.title.contains(search) |
                models.BlogPost.keywords.contains(search) |
                models.BlogPost.content_html.contains(search)
            )
        
        if category:
            query = query.filter(models.BlogPost.keywords.contains(category))
        
        return query.order_by(desc(models.BlogPost.created_at)).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"포스트 목록 조회 중 오류 발생: {e}")
        raise

def get_posts_count(
    db: Session,
    search: str = None,
    category: str = None
) -> int:
    """
    포스트 개수를 가져옵니다.
    """
    try:
        query = db.query(models.BlogPost)
        
        if search:
            query = query.filter(
                models.BlogPost.title.contains(search) |
                models.BlogPost.keywords.contains(search) |
                models.BlogPost.content_html.contains(search)
            )
        
        if category:
            query = query.filter(models.BlogPost.keywords.contains(category))
        
        return query.count()
    except Exception as e:
        logger.error(f"포스트 개수 조회 중 오류 발생: {e}")
        raise

def get_post(db: Session, post_id: int) -> Optional[models.BlogPost]:
    """
    특정 포스트를 가져옵니다.
    """
    try:
        return db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    except Exception as e:
        logger.error(f"포스트 조회 중 오류 발생 (ID: {post_id}): {e}")
        raise

def delete_post(db: Session, post_id: int) -> bool:
    """
    특정 포스트를 삭제합니다.
    """
    try:
        post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
        if post:
            db.delete(post)
            db.commit()
            logger.info(f"포스트가 삭제되었습니다: {post.title}")
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"포스트 삭제 중 오류 발생 (ID: {post_id}): {e}")
        raise

def get_blog_post_by_id(db: Session, post_id: int) -> Optional[models.BlogPost]:
    """
    ID로 특정 블로그 포스트를 가져옵니다.
    """
    try:
        return db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    except Exception as e:
        logger.error(f"블로그 포스트 조회 중 오류 발생 (ID: {post_id}): {e}")
        raise

def delete_blog_post(db: Session, post_id: int) -> bool:
    """
    특정 블로그 포스트를 삭제합니다.
    """
    try:
        post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
        if post:
            db.delete(post)
            db.commit()
            logger.info(f"블로그 포스트가 삭제되었습니다: {post.title}")
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"블로그 포스트 삭제 중 오류 발생 (ID: {post_id}): {e}")
        raise

def search_blog_posts(
    db: Session, 
    keyword: str, 
    skip: int = 0, 
    limit: int = 50
) -> List[models.BlogPost]:
    """
    키워드로 블로그 포스트를 검색합니다.
    """
    try:
        return db.query(models.BlogPost).filter(
            models.BlogPost.title.contains(keyword) |
            models.BlogPost.keywords.contains(keyword) |
            models.BlogPost.content_html.contains(keyword)
        ).order_by(desc(models.BlogPost.created_at)).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"블로그 포스트 검색 중 오류 발생 (키워드: {keyword}): {e}")
        raise

def extract_title_from_html(html_content: str) -> str:
    """
    AI가 생성한 HTML에서 <h2> 태그의 내용을 제목으로 추출합니다.
    """
    try:
        match = re.search(r"<h2.*?>(.*?)</h2>", html_content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return "제목을 찾을 수 없음"
    except Exception as e:
        logger.error(f"HTML에서 제목 추출 중 오류 발생: {e}")
        return "제목을 찾을 수 없음"

def extract_meta_description_from_html(html_content: str) -> str:
    """
    AI가 생성한 HTML에서 메타 설명을 추출합니다.
    """
    try:
        match = re.search(r"<p><strong>메타 설명:</strong>\s*(.*?)</p>", html_content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    except Exception as e:
        logger.error(f"HTML에서 메타 설명 추출 중 오류 발생: {e}")
        return ""

def _count_words(text: str) -> int:
    """
    텍스트의 단어 수를 계산합니다.
    """
    try:
        # HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', text)
        # 공백으로 분리하여 단어 수 계산
        words = clean_text.split()
        return len(words)
    except Exception as e:
        logger.error(f"단어 수 계산 중 오류 발생: {e}")
        return 0

# API Key CRUD

def get_api_keys(db: Session, service: str = None, active_only: bool = False):
    q = db.query(APIKey)
    if service:
        q = q.filter(APIKey.service == service)
    if active_only:
        q = q.filter(APIKey.is_active == True)
    return q.order_by(APIKey.created_at.desc()).all()

def get_api_key_by_id(db: Session, key_id: int):
    return db.query(APIKey).filter(APIKey.id == key_id).first()

def create_api_key(db: Session, service: str, key: str, description: str = None, is_active: bool = True):
    api_key = APIKey(service=service, key=key, description=description, is_active=is_active)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key

def update_api_key(db: Session, key_id: int, **kwargs):
    api_key = get_api_key_by_id(db, key_id)
    if not api_key:
        return None
    for k, v in kwargs.items():
        if hasattr(api_key, k):
            setattr(api_key, k, v)
    db.commit()
    db.refresh(api_key)
    return api_key

def delete_api_key(db: Session, key_id: int):
    api_key = get_api_key_by_id(db, key_id)
    if not api_key:
        return False
    db.delete(api_key)
    db.commit()
    return True

# 키워드 블랙/화이트리스트 CRUD

def get_keywords_list(db: Session, list_type: str = None):
    q = db.query(KeywordList)
    if list_type:
        q = q.filter(KeywordList.type == list_type)
    return q.order_by(KeywordList.keyword).all()

def add_keyword_to_list(db: Session, keyword: str, type: str = "general") -> KeywordList:
    """키워드 리스트에 키워드 추가"""
    try:
        # 중복 확인
        existing = db.query(KeywordList).filter(
            KeywordList.keyword == keyword,
            KeywordList.type == type
        ).first()
        
        if existing:
            logger.warning(f"키워드가 이미 존재합니다: {keyword} (타입: {type})")
            return existing
        
        # 새 키워드 생성
        db_keyword = KeywordList(
            keyword=keyword,
            type=type,
            created_at=datetime.utcnow()
        )
        db.add(db_keyword)
        db.commit()
        db.refresh(db_keyword)
        
        logger.info(f"새 키워드가 추가되었습니다: {keyword} (타입: {type})")
        return db_keyword
        
    except Exception as e:
        logger.error(f"키워드 추가 중 오류 발생: {e}")
        db.rollback()
        raise

def initialize_default_keywords(db: Session) -> None:
    """기본 키워드 데이터 초기화"""
    default_keywords = [
        # AI 관련 키워드 (확장)
        ("AI", "ai"),
        ("인공지능", "ai"),
        ("머신러닝", "ai"),
        ("딥러닝", "ai"),
        ("자연어처리", "ai"),
        ("컴퓨터비전", "ai"),
        ("AI 모델", "ai"),
        ("AI 알고리즘", "ai"),
        ("AI 플랫폼", "ai"),
        ("AI 솔루션", "ai"),
        ("AI 서비스", "ai"),
        ("AI 기술", "ai"),
        ("AI 개발", "ai"),
        ("AI 연구", "ai"),
        ("AI 트렌드", "ai"),
        
        # SEO 관련 키워드 (확장)
        ("SEO", "seo"),
        ("검색엔진최적화", "seo"),
        ("키워드최적화", "seo"),
        ("백링크", "seo"),
        ("메타태그", "seo"),
        ("사이트맵", "seo"),
        ("SEO 전략", "seo"),
        ("SEO 도구", "seo"),
        ("SEO 분석", "seo"),
        ("SEO 리포트", "seo"),
        ("검색순위", "seo"),
        ("구글순위", "seo"),
        ("SEO 팁", "seo"),
        ("SEO 가이드", "seo"),
        ("SEO 최적화", "seo"),
        
        # 기술 관련 키워드 (확장)
        ("프로그래밍", "tech"),
        ("개발", "tech"),
        ("코딩", "tech"),
        ("알고리즘", "tech"),
        ("데이터구조", "tech"),
        ("웹개발", "tech"),
        ("모바일앱", "tech"),
        ("클라우드", "tech"),
        ("데이터베이스", "tech"),
        ("API", "tech"),
        ("개발도구", "tech"),
        ("프레임워크", "tech"),
        ("라이브러리", "tech"),
        ("버전관리", "tech"),
        ("개발환경", "tech"),
        
        # 마케팅 관련 키워드 (확장)
        ("디지털마케팅", "marketing"),
        ("콘텐츠마케팅", "marketing"),
        ("소셜미디어", "marketing"),
        ("인플루언서", "marketing"),
        ("브랜딩", "marketing"),
        ("고객경험", "marketing"),
        ("마케팅전략", "marketing"),
        ("마케팅도구", "marketing"),
        ("마케팅분석", "marketing"),
        ("마케팅자동화", "marketing"),
        ("마케팅캠페인", "marketing"),
        ("마케팅성과", "marketing"),
        ("마케팅트렌드", "marketing"),
        ("마케팅팁", "marketing"),
        ("마케팅가이드", "marketing"),
        
        # 비즈니스 관련 키워드 (확장)
        ("스타트업", "business"),
        ("창업", "business"),
        ("투자", "business"),
        ("수익화", "business"),
        ("성장전략", "business"),
        ("시장분석", "business"),
        ("비즈니스모델", "business"),
        ("경영전략", "business"),
        ("비즈니스개발", "business"),
        ("비즈니스분석", "business"),
        ("비즈니스도구", "business"),
        ("비즈니스트렌드", "business"),
        ("비즈니스팁", "business"),
        ("비즈니스가이드", "business"),
        ("비즈니스성공", "business"),
        
        # 최신 트렌드 키워드
        ("메타버스", "trend"),
        ("블록체인", "trend"),
        ("NFT", "trend"),
        ("크립토", "trend"),
        ("웹3", "trend"),
        ("5G", "trend"),
        ("IoT", "trend"),
        ("빅데이터", "trend"),
        ("데이터분석", "trend"),
        ("데이터사이언스", "trend"),
        ("클라우드컴퓨팅", "trend"),
        ("엣지컴퓨팅", "trend"),
        ("양자컴퓨팅", "trend"),
        ("자율주행", "trend"),
        ("드론", "trend"),
        
        # 실용적 키워드
        ("하우투", "howto"),
        ("가이드", "howto"),
        ("튜토리얼", "howto"),
        ("팁", "howto"),
        ("노하우", "howto"),
        ("방법", "howto"),
        ("기법", "howto"),
        ("전략", "howto"),
        ("솔루션", "howto"),
        ("도구", "howto"),
        ("서비스", "howto"),
        ("플랫폼", "howto"),
        ("앱", "howto"),
        ("소프트웨어", "howto"),
        ("하드웨어", "howto")
    ]
    
    try:
        for keyword, keyword_type in default_keywords:
            add_keyword_to_list(db, keyword, keyword_type)
        
        logger.info(f"기본 키워드 {len(default_keywords)}개가 초기화되었습니다.")
        
    except Exception as e:
        logger.error(f"기본 키워드 초기화 중 오류 발생: {e}")
        raise

def delete_keyword_from_list(db: Session, list_type: str, keyword: str):
    entry = db.query(KeywordList).filter(KeywordList.type == list_type, KeywordList.keyword == keyword).first()
    if entry:
        db.delete(entry)
        db.commit()
        return True
    return False

def bulk_add_keywords(db: Session, list_type: str, keywords: list[str]):
    entries = [KeywordList(type=list_type, keyword=k) for k in keywords]
    db.bulk_save_objects(entries)
    db.commit()
    return entries

def bulk_delete_keywords(db: Session, list_type: str, keywords: list[str]):
    db.query(KeywordList).filter(KeywordList.type == list_type, KeywordList.keyword.in_(keywords)).delete(synchronize_session=False)
    db.commit()

def get_keyword_by_id(db: Session, keyword_id: int):
    """ID로 키워드를 조회합니다."""
    try:
        return db.query(models.KeywordList).filter(models.KeywordList.id == keyword_id).first()
    except Exception as e:
        logger.error(f"키워드 조회 중 오류: {e}")
        return None

def delete_keyword(db: Session, keyword_id: int):
    """ID로 키워드를 삭제합니다."""
    try:
        keyword = db.query(models.KeywordList).filter(models.KeywordList.id == keyword_id).first()
        if keyword:
            db.delete(keyword)
            db.commit()
            logger.info(f"키워드 삭제 완료: ID {keyword_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"키워드 삭제 중 오류: {e}")
        db.rollback()
        return False

def get_keywords(db: Session, skip: int = 0, limit: int = 100, search: str = None, category: str = None):
    """키워드 목록을 조회합니다. (검색 및 필터링 지원)"""
    try:
        query = db.query(models.KeywordList)
        
        if search:
            query = query.filter(models.KeywordList.keyword.contains(search))
        
        if category:
            query = query.filter(models.KeywordList.type == category)
        
        keywords = query.offset(skip).limit(limit).all()
        return [
            {
                "id": keyword.id,
                "keyword": keyword.keyword,
                "type": keyword.type,
                "category": keyword.type,  # 호환성을 위해
                "description": getattr(keyword, 'description', None),
                "search_volume": getattr(keyword, 'search_volume', None),
                "competition": getattr(keyword, 'competition', 'medium'),
                "status": getattr(keyword, 'status', 'active'),
                "usage_count": getattr(keyword, 'usage_count', 0),
                "created_at": keyword.created_at.isoformat() if keyword.created_at else None,
                "updated_at": keyword.updated_at.isoformat() if keyword.updated_at else None
            }
            for keyword in keywords
        ]
    except Exception as e:
        logger.error(f"키워드 목록 조회 중 오류: {e}")
        return []

def get_keywords_count(db: Session, search: str = None, category: str = None) -> int:
    """키워드 개수를 가져옵니다."""
    try:
        query = db.query(models.KeywordList)
        
        if search:
            query = query.filter(models.KeywordList.keyword.contains(search))
        
        if category:
            query = query.filter(models.KeywordList.type == category)
        
        return query.count()
    except Exception as e:
        logger.error(f"키워드 개수 조회 중 오류: {e}")
        return 0

def get_keyword(db: Session, keyword_id: int):
    """특정 키워드를 가져옵니다."""
    try:
        keyword = db.query(models.KeywordList).filter(models.KeywordList.id == keyword_id).first()
        if keyword:
            return {
                "id": keyword.id,
                "keyword": keyword.keyword,
                "type": keyword.type,
                "category": keyword.type,
                "description": getattr(keyword, 'description', None),
                "search_volume": getattr(keyword, 'search_volume', None),
                "competition": getattr(keyword, 'competition', 'medium'),
                "status": getattr(keyword, 'status', 'active'),
                "usage_count": getattr(keyword, 'usage_count', 0),
                "created_at": keyword.created_at.isoformat() if keyword.created_at else None,
                "updated_at": keyword.updated_at.isoformat() if keyword.updated_at else None
            }
        return None
    except Exception as e:
        logger.error(f"키워드 조회 중 오류 (ID: {keyword_id}): {e}")
        return None

def create_keyword(db: Session, keyword_data: dict):
    """새로운 키워드를 생성합니다."""
    try:
        db_keyword = models.KeywordList(
            keyword=keyword_data.get('keyword'),
            type=keyword_data.get('category', 'general'),
            description=keyword_data.get('description'),
            search_volume=keyword_data.get('search_volume'),
            competition=keyword_data.get('competition', 'medium'),
            status=keyword_data.get('status', 'active')
        )
        db.add(db_keyword)
        db.commit()
        db.refresh(db_keyword)
        logger.info(f"새로운 키워드가 생성되었습니다: {keyword_data.get('keyword')}")
        return get_keyword(db, db_keyword.id)
    except Exception as e:
        db.rollback()
        logger.error(f"키워드 생성 중 오류: {e}")
        raise

def update_keyword(db: Session, keyword_id: int, keyword_data: dict):
    """키워드를 수정합니다."""
    try:
        keyword = db.query(models.KeywordList).filter(models.KeywordList.id == keyword_id).first()
        if keyword:
            if 'keyword' in keyword_data:
                keyword.keyword = keyword_data['keyword']
            if 'category' in keyword_data:
                keyword.type = keyword_data['category']
            if 'description' in keyword_data:
                keyword.description = keyword_data['description']
            if 'search_volume' in keyword_data:
                keyword.search_volume = keyword_data['search_volume']
            if 'competition' in keyword_data:
                keyword.competition = keyword_data['competition']
            if 'status' in keyword_data:
                keyword.status = keyword_data['status']
            
            db.commit()
            db.refresh(keyword)
            logger.info(f"키워드가 수정되었습니다: {keyword.keyword}")
            return get_keyword(db, keyword_id)
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"키워드 수정 중 오류 (ID: {keyword_id}): {e}")
        raise

def delete_keyword(db: Session, keyword_id: int) -> bool:
    """특정 키워드를 삭제합니다."""
    try:
        keyword = db.query(models.KeywordList).filter(models.KeywordList.id == keyword_id).first()
        if keyword:
            db.delete(keyword)
            db.commit()
            logger.info(f"키워드가 삭제되었습니다: {keyword.keyword}")
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"키워드 삭제 중 오류 (ID: {keyword_id}): {e}")
        raise

# 포스트 일괄 삭제/백업/복원

def bulk_delete_posts(db: Session, post_ids: list[int]):
    db.query(models.BlogPost).filter(models.BlogPost.id.in_(post_ids)).delete(synchronize_session=False)
    db.commit()
    return True

def export_posts(db: Session, post_ids: Optional[List[int]] = None):
    q = db.query(models.BlogPost)
    if post_ids:
        q = q.filter(models.BlogPost.id.in_(post_ids))
    posts = q.all()
    # JSON 직렬화
    def safe_str(dt):
        if dt is None:
            return None
        try:
            return str(dt)
        except Exception:
            return None
    return [
        {
            "id": p.id,
            "title": p.title,
            "original_url": p.original_url,
            "keywords": p.keywords,
            "content_html": p.content_html,
            "meta_description": p.meta_description,
            "word_count": p.word_count,
            "created_at": safe_str(p.created_at),
            "updated_at": safe_str(p.updated_at)
        }
        for p in posts
    ]

def import_posts(db: Session, posts_data: list[dict]):
    for pdata in posts_data:
        post = models.BlogPost(
            title=pdata.get("title"),
            original_url=pdata.get("original_url"),
            keywords=pdata.get("keywords"),
            content_html=pdata.get("content_html"),
            meta_description=pdata.get("meta_description"),
            word_count=pdata.get("word_count", 0)
        )
        db.add(post)
    db.commit()
    return True

def get_today_update(db: Session):
    from datetime import date
    return db.query(FeatureUpdate).filter(FeatureUpdate.date == date.today()).first()

def get_update_by_date(db: Session, target_date):
    return db.query(FeatureUpdate).filter(FeatureUpdate.date == target_date).first()

def get_update_history(db: Session, limit=30):
    return db.query(FeatureUpdate).order_by(FeatureUpdate.date.desc()).limit(limit).all()

def upsert_update(db: Session, target_date, content):
    obj = db.query(FeatureUpdate).filter(FeatureUpdate.date == target_date).first()
    if obj:
        obj.content = content
    else:
        from datetime import datetime
        obj = FeatureUpdate(date=target_date, content=content, created_at=datetime.utcnow())
        db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def validate_post_quality(post_content: str, title: str) -> dict:
    """포스트 품질을 검증합니다."""
    quality_score = 100
    issues = []
    suggestions = []
    
    # 길이 검증
    content_length = len(post_content)
    if content_length < 500:
        quality_score -= 30
        issues.append("콘텐츠가 너무 짧습니다")
        suggestions.append("최소 500자 이상으로 작성하세요")
    elif content_length < 1000:
        quality_score -= 10
        suggestions.append("더 자세한 내용을 추가하세요")
    
    # 제목 검증
    title_length = len(title)
    if title_length < 10:
        quality_score -= 20
        issues.append("제목이 너무 짧습니다")
        suggestions.append("제목을 10자 이상으로 작성하세요")
    elif title_length > 60:
        quality_score -= 10
        suggestions.append("제목이 너무 깁니다 (60자 이하 권장)")
    
    # 키워드 밀도 검증
    keyword_density = calculate_keyword_density(post_content, title)
    if keyword_density < 0.5:
        quality_score -= 15
        issues.append("키워드 밀도가 낮습니다")
        suggestions.append("주요 키워드를 자연스럽게 포함하세요")
    elif keyword_density > 3.0:
        quality_score -= 10
        issues.append("키워드 밀도가 너무 높습니다")
        suggestions.append("키워드 스팸을 피하세요")
    
    # HTML 구조 검증
    if "<h2>" not in post_content and "<h3>" not in post_content:
        quality_score -= 15
        issues.append("제목 구조가 없습니다")
        suggestions.append("H2, H3 태그를 사용하여 구조화하세요")
    
    if "<p>" not in post_content:
        quality_score -= 10
        issues.append("단락 구분이 없습니다")
        suggestions.append("P 태그를 사용하여 단락을 구분하세요")
    
    return {
        "score": max(0, quality_score),
        "issues": issues,
        "suggestions": suggestions,
        "content_length": content_length,
        "title_length": title_length,
        "keyword_density": keyword_density
    }

def calculate_keyword_density(content: str, title: str) -> float:
    """키워드 밀도를 계산합니다."""
    # 제목에서 주요 키워드 추출
    title_words = title.split()
    main_keywords = [word for word in title_words if len(word) > 1]
    
    if not main_keywords:
        return 0.0
    
    # 콘텐츠에서 키워드 출현 횟수 계산
    total_words = len(content.split())
    keyword_count = 0
    
    for keyword in main_keywords:
        keyword_count += content.lower().count(keyword.lower())
    
    # 키워드 밀도 계산 (백분율)
    return (keyword_count / total_words * 100) if total_words > 0 else 0.0

def improve_post_content(post_content: str, title: str) -> str:
    """포스트 콘텐츠를 개선합니다."""
    # 기본 HTML 구조 확인
    if not post_content.startswith("<"):
        post_content = f"<p>{post_content}</p>"
    
    # 제목 구조 추가
    if "<h2>" not in post_content and "<h3>" not in post_content:
        # 첫 번째 단락을 H2로 변경
        post_content = post_content.replace("<p>", "<h2>", 1)
        post_content = post_content.replace("</p>", "</h2>", 1)
    
    # 결론 섹션 추가
    if "결론" not in post_content and "마무리" not in post_content:
        conclusion = f"""
<h3>결론</h3>
<p>이상으로 {title}에 대한 내용을 마치겠습니다. 도움이 되었기를 바랍니다.</p>
"""
        post_content += conclusion
    
    return post_content

def get_total_posts(db: Session) -> int:
    """총 포스트 수를 반환합니다."""
    try:
        return db.query(models.BlogPost).count()
    except:
        return 0

def get_total_keywords(db: Session) -> int:
    """총 키워드 수를 반환합니다."""
    try:
        return db.query(models.KeywordList).count()
    except:
        return 0

def get_posts_stats(db: Session) -> dict:
    """포스트 분량별 통계를 반환합니다."""
    try:
        posts = db.query(models.BlogPost).all()
        stats = {"2000": 0, "3000": 0, "4000": 0, "5000": 0}
        
        for post in posts:
            content_length = post.content_length or 0
            if content_length <= 2000:
                stats["2000"] += 1
            elif content_length <= 3000:
                stats["3000"] += 1
            elif content_length <= 4000:
                stats["4000"] += 1
            else:
                stats["5000"] += 1
        
        return stats
    except:
        return {"2000": 0, "3000": 0, "4000": 0, "5000": 0}

def get_keywords_stats(db: Session) -> dict:
    """키워드 타입별 통계를 반환합니다."""
    try:
        keywords = db.query(models.KeywordList).all()
        stats = {}
        
        for keyword in keywords:
            keyword_type = keyword.type or "기타"
            stats[keyword_type] = stats.get(keyword_type, 0) + 1
        
        return stats
    except:
        return {}

def create_post(db: Session, post_data: dict) -> models.BlogPost:
    """새로운 포스트를 생성합니다."""
    try:
        db_post = models.BlogPost(
            title=post_data.get("title"),
            original_url=post_data.get("original_url", ""),
            keywords=post_data.get("keywords", ""),
            content_html=post_data.get("content", ""),
            meta_description=post_data.get("description", ""),
            word_count=post_data.get("word_count", 0),
            content_length=post_data.get("content_length", "3000"),
            category=post_data.get("category", "기타"),
            status=post_data.get("status", "draft")
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        logger.info(f"새로운 포스트가 생성되었습니다: {post_data.get('title')}")
        return db_post
    except Exception as e:
        db.rollback()
        logger.error(f"포스트 생성 중 오류 발생: {e}")
        raise

def update_post(db: Session, post_id: int, post_data: dict) -> models.BlogPost:
    """포스트를 업데이트합니다."""
    try:
        post = get_post(db, post_id)
        if not post:
            raise ValueError(f"포스트 ID {post_id}를 찾을 수 없습니다.")
        
        # 업데이트할 필드들
        if "title" in post_data:
            post.title = post_data["title"]
        if "keywords" in post_data:
            post.keywords = post_data["keywords"]
        if "content_html" in post_data:
            post.content_html = post_data["content_html"]
        if "meta_description" in post_data:
            post.meta_description = post_data["meta_description"]
        if "category" in post_data:
            post.category = post_data["category"]
        if "status" in post_data:
            post.status = post_data["status"]
        if "word_count" in post_data:
            post.word_count = post_data["word_count"]
        
        db.commit()
        db.refresh(post)
        logger.info(f"포스트가 업데이트되었습니다: {post_id}")
        return post
    except Exception as e:
        db.rollback()
        logger.error(f"포스트 업데이트 중 오류 발생: {e}")
        raise