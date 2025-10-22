#!/usr/bin/env python3
"""
JSON 크롤링 디버깅 스크립트
"""

import sys
import os
import requests
import json

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_json_crawling():
    """JSON 크롤링 디버깅"""
    print("🔍 JSON 크롤링 디버깅 시작...")
    
    url = "https://jsonplaceholder.typicode.com/posts/1"
    
    # 1. 기본 requests 테스트
    print(f"\n1. 기본 requests 테스트:")
    try:
        response = requests.get(url, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        print(f"   Text starts with: {repr(response.text[:50])}")
        
        # JSON 파싱 테스트
        try:
            json_data = response.json()
            print(f"   JSON 파싱 성공: {type(json_data)}")
            print(f"   JSON 키: {list(json_data.keys())}")
        except Exception as e:
            print(f"   JSON 파싱 실패: {e}")
            
    except Exception as e:
        print(f"   Requests 실패: {e}")
    
    # 2. 크롤러 세션 테스트
    print(f"\n2. 크롤러 세션 테스트:")
    try:
        from app.services.crawler import EnhancedCrawler
        crawler = EnhancedCrawler()
        
        response = crawler.session.get(url, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        print(f"   Text starts with: {repr(response.text[:50])}")
        
        # JSON 파싱 테스트
        try:
            json_data = response.json()
            print(f"   JSON 파싱 성공: {type(json_data)}")
            print(f"   JSON 키: {list(json_data.keys())}")
            
            # JSON을 텍스트로 변환 테스트
            content = crawler._json_to_text(json_data)
            print(f"   JSON to text 성공: {len(content)}자")
            print(f"   변환된 텍스트: {content[:100]}...")
            
        except Exception as e:
            print(f"   JSON 파싱 실패: {e}")
            
    except Exception as e:
        print(f"   크롤러 세션 실패: {e}")
    
    # 3. 전체 크롤링 프로세스 테스트
    print(f"\n3. 전체 크롤링 프로세스 테스트:")
    try:
        from app.services.crawler import crawl_url
        
        # 캐시 클리어
        from app.services.crawler import _get_crawling_cache_key, _set_cached_content
        cache_key = _get_crawling_cache_key(url)
        _set_cached_content(cache_key, None)  # 캐시 클리어
        
        result = crawl_url(url)
        print(f"   크롤링 결과: {len(result) if result else 0}자")
        if result:
            print(f"   결과 내용: {result[:100]}...")
        else:
            print(f"   크롤링 실패")
            
    except Exception as e:
        print(f"   전체 크롤링 실패: {e}")

if __name__ == "__main__":
    debug_json_crawling() 