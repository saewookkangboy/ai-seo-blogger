# app/routers/news_archive.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from app.database import get_db
from app.utils.logger import setup_logger
from app.services.news_collector import NewsCollectorService

logger = setup_logger(__name__, "app.log")
router = APIRouter()

@router.get("/")
async def get_news_archive(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """뉴스 아카이브를 조회합니다."""
    try:
        service = NewsCollectorService()
        news_data = service.get_all_news()
        logger.info(f"뉴스 아카이브 조회 완료: {len(news_data)}개 뉴스")
        return news_data
    except Exception as e:
        logger.error(f"뉴스 아카이브 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="뉴스 아카이브를 불러오는데 실패했습니다.")

@router.post("/collect")
async def collect_news(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """AEO, GEO, AIO 뉴스를 수집합니다."""
    try:
        service = NewsCollectorService()
        result = service.collect_all_news()
        logger.info(f"뉴스 수집 완료: {result['total_collected']}개 수집")
        return result
    except Exception as e:
        logger.error(f"뉴스 수집 중 오류: {e}")
        raise HTTPException(status_code=500, detail="뉴스 수집에 실패했습니다.")

@router.get("/categories")
async def get_news_categories() -> Dict[str, Any]:
    """뉴스 카테고리별 통계를 반환합니다."""
    try:
        service = NewsCollectorService()
        categories = service.get_category_stats()
        return categories
    except Exception as e:
        logger.error(f"뉴스 카테고리 통계 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="뉴스 카테고리 통계를 불러오는데 실패했습니다.")

@router.get("/{news_id}/summary")
async def get_news_summary(news_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """특정 뉴스의 요약과 신뢰성 점수를 반환합니다."""
    try:
        service = NewsCollectorService()
        summary = service.get_news_summary(news_id)
        return summary
    except Exception as e:
        logger.error(f"뉴스 요약 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="뉴스 요약을 불러오는데 실패했습니다.")

@router.delete("/{news_id}")
async def delete_news(news_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """특정 뉴스를 삭제합니다."""
    try:
        service = NewsCollectorService()
        result = service.delete_news(news_id)
        return {"success": True, "message": "뉴스가 삭제되었습니다."}
    except Exception as e:
        logger.error(f"뉴스 삭제 중 오류: {e}")
        raise HTTPException(status_code=500, detail="뉴스 삭제에 실패했습니다.") 