from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
import re
from datetime import datetime
from app.database import get_db
from app.services.update_history import UpdateHistoryService
from app.utils.logger import setup_logger
import json

logger = setup_logger(__name__, "app.log")
router = APIRouter()

@router.get("/history")
async def get_update_history(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """JSON 파일에서 업데이트 이력을 로드하여 반환합니다."""
    try:
        history_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "update_history.json")
        
        if not os.path.exists(history_file):
            logger.warning("update_history.json 파일을 찾을 수 없습니다.")
            return []
        
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        updates = data.get('updates', [])
        logger.info(f"업데이트 이력 로드 완료: {len(updates)}개 항목")
        return updates
        
    except Exception as e:
        logger.error(f"업데이트 이력 로드 중 오류: {e}")
        raise HTTPException(status_code=500, detail="업데이트 이력을 불러오는데 실패했습니다.")

@router.get("/statistics")
async def get_update_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """상세한 업데이트 이력 통계를 반환합니다."""
    try:
        history_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "update_history.json")
        
        if not os.path.exists(history_file):
            logger.warning("update_history.json 파일을 찾을 수 없습니다.")
            return {
                'total_updates': 0,
                'by_category': {},
                'by_importance': {},
                'by_impact_level': {},
                'performance_metrics': {},
                'trends': {},
                'last_updated': None
            }
        
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        statistics = data.get('statistics', {})
        logger.info(f"업데이트 이력 통계 로드 완료")
        return statistics
        
    except Exception as e:
        logger.error(f"업데이트 이력 통계 로드 중 오류: {e}")
        raise HTTPException(status_code=500, detail="업데이트 이력 통계를 불러오는데 실패했습니다.")

