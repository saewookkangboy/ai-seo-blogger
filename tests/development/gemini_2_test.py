#!/usr/bin/env python3
"""
Gemini-2.0-flash 모델 테스트 도구
새로운 Gemini-2.0-flash 모델의 성능을 테스트합니다.
"""

import sys
import os
import time
import json
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, List

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.translator import translate_text, detect_language, translate_text_gemini
from app.config import settings

class Gemini2Tester:
    """Gemini-2.0-flash 테스터"""
    
    def __init__(self):
        self.api_key = settings.get_gemini_api_key()
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        # 테스트 텍스트들
        self.test_texts = [
            "Artificial Intelligence is transforming the way we live and work.",
            "The future of renewable energy looks promising as solar and wind power technologies continue to advance.",
            "Digital transformation is reshaping industries across the globe.",
            "Machine learning algorithms are becoming more sophisticated and accurate.",
            "Cloud computing has revolutionized how businesses store and process data."
        ]
        
        # 번역 테스트 텍스트들
        self.translation_texts = [
            "Hello, how are you today?",
            "The weather is beautiful today.",
            "I love learning new technologies.",
            "This is a test of the translation system.",
            "Artificial intelligence is amazing."
        ]
    
    async def test_basic_generation(self):
        """기본 생성 테스트"""
        print("🔧 기본 생성 테스트 시작...")
        print("=" * 60)
        
        if not self.api_key:
            print("❌ Gemini API 키가 설정되지 않았습니다.")
            return
        
        url = f"{self.base_url}?key={self.api_key}"
        
        for i, text in enumerate(self.test_texts, 1):
            print(f"\n📝 테스트 {i}: {text}")
            
            try:
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": f"Explain this in a few words: {text}"
                                }
                            ]
                        }
                    ]
                }
                
                start_time = time.time()
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=payload)
                    response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if 'candidates' in data and len(data['candidates']) > 0:
                        result = data['candidates'][0]['content']['parts'][0]['text']
                        print(f"    ✅ 성공 ({response_time:.2f}초)")
                        print(f"    📝 결과: {result}")
                    else:
                        print(f"    ❌ 응답에 결과가 없음")
                        print(f"    📝 응답: {data}")
                else:
                    print(f"    ❌ API 오류: {response.status_code}")
                    print(f"    📝 응답: {response.text}")
                
            except Exception as e:
                print(f"    ❌ 오류: {e}")
            
            await asyncio.sleep(1)  # API 호출 간격
    
    async def test_translation(self):
        """번역 테스트"""
        print("\n🌐 번역 테스트 시작...")
        print("=" * 60)
        
        for i, text in enumerate(self.translation_texts, 1):
            print(f"\n📝 번역 테스트 {i}: {text}")
            
            try:
                start_time = time.time()
                translated = await translate_text(text, "ko")
                response_time = time.time() - start_time
                
                if translated and translated != text:
                    print(f"    ✅ 번역 성공 ({response_time:.2f}초)")
                    print(f"    📝 원문: {text}")
                    print(f"    📝 번역: {translated}")
                else:
                    print(f"    ⚠️ 번역 실패 또는 원문과 동일")
                    print(f"    📝 결과: {translated}")
                
            except Exception as e:
                print(f"    ❌ 번역 오류: {e}")
            
            await asyncio.sleep(1)
    
    async def test_language_detection(self):
        """언어 감지 테스트"""
        print("\n🔍 언어 감지 테스트 시작...")
        print("=" * 60)
        
        test_languages = [
            ("Hello, how are you?", "en"),
            ("안녕하세요, 어떻게 지내세요?", "ko"),
            ("Bonjour, comment allez-vous?", "fr"),
            ("Hola, ¿cómo estás?", "es"),
            ("こんにちは、お元気ですか？", "ja")
        ]
        
        for i, (text, expected) in enumerate(test_languages, 1):
            print(f"\n📝 언어 감지 테스트 {i}: {text}")
            
            try:
                start_time = time.time()
                detected = await detect_language(text)
                response_time = time.time() - start_time
                
                print(f"    ✅ 감지 완료 ({response_time:.2f}초)")
                print(f"    📝 예상: {expected}")
                print(f"    📝 감지: {detected}")
                
                if detected == expected:
                    print(f"    ✅ 정확한 감지")
                else:
                    print(f"    ⚠️ 감지 오류")
                
            except Exception as e:
                print(f"    ❌ 언어 감지 오류: {e}")
            
            await asyncio.sleep(1)
    
    async def test_long_text_translation(self):
        """긴 텍스트 번역 테스트"""
        print("\n📄 긴 텍스트 번역 테스트 시작...")
        print("=" * 60)
        
        long_text = """
        Artificial Intelligence (AI) has emerged as one of the most transformative technologies of the 21st century. 
        From autonomous vehicles to smart home devices, AI is becoming an integral part of our daily lives. 
        Machine learning algorithms are becoming more sophisticated and accurate, enabling computers to learn from data 
        and make predictions or decisions without being explicitly programmed for specific tasks.
        
        The applications of AI are vast and diverse. In healthcare, AI is being used to diagnose diseases, 
        predict patient outcomes, and develop personalized treatment plans. In finance, AI algorithms are 
        used for fraud detection, risk assessment, and automated trading. In education, AI-powered systems 
        can provide personalized learning experiences and adaptive tutoring.
        
        However, the rapid advancement of AI also raises important questions about ethics, privacy, and 
        the future of work. As AI systems become more capable, we need to ensure they are developed and 
        deployed responsibly, with proper safeguards to protect human rights and dignity.
        """
        
        print(f"📝 긴 텍스트 길이: {len(long_text)}자")
        
        try:
            start_time = time.time()
            translated = await translate_text(long_text, "ko")
            response_time = time.time() - start_time
            
            if translated and len(translated) > 100:
                print(f"    ✅ 긴 텍스트 번역 성공 ({response_time:.2f}초)")
                print(f"    📝 번역된 길이: {len(translated)}자")
                print(f"    📝 번역 미리보기: {translated[:200]}...")
            else:
                print(f"    ⚠️ 긴 텍스트 번역 실패 또는 결과가 너무 짧음")
                print(f"    📝 결과: {translated}")
            
        except Exception as e:
            print(f"    ❌ 긴 텍스트 번역 오류: {e}")
    
    async def test_performance_comparison(self):
        """성능 비교 테스트"""
        print("\n⚡ 성능 비교 테스트 시작...")
        print("=" * 60)
        
        test_text = "This is a performance test of the Gemini-2.0-flash model."
        
        # 여러 번 반복하여 평균 성능 측정
        times = []
        success_count = 0
        
        for i in range(5):
            try:
                start_time = time.time()
                translated = await translate_text(test_text, "ko")
                response_time = time.time() - start_time
                
                if translated and translated != test_text:
                    times.append(response_time)
                    success_count += 1
                    print(f"    📊 시도 {i+1}: {response_time:.2f}초")
                else:
                    print(f"    📊 시도 {i+1}: 실패")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"    📊 시도 {i+1}: 오류 - {e}")
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"\n📈 성능 통계:")
            print(f"    📊 성공률: {success_count}/5 ({success_count/5*100:.1f}%)")
            print(f"    📊 평균 응답 시간: {avg_time:.2f}초")
            print(f"    📊 최소 응답 시간: {min_time:.2f}초")
            print(f"    📊 최대 응답 시간: {max_time:.2f}초")
        else:
            print(f"\n❌ 성능 측정 실패")
    
    async def test_error_handling(self):
        """에러 처리 테스트"""
        print("\n⚠️ 에러 처리 테스트 시작...")
        print("=" * 60)
        
        # 1. 빈 텍스트 테스트
        print("\n1️⃣ 빈 텍스트 테스트")
        try:
            result = await translate_text("", "ko")
            print(f"    📝 결과: '{result}'")
            if result == "":
                print(f"    ✅ 올바른 처리")
            else:
                print(f"    ⚠️ 예상과 다른 처리")
        except Exception as e:
            print(f"    ❌ 오류: {e}")
        
        # 2. 매우 긴 텍스트 테스트
        print("\n2️⃣ 매우 긴 텍스트 테스트")
        very_long_text = "This is a test. " * 1000  # 약 18,000자
        try:
            result = await translate_text(very_long_text, "ko")
            print(f"    📝 결과 길이: {len(result)}자")
            if len(result) > 100:
                print(f"    ✅ 긴 텍스트 처리 성공")
            else:
                print(f"    ⚠️ 긴 텍스트 처리 실패")
        except Exception as e:
            print(f"    ❌ 오류: {e}")
        
        # 3. 특수 문자 테스트
        print("\n3️⃣ 특수 문자 테스트")
        special_text = "Hello! @#$%^&*()_+{}|:<>?[]\\;'\",./"
        try:
            result = await translate_text(special_text, "ko")
            print(f"    📝 결과: {result}")
            if result and result != special_text:
                print(f"    ✅ 특수 문자 처리 성공")
            else:
                print(f"    ⚠️ 특수 문자 처리 실패")
        except Exception as e:
            print(f"    ❌ 오류: {e}")
    
    def save_test_results(self, results: Dict[str, Any]):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gemini_2_test_results_{timestamp}.json"
        
        output = {
            "test_timestamp": datetime.now().isoformat(),
            "model": "gemini-2.0-flash",
            "results": results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🔧 Gemini-2.0-flash 모델 테스트 도구")
        print("새로운 Gemini-2.0-flash 모델의 성능을 테스트합니다.")
        print("=" * 60)
        
        results = {
            "basic_generation": {},
            "translation": {},
            "language_detection": {},
            "long_text_translation": {},
            "performance": {},
            "error_handling": {}
        }
        
        try:
            # 1. 기본 생성 테스트
            await self.test_basic_generation()
            
            # 2. 번역 테스트
            await self.test_translation()
            
            # 3. 언어 감지 테스트
            await self.test_language_detection()
            
            # 4. 긴 텍스트 번역 테스트
            await self.test_long_text_translation()
            
            # 5. 성능 비교 테스트
            await self.test_performance_comparison()
            
            # 6. 에러 처리 테스트
            await self.test_error_handling()
            
            print("\n✅ 모든 테스트가 완료되었습니다!")
            
            # 결과 저장
            self.save_test_results(results)
            
        except KeyboardInterrupt:
            print("\n⏹️ 테스트가 중단되었습니다.")
        except Exception as e:
            print(f"\n❌ 테스트 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()

def main():
    """메인 함수"""
    tester = Gemini2Tester()
    asyncio.run(tester.run_all_tests())

if __name__ == "__main__":
    main() 