#!/usr/bin/env python3
"""
번역 함수 테스트 도구
"""

import sys
import os
import asyncio

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.translator import translate_text, translate_text_gemini

async def test_translation():
    """번역 함수 테스트"""
    
    print("🔧 번역 함수 테스트")
    print("=" * 50)
    
    # 테스트 텍스트들
    test_texts = [
        "Hello, how are you today?",
        "The weather is beautiful today.",
        "I love learning new technologies.",
        "This is a test of the translation system.",
        "Artificial intelligence is amazing."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 테스트 {i}: {text}")
        
        try:
            # translate_text 함수 테스트
            print("  🔄 translate_text 함수 테스트 중...")
            result1 = await translate_text(text, "ko")
            print(f"  📝 결과: {result1}")
            
            # translate_text_gemini 함수 직접 테스트
            print("  🔄 translate_text_gemini 함수 직접 테스트 중...")
            result2 = await translate_text_gemini(text, "ko")
            print(f"  📝 결과: {result2}")
            
        except Exception as e:
            print(f"  ❌ 오류: {e}")
        
        await asyncio.sleep(1)

async def main():
    """메인 함수"""
    await test_translation()
    print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main()) 