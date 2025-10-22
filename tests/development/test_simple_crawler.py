#!/usr/bin/env python3
"""
간단한 크롤러 테스트
"""

import requests
from bs4 import BeautifulSoup
import re

def test_simple_crawler():
    """간단한 크롤러 테스트"""
    print("🔍 간단한 크롤러 테스트 시작...")
    
    test_url = "https://www.example.com/"
    
    try:
        print(f"📄 테스트 URL: {test_url}")
        
        # 직접 requests로 테스트
        response = requests.get(test_url, timeout=10)
        response.raise_for_status()
        
        print(f"✅ HTTP 요청 성공: {response.status_code}")
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 제목 추출
        title = soup.find('title')
        if title:
            print(f"📝 제목: {title.get_text()}")
        
        # 본문 추출 시도
        content_selectors = [
            'body',
            'div',
            'p',
            'article',
            'main'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                # 가장 큰 텍스트 블록 찾기
                best_content = None
                max_length = 0
                
                for element in elements:
                    text = element.get_text(strip=True)
                    if len(text) > max_length:
                        max_length = len(text)
                        best_content = text
                
                if best_content and len(best_content) > 50:
                    print(f"✅ {selector} 선택자로 콘텐츠 추출 성공: {len(best_content)}자")
                    print(f"📝 내용 미리보기: {best_content[:200]}...")
                    return True
        
        print("❌ 모든 선택자로 콘텐츠 추출 실패")
        return False
        
    except Exception as e:
        print(f"❌ 크롤러 테스트 오류: {e}")
        return False

if __name__ == "__main__":
    test_simple_crawler() 