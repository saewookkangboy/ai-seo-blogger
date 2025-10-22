#!/usr/bin/env python3
"""
크롤링 디버깅 도구
특정 사이트의 HTML 구조를 분석하고 크롤링 문제를 진단합니다.
"""

import sys
import os
import requests
from bs4 import BeautifulSoup, Tag
from pathlib import Path
from typing import Optional, List, Any
from datetime import date
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database import SessionLocal
from app.crud import upsert_update

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def analyze_site_structure(url: str):
    """사이트의 HTML 구조를 분석합니다."""
    print(f"🔍 {url} 사이트 분석 시작...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"✅ 페이지 로드 성공 (크기: {len(response.text)} bytes)")
        
        # 1. 기본 정보
        print("\n📋 기본 정보:")
        print(f"   제목: {soup.title.string if soup.title else '없음'}")
        
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and isinstance(meta_desc, Tag) and meta_desc.get('content'):
            print(f"   메타 설명: {meta_desc['content']}")
        else:
            print("   메타 설명: 없음")
        
        # 2. 본문 관련 클래스/ID 검색
        print("\n🔍 본문 관련 요소 검색:")
        content_selectors = [
            'article', 'main', '[role="main"]',
            '.content', '.post-content', '.entry-content', '.article-content',
            '.main-content', '#content', '#main', '.post', '.entry', '.article'
        ]
        
        found_elements = []
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                found_elements.append((selector, len(elements)))
                print(f"   ✅ {selector}: {len(elements)}개 발견")
        
        if not found_elements:
            print("   ❌ 일반적인 본문 선택자에서 요소를 찾을 수 없습니다.")
        
        # 3. 모든 클래스 분석
        print("\n🏷️  페이지의 모든 클래스 분석:")
        all_classes = set()
        for tag in soup.find_all(class_=True):
            if isinstance(tag, Tag):
                class_attr = tag.get('class')
                if class_attr:
                    if isinstance(class_attr, list):
                        all_classes.update(class_attr)
                    else:
                        all_classes.add(str(class_attr))
        
        content_related_classes = []
        for class_name in sorted(all_classes):
            if any(keyword in class_name.lower() for keyword in ['content', 'post', 'entry', 'article', 'main', 'body']):
                content_related_classes.append(class_name)
                print(f"   📝 {class_name}")
        
        # 4. 텍스트 블록 분석
        print("\n📄 텍스트 블록 분석:")
        text_blocks = []
        for tag in soup.find_all(['p', 'div', 'article', 'section']):
            if isinstance(tag, Tag):
                text = tag.get_text(strip=True)
                if len(text) > 100:  # 의미있는 텍스트 블록
                    text_blocks.append((tag.name, len(text), text[:100] + "..."))
        
        text_blocks.sort(key=lambda x: x[1], reverse=True)
        for i, (tag_name, length, preview) in enumerate(text_blocks[:5]):
            print(f"   {i+1}. <{tag_name}> ({length}자): {preview}")
        
        # 5. 추천 선택자 생성
        print("\n💡 추천 선택자:")
        if content_related_classes:
            print("   사이트별 커스텀 선택자:")
            for class_name in content_related_classes[:5]:
                print(f"     '.{class_name}'")
        
        # 6. 실제 크롤링 테스트
        print("\n🧪 실제 크롤링 테스트:")
        test_selectors = content_related_classes[:3] + ['article', 'main', '.content']
        
        for selector in test_selectors:
            try:
                if selector.startswith('.'):
                    elements = soup.select(selector)
                else:
                    elements = soup.find_all(selector)
                
                if elements:
                    total_text = ""
                    for element in elements:
                        if isinstance(element, Tag):
                            total_text += element.get_text(strip=True) + " "
                    
                    if len(total_text.strip()) > 500:
                        print(f"   ✅ {selector}: {len(total_text)}자 텍스트 추출 성공")
                        print(f"      미리보기: {total_text[:200]}...")
                        break
                    else:
                        print(f"   ⚠️  {selector}: 텍스트가 너무 짧음 ({len(total_text)}자)")
                else:
                    print(f"   ❌ {selector}: 요소를 찾을 수 없음")
            except Exception as e:
                print(f"   ❌ {selector}: 오류 발생 - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        return False

def generate_custom_crawler(url: str):
    """사이트별 커스텀 크롤러 코드를 생성합니다."""
    print(f"\n🔧 {url} 사이트용 커스텀 크롤러 생성...")
    
    domain = url.split('/')[2]
    
    custom_code = f'''
# {domain} 사이트용 커스텀 크롤러
def crawl_{domain.replace('.', '_').replace('-', '_')}(soup):
    """{domain} 사이트 전용 크롤링 함수"""
    main_content = None
    
    # 사이트별 특화 선택자들
    selectors = [
        # 여기에 분석 결과를 바탕으로 한 선택자들을 추가하세요
    ]
    
    for selector in selectors:
        main_content = soup.select_one(selector)
        if main_content:
            logger.info(f"{domain} 사이트 본문을 찾았습니다: {{selector}}")
            break
    
    if not main_content:
        # 폴백: 일반적인 선택자들
        fallback_selectors = ['article', 'main', '.content', '.post-content']
        for selector in fallback_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
    
    if not main_content:
        main_content = soup.body
    
    return main_content
'''
    
    print("생성된 코드:")
    print(custom_code)
    
    # 파일로 저장
    output_file = f"custom_crawlers/{domain.replace('.', '_').replace('-', '_')}.py"
    os.makedirs("custom_crawlers", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(custom_code)
    
    print(f"\n💾 커스텀 크롤러가 {output_file}에 저장되었습니다.")

def main_debug():
    if len(sys.argv) < 2:
        print("사용법: python tools/crawler_debug.py <URL>")
        print("예시: python tools/crawler_debug.py https://example.com/article")
        return
    
    url = sys.argv[1]
    
    print("=" * 60)
    print("🔧 크롤링 디버깅 도구")
    print("=" * 60)
    
    if analyze_site_structure(url):
        generate_custom_crawler(url)
        print("\n✅ 분석 완료! 위의 결과를 바탕으로 크롤러를 개선하세요.")
    else:
        print("\n❌ 분석 실패. URL을 확인하고 다시 시도하세요.")

def merge_feature_updates():
    db = SessionLocal()
    # (1) 날짜 이동
    move_map = {
        "2024-06-01": "2025-06-24",
        "2024-05-01": "2025-06-23",
        "2024-04-01": "2025-06-22",
    }
    # (2) 병합 대상(2024-03-01 이하)
    merge_target_dates = [
        "2024-03-01", "2024-02-01", "2024-01-01", "2023-12-01"
    ]
    # (2-1) 병합 내용 수집
    from app.models import FeatureUpdate
    merged_content = ""
    for d in merge_target_dates:
        d_obj = date.fromisoformat(d)
        obj = db.query(FeatureUpdate).filter(FeatureUpdate.date == d_obj).first()
        if obj:
            merged_content += f"[{d}]\n" + obj.content + "\n\n"
    # (2-2) 병합 등록 (2025-06-22)
    if merged_content:
        upsert_update(db, date.fromisoformat("2025-06-22"), merged_content.strip())
    # (1-2) 날짜 이동(upsert)
    for old, new in move_map.items():
        obj = db.query(FeatureUpdate).filter(FeatureUpdate.date == date.fromisoformat(old)).first()
        if obj:
            upsert_update(db, date.fromisoformat(new), obj.content)
    db.commit()
    db.close()
    print("날짜 이동 및 병합 완료!")

if __name__ == "__main__":
    merge_feature_updates() 