@router.post("/refresh")
async def refresh_update_history(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """업데이트 이력을 새로고침합니다."""
    try:
        service = UpdateHistoryService()
        result = service.auto_update_history()
        
        if result['success']:
            logger.info(f"업데이트 이력 새로고침 완료: {result['total_updates']}개 항목")
            return {
                'success': True,
                'message': f"업데이트 이력이 성공적으로 새로고침되었습니다. (총 {result['total_updates']}개 항목)",
                'total_updates': result['total_updates'],
                'last_updated': result['last_updated']
            }
        else:
            logger.error(f"업데이트 이력 새로고침 실패: {result.get('error', '알 수 없는 오류')}")
            raise HTTPException(status_code=500, detail=f"업데이트 이력 새로고침에 실패했습니다: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        logger.error(f"업데이트 이력 새로고침 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"업데이트 이력 새로고침 중 오류가 발생했습니다: {str(e)}")

@router.get("/trends")
async def get_update_trends(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """업데이트 이력 트렌드를 반환합니다."""
    try:
        history_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "update_history.json")
        
        if not os.path.exists(history_file):
            logger.warning("update_history.json 파일을 찾을 수 없습니다.")
            return {
                'hot_topics': [],
                'monthly_growth': {},
                'category_growth': {}
            }
        
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        trends = data.get('statistics', {}).get('trends', {})
        logger.info("업데이트 이력 트렌드 로드 완료")
        return trends
        
    except Exception as e:
        logger.error(f"업데이트 이력 트렌드 로드 중 오류: {e}")
        raise HTTPException(status_code=500, detail="업데이트 이력 트렌드를 불러오는데 실패했습니다.")

def parse_readme_updates(content: str) -> List[Dict[str, Any]]:
    """README.md에서 업데이트 이력을 파싱합니다."""
    updates = []
    
    # 연도별 섹션 찾기
    year_patterns = [
        r"## (\d{4})년 주요 변경 이력",
        r"## (\d{4})년 업데이트",
        r"## (\d{4})년 변경사항"
    ]
    
    for pattern in year_patterns:
        year_matches = re.finditer(pattern, content)
        for year_match in year_matches:
            year = year_match.group(1)
            year_start = year_match.end()
            
            # 다음 연도 섹션까지의 내용 추출
            next_year = re.search(r"## \d{4}년", content[year_start:])
            year_end = year_start + next_year.start() if next_year else len(content)
            year_content = content[year_start:year_end]
            
            # 월별 업데이트 파싱
            month_patterns = [
                r"- \*\*(\d{4}\.\d{2})\*\*",
                r"### (\d{4}\.\d{2})",
                r"#### (\d{4}\.\d{2})",
                r"- (\d{4}\.\d{2})"
            ]
            
            for month_pattern in month_patterns:
                month_matches = re.finditer(month_pattern, year_content)
                for month_match in month_matches:
                    month = month_match.group(1)
                    month_start = month_match.end()
                    
                    # 다음 월까지의 내용 추출
                    next_month = None
                    for next_pattern in month_patterns:
                        next_month = re.search(next_pattern, year_content[month_start:])
                        if next_month:
                            break
                    
                    month_end = month_start + next_month.start() if next_month else len(year_content)
                    month_content = year_content[month_start:month_end]
                    
                    # 개별 업데이트 항목 파싱
                    update_items = parse_update_items(month_content, month)
                    updates.extend(update_items)
    
    # 날짜순으로 정렬 (최신순)
    updates.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return updates

def parse_update_items(content: str, month: str) -> List[Dict[str, Any]]:
    """개별 업데이트 항목을 파싱합니다."""
    updates = []
    
    # 다양한 업데이트 패턴 지원
    patterns = [
        r'^\s*[-•→]\s*(.+?)(?=\n\s*[-•→]|\n\s*$|\n\s*\*\*|\n\s*###|\n\s*####|\n\s*##)',
        r'^\s*[-•→]\s*(.+?)(?=\n\s*[-•→]|\n\s*$)',
        r'^\s*[-•→]\s*(.+?)$'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            item_content = match.group(1).strip()
            if item_content and len(item_content) > 5:
                update = {
                    'date': month,
                    'content': item_content,
                    'title': extract_title(item_content),
                    'description': extract_description(item_content),
                    'type': categorize_update(item_content),
                    'created_at': parse_date(month)
                }
                updates.append(update)
    
    return updates

def extract_title(content: str) -> str:
    """업데이트 내용에서 제목을 추출합니다."""
    sentences = re.split(r'[.!?]', content)
    if sentences:
        title = sentences[0].strip()
        title = re.sub(r'[^\w\s가-힣]', '', title)
        return title[:50] + '...' if len(title) > 50 else title
    return '업데이트'

def extract_description(content: str) -> str:
    """업데이트 내용에서 설명을 추출합니다."""
    description = content.strip()
    description = re.sub(r'<[^>]+>', '', description)
    description = re.sub(r'[^\w\s가-힣.!?]', '', description)
    return description[:200] + '...' if len(description) > 200 else description

def categorize_update(content: str) -> str:
    """업데이트 내용을 카테고리로 분류합니다."""
    content_lower = content.lower()
    
    if any(keyword in content_lower for keyword in ['ui', 'ux', '디자인', '인터페이스', '화면']):
        return 'UI/UX'
    elif any(keyword in content_lower for keyword in ['api', '엔드포인트', '백엔드']):
        return 'API'
    elif any(keyword in content_lower for keyword in ['데이터', 'db', '데이터베이스']):
        return '데이터'
    elif any(keyword in content_lower for keyword in ['크롤링', '수집']):
        return '크롤링'
    elif any(keyword in content_lower for keyword in ['번역', 'translation']):
        return '번역'
    elif any(keyword in content_lower for keyword in ['ai', 'openai', 'gemini']):
        return 'AI'
    elif any(keyword in content_lower for keyword in ['성능', '최적화', '속도']):
        return '성능'
    elif any(keyword in content_lower for keyword in ['보안', '인증', '로그인']):
        return '보안'
    elif any(keyword in content_lower for keyword in ['통계', '분석']):
        return '통계'
    elif any(keyword in content_lower for keyword in ['오류', '버그', '수정']):
        return '버그수정'
    else:
        return '기타'

def parse_date(date_str: str) -> str:
    """날짜 문자열을 파싱합니다."""
    try:
        if re.match(r'\d{4}\.\d{2}', date_str):
            year, month = date_str.split('.')
            return f"{year}-{month}-01"
        return date_str
    except:
        return date_str 