from sqlalchemy.orm import Session
from sqlalchemy import desc
import re
from typing import List, Optional
from . import models
from .schemas import BlogPostResponse
from .utils.logger import setup_logger
from .models import APIKey, KeywordList, FeatureUpdate

logger = setup_logger(__name__)

def create_blog_post(
    db: Session, 
    title: str, 
    original_url: str, 
    keywords: str, 
    content_html: str,
    meta_description: Optional[str] = None,
    word_count: Optional[int] = None
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
            word_count=word_count or _count_words(content_html)
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

def add_keyword_to_list(db: Session, list_type: str, keyword: str):
    entry = KeywordList(type=list_type, keyword=keyword)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

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