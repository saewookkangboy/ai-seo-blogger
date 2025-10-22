#!/usr/bin/env python3
"""
향상된 기능 테스트 스크립트
- AI 추천 키워드 (명사 중심, 최대 10개)
- 주요 내용, 핵심 포인트, 실용적인 팁, 요약
- AI 요약 (100자 이내)
- 신뢰도 평가 (5점 만점)
- SEO 최적화 점수 (10점 만점)
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.content_generator import (
    create_enhanced_blog_post,
    _extract_ai_keywords,
    _extract_ai_analysis
)

async def test_enhanced_features():
    """향상된 기능 테스트"""
    print("🚀 향상된 기능 테스트 시작")
    print("=" * 50)
    
    # 테스트 텍스트
    test_text = """
    인공지능(AI)과 머신러닝(ML)은 현대 기술의 핵심 분야입니다. 
    AI는 인간의 지능을 모방하는 컴퓨터 시스템을 의미하며, 
    머신러닝은 AI의 하위 분야로 데이터로부터 패턴을 학습하는 기술입니다.
    
    딥러닝은 머신러닝의 한 분야로, 인공신경망을 사용하여 복잡한 패턴을 학습합니다.
    자연어 처리(NLP)는 컴퓨터가 인간의 언어를 이해하고 처리하는 기술입니다.
    
    이러한 기술들은 의료, 금융, 교육, 엔터테인먼트 등 다양한 분야에서 활용되고 있습니다.
    """
    
    test_keywords = "인공지능, 머신러닝, 딥러닝, 자연어처리"
    
    print(f"📝 테스트 텍스트: {len(test_text)}자")
    print(f"🔑 테스트 키워드: {test_keywords}")
    print()
    
    try:
        # 1. AI 키워드 추출 테스트
        print("1️⃣ AI 키워드 추출 테스트")
        ai_keywords = _extract_ai_keywords(test_text, test_keywords)
        print(f"   추출된 키워드: {ai_keywords}")
        print(f"   키워드 수: {len(ai_keywords)}개")
        print()
        
        # 2. 향상된 콘텐츠 생성 테스트
        print("2️⃣ 향상된 콘텐츠 생성 테스트")
        result = await create_enhanced_blog_post(
            text=test_text,
            keywords=test_keywords,
            content_length="2000",
            ai_mode="enhanced"
        )
        
        print(f"   제목: {result['title']}")
        print(f"   단어 수: {result['word_count']}")
        print(f"   AI 모드: {result['ai_mode']}")
        print()
        
        # 3. AI 분석 결과 확인
        print("3️⃣ AI 분석 결과 확인")
        ai_analysis = result.get('ai_analysis', {})
        
        print(f"   AI 요약: {ai_analysis.get('ai_summary', 'N/A')}")
        print(f"   신뢰도 평가: {ai_analysis.get('trust_score', 0)}/5")
        print(f"   SEO 최적화 점수: {ai_analysis.get('seo_score', 0)}/10")
        print(f"   신뢰도 근거: {ai_analysis.get('trust_reason', 'N/A')}")
        print(f"   SEO 최적화 근거: {ai_analysis.get('seo_reason', 'N/A')}")
        print()
        
        # 4. 생성된 콘텐츠 구조 확인
        print("4️⃣ 생성된 콘텐츠 구조 확인")
        content = result['post']
        
        # 주요 섹션 확인
        sections = [
            ('AI 추천 키워드', 'ai-keywords'),
            ('주요 내용', '📋 주요 내용'),
            ('핵심 포인트', '🔍 핵심 포인트'),
            ('실용적인 팁', '💡 실용적인 팁'),
            ('요약', '📊 요약'),
            ('AI 분석', '🤖 AI 분석')
        ]
        
        for section_name, section_marker in sections:
            if section_marker in content:
                print(f"   ✅ {section_name}: 포함됨")
            else:
                print(f"   ❌ {section_name}: 누락됨")
        
        print()
        
        # 5. 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_features_test_{timestamp}.json"
        
        test_result = {
            "test_timestamp": timestamp,
            "test_text": test_text,
            "test_keywords": test_keywords,
            "extracted_keywords": ai_keywords,
            "generated_content": result,
            "ai_analysis": ai_analysis
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 테스트 결과가 {filename}에 저장되었습니다.")
        print()
        
        # 6. 성공 메시지
        print("✅ 모든 테스트가 성공적으로 완료되었습니다!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        print(f"🔍 오류 상세: {type(e).__name__}: {str(e)}")
        return False

async def test_gemini_enhanced():
    """Gemini 2.0 Flash 향상된 기능 테스트"""
    print("🚀 Gemini 2.0 Flash 향상된 기능 테스트 시작")
    print("=" * 50)
    
    # 테스트 텍스트
    test_text = """
    블록체인 기술은 분산 원장 기술로, 중앙화된 기관 없이 
    안전하고 투명한 거래를 가능하게 합니다. 
    
    비트코인은 최초의 블록체인 기반 암호화폐로, 
    사토시 나카모토에 의해 2009년에 발명되었습니다.
    
    스마트 컨트랙트는 이더리움에서 도입된 기능으로, 
    자동으로 실행되는 계약을 의미합니다.
    """
    
    test_keywords = "블록체인, 비트코인, 스마트컨트랙트, 암호화폐"
    
    print(f"📝 테스트 텍스트: {len(test_text)}자")
    print(f"🔑 테스트 키워드: {test_keywords}")
    print()
    
    try:
        from app.services.content_generator import _create_enhanced_blog_post_with_gemini
        
        result = await _create_enhanced_blog_post_with_gemini(
            text=test_text,
            keywords=test_keywords,
            content_length="3000",
            ai_mode="gemini_2_0_flash"
        )
        
        print(f"   제목: {result['title']}")
        print(f"   단어 수: {result['word_count']}")
        print(f"   AI 모드: {result['ai_mode']}")
        print()
        
        # AI 분석 결과 확인
        ai_analysis = result.get('ai_analysis', {})
        print(f"   AI 요약: {ai_analysis.get('ai_summary', 'N/A')}")
        print(f"   신뢰도 평가: {ai_analysis.get('trust_score', 0)}/5")
        print(f"   SEO 최적화 점수: {ai_analysis.get('seo_score', 0)}/10")
        print()
        
        print("✅ Gemini 2.0 Flash 향상된 기능 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ Gemini 테스트 중 오류 발생: {e}")
        return False

async def main():
    """메인 테스트 함수"""
    print("🎯 AI SEO Blogger 향상된 기능 테스트")
    print("=" * 60)
    
    # 기본 향상된 기능 테스트
    success1 = await test_enhanced_features()
    
    print()
    
    # Gemini 2.0 Flash 테스트
    success2 = await test_gemini_enhanced()
    
    print()
    print("📊 테스트 결과 요약")
    print("=" * 30)
    print(f"기본 향상된 기능: {'✅ 성공' if success1 else '❌ 실패'}")
    print(f"Gemini 2.0 Flash: {'✅ 성공' if success2 else '❌ 실패'}")
    
    if success1 and success2:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("\n⚠️ 일부 테스트에서 문제가 발생했습니다.")

if __name__ == "__main__":
    asyncio.run(main()) 