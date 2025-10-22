import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class UpdateHistoryService:
    """README.md 기반 업데이트 이력 자동 관리 서비스"""
    
    def __init__(self):
        self.readme_path = Path(__file__).parent.parent.parent / "README.md"
        self.history_file = Path(__file__).parent.parent.parent / "update_history.json"
        
    def parse_readme_updates(self) -> List[Dict[str, Any]]:
        """README.md에서 업데이트 이력을 파싱하여 추출"""
        try:
            if not self.readme_path.exists():
                logger.warning("README.md 파일을 찾을 수 없습니다.")
                return []
            
            with open(self.readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            updates = []
            
            # 2025년 업데이트 이력 파싱
            updates.extend(self._parse_year_section(content, "2025"))
            
            # 2024년 업데이트 이력 파싱
            updates.extend(self._parse_year_section(content, "2024"))
            
            # 이전 업데이트 이력 파싱
            updates.extend(self._parse_previous_updates(content))
            
            # 날짜순 정렬 (최신순)
            updates.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            logger.info(f"총 {len(updates)}개의 업데이트 이력을 파싱했습니다.")
            return updates
            
        except Exception as e:
            logger.error(f"README.md 파싱 중 오류 발생: {e}")
            return []
    
    def _parse_year_section(self, content: str, year: str) -> List[Dict[str, Any]]:
        """특정 연도의 업데이트 이력 파싱"""
        updates = []
        
        # 연도 섹션 찾기 (더 유연한 패턴)
        year_patterns = [
            rf"## {year}년 주요 변경 이력",
            rf"## {year}년 업데이트",
            rf"## {year}년 변경사항",
            rf"## {year}년 주요 변경사항"
        ]
        
        year_match = None
        for pattern in year_patterns:
            year_match = re.search(pattern, content)
            if year_match:
                break
        
        if not year_match:
            return updates
        
        # 연도 섹션의 끝까지 추출
        start_pos = year_match.end()
        next_section = re.search(r"## \d{4}년", content[start_pos:])
        end_pos = start_pos + next_section.start() if next_section else len(content)
        
        year_content = content[start_pos:end_pos]
        
        # 월별 업데이트 파싱 (더 유연한 패턴)
        month_patterns = [
            r"- \*\*(20\d{2}\.\d{2})\*\*",
            r"### (20\d{2}\.\d{2})",
            r"#### (20\d{2}\.\d{2})",
            r"- (20\d{2}\.\d{2})"
        ]
        
        for pattern in month_patterns:
            month_matches = re.finditer(pattern, year_content)
            for match in month_matches:
                month = match.group(1)
                month_start = match.end()
                
                # 다음 월까지의 내용 추출
                next_month = None
                for next_pattern in month_patterns:
                    next_month = re.search(next_pattern, year_content[month_start:])
                    if next_month:
                        break
                
                month_end = month_start + next_month.start() if next_month else len(year_content)
                month_content = year_content[month_start:month_end]
                
                # 개별 업데이트 항목 파싱
                update_items = self._parse_update_items(month_content, month)
                updates.extend(update_items)
        
        # 특정 날짜 업데이트 파싱 (2025.07.30 등)
        specific_date_patterns = [
            r"- \*\*(20\d{2}\.\d{2}\.\d{2})\*\*",
            r"### (20\d{2}\.\d{2}\.\d{2})",
            r"#### (20\d{2}\.\d{2}\.\d{2})",
            r"- (20\d{2}\.\d{2}\.\d{2})"
        ]
        
        for pattern in specific_date_patterns:
            date_matches = re.finditer(pattern, year_content)
            for match in date_matches:
                date = match.group(1)
                date_start = match.end()
                
                # 다음 날짜까지의 내용 추출
                next_date = None
                for next_pattern in specific_date_patterns:
                    next_date = re.search(next_pattern, year_content[date_start:])
                    if next_date:
                        break
                
                date_end = date_start + next_date.start() if next_date else len(year_content)
                date_content = year_content[date_start:date_end]
                
                # 개별 업데이트 항목 파싱
                update_items = self._parse_update_items(date_content, date)
                updates.extend(update_items)
        
        return updates
    
    def _parse_previous_updates(self, content: str) -> List[Dict[str, Any]]:
        """이전 업데이트 이력 섹션 파싱"""
        updates = []
        
        # "이전 주요 업데이트 이력" 섹션 찾기
        section_pattern = r"## 이전 주요 업데이트 이력"
        section_match = re.search(section_pattern, content)
        
        if not section_match:
            return updates
        
        # 섹션 내용 추출
        start_pos = section_match.end()
        next_section = re.search(r"## ", content[start_pos:])
        end_pos = start_pos + next_section.start() if next_section else len(content)
        
        section_content = content[start_pos:end_pos]
        
        # 개별 업데이트 항목 파싱
        update_items = self._parse_update_items(section_content, "2024.01")
        updates.extend(update_items)
        
        return updates
    
    def _parse_update_items(self, content: str, month: str) -> List[Dict[str, Any]]:
        """개별 업데이트 항목을 파싱합니다."""
        updates = []
        
        # 다양한 업데이트 패턴 지원
        patterns = [
            r'^\s*[-•→]\s*(.+?)(?=\n\s*[-•→]|\n\s*$|\n\s*\*\*|\n\s*###|\n\s*####|\n\s*##)',  # 기본 리스트
            r'^\s*[-•→]\s*(.+?)(?=\n\s*[-•→]|\n\s*$)',  # 단순 리스트
            r'^\s*[-•→]\s*(.+?)$',  # 한 줄 항목
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                item_content = match.group(1).strip()
                if item_content and len(item_content) > 5:  # 의미있는 내용만 포함
                    update = {
                        'date': month,
                        'content': item_content,
                        'title': self._extract_title(item_content),
                        'description': self._extract_description(item_content),
                        'category': self._categorize_update(item_content),
                        'type': self._categorize_update(item_content),
                        'importance': self._extract_importance(item_content),
                        'created_at': self._parse_date(month)
                    }
                    updates.append(update)
        
        return updates

    def _extract_title(self, content: str) -> str:
        """업데이트 내용에서 제목을 추출합니다."""
        # 첫 번째 문장을 제목으로 사용
        sentences = re.split(r'[.!?]', content)
        if sentences:
            title = sentences[0].strip()
            # 특수 문자 제거 및 길이 제한
            title = re.sub(r'[^\w\s가-힣]', '', title)
            return title[:50] + '...' if len(title) > 50 else title
        return '업데이트'

    def _extract_description(self, content: str) -> str:
        """업데이트 내용에서 설명을 추출합니다."""
        # 전체 내용을 설명으로 사용 (제목 제외)
        description = content.strip()
        # HTML 태그 제거
        description = re.sub(r'<[^>]+>', '', description)
        # 특수 문자 정리
        description = re.sub(r'[^\w\s가-힣.!?]', '', description)
        return description[:200] + '...' if len(description) > 200 else description

    def _categorize_update(self, content: str) -> str:
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

    def _parse_date(self, date_str: str) -> str:
        """날짜 문자열을 파싱합니다."""
        try:
            # YYYY.MM 형식 파싱
            if re.match(r'\d{4}\.\d{2}', date_str):
                year, month = date_str.split('.')
                return f"{year}-{month}-01"
            # 기타 형식 처리
            return date_str
        except:
            return date_str
    
    def _extract_category(self, content: str) -> str:
        """업데이트 내용에서 카테고리 추출"""
        categories = {
            'UI/UX': ['UI', 'UX', '디자인', '인터페이스', '템플릿', '스타일', '폰트'],
            '기능': ['기능', '추가', '구현', '개발', '새로운'],
            'API': ['API', '엔드포인트', 'REST', '통합'],
            '데이터': ['데이터', '데이터베이스', 'DB', 'CRUD', '저장'],
            '성능': ['성능', '최적화', '속도', '응답시간'],
            '보안': ['보안', '인증', '로그인', '권한'],
            '크롤링': ['크롤링', '크롤러', '수집'],
            '번역': ['번역', 'Gemini', 'AI'],
            '통계': ['통계', '분석', '리포트', '대시보드'],
            '테스트': ['테스트', '검증', '오류', '버그'],
            '문서': ['문서', 'README', '가이드', '설명']
        }
        
        for category, keywords in categories.items():
            if any(keyword in content for keyword in keywords):
                return category
        
        return '기타'
    
    def _extract_importance(self, content: str) -> str:
        """업데이트 내용에서 중요도 추출"""
        if any(word in content for word in ['주요', '핵심', '중요', '대규모', '전면']):
            return '높음'
        elif any(word in content for word in ['개선', '수정', '업데이트', '변경']):
            return '보통'
        else:
            return '낮음'
    
    def save_history(self, updates: List[Dict]) -> bool:
        """업데이트 이력을 JSON 파일로 저장"""
        try:
            # 통계 생성
            stats = self.get_statistics(updates)
            
            history_data = {
                'last_updated': datetime.now().isoformat(),
                'total_count': len(updates),
                'updates': updates,
                'statistics': stats
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"업데이트 이력이 {self.history_file}에 저장되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"업데이트 이력 저장 중 오류 발생: {e}")
            return False
    
    def load_history(self) -> Dict:
        """저장된 업데이트 이력 로드"""
        try:
            if not self.history_file.exists():
                return {'updates': [], 'last_updated': None, 'total_count': 0}
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"업데이트 이력 로드 중 오류 발생: {e}")
            return {'updates': [], 'last_updated': None, 'total_count': 0}
    
    def get_statistics(self, updates: List[Dict]) -> Dict:
        """업데이트 이력 통계 생성"""
        stats = {
            'total_updates': len(updates),
            'by_year': {},
            'by_category': {},
            'by_importance': {},
            'recent_updates': []
        }
        
        for update in updates:
            year = update['date'][:4]
            category = update['category']
            importance = update['importance']
            
            # 연도별 통계
            stats['by_year'][year] = stats['by_year'].get(year, 0) + 1
            
            # 카테고리별 통계
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # 중요도별 통계
            stats['by_importance'][importance] = stats['by_importance'].get(importance, 0) + 1
        
        # 최근 업데이트 (최근 10개)
        stats['recent_updates'] = updates[:10]
        
        return stats
    
    def auto_update_history(self) -> Dict:
        """자동으로 업데이트 이력을 갱신"""
        try:
            # README.md에서 최신 업데이트 이력 파싱
            updates = self.parse_readme_updates()
            
            # 통계 생성
            stats = self.get_statistics(updates)
            
            # JSON 파일로 저장
            self.save_history(updates)
            
            return {
                'success': True,
                'total_updates': len(updates),
                'last_updated': datetime.now().isoformat(),
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"자동 업데이트 이력 갱신 중 오류 발생: {e}")
            return {
                'success': False,
                'error': str(e)
            } 