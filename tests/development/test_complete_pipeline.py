#!/usr/bin/env python3
"""
전체 파이프라인 테스트 스크립트
크롤링 → 번역 → 키워드 추출 → 콘텐츠 생성까지 전체 프로세스를 테스트합니다.
"""

import asyncio
import sys
import os
import json
import requests
from datetime import datetime
import time

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

class CompletePipelineTest:
    """전체 파이프라인 테스트 클래스"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {}
        }
    
    def test_system_status(self):
        """시스템 상태 테스트"""
        print("🔍 시스템 상태 확인 중...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 시스템 상태: {data.get('status', '알 수 없음')}")
                print(f"   - 버전: {data.get('version', 'N/A')}")
                print(f"   - 타임스탬프: {data.get('timestamp', 'N/A')}")
                return True
            else:
                print(f"❌ 시스템 상태 확인 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 시스템 상태 확인 오류: {e}")
            return False
    
    def test_complete_pipeline_openai(self):
        """OpenAI를 사용한 전체 파이프라인 테스트"""
        print("\n🤖 OpenAI 전체 파이프라인 테스트...")
        
        test_data = {
            "text": """
            Artificial Intelligence (AI) is revolutionizing the way we live and work. 
            From virtual assistants to autonomous vehicles, AI technologies are becoming 
            increasingly integrated into our daily lives. Machine learning algorithms 
            can now process vast amounts of data to identify patterns and make predictions 
            with remarkable accuracy.
            
            The impact of AI on various industries is profound. In healthcare, AI is 
            helping doctors diagnose diseases more accurately and develop personalized 
            treatment plans. In finance, AI algorithms are detecting fraudulent transactions 
            and optimizing investment strategies. In education, AI-powered platforms are 
            providing personalized learning experiences for students.
            
            However, the rapid advancement of AI also raises important questions about 
            privacy, security, and the future of work. As AI systems become more capable, 
            we must ensure they are developed and deployed responsibly, with proper 
            safeguards to protect human rights and promote social good.
            """,
            "ai_mode": "informative",
            "content_length": "3000",
            "rules": ["AI_SEO", "AI_SEARCH"]
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/generate-post",
                json=test_data,
                timeout=120
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ OpenAI 파이프라인 테스트 성공 ({duration:.2f}초)")
                print(f"   - 제목: {data.get('data', {}).get('title', 'N/A')[:50]}...")
                print(f"   - 콘텐츠 길이: {len(data.get('data', {}).get('content', ''))}자")
                print(f"   - 키워드: {data.get('data', {}).get('keywords', 'N/A')}")
                print(f"   - AI 모드: {data.get('data', {}).get('ai_mode', 'N/A')}")
                
                result = {
                    "test": "complete_pipeline_openai",
                    "status": "success",
                    "duration": round(duration, 2),
                    "content_length": len(data.get('data', {}).get('content', '')),
                    "keywords": data.get('data', {}).get('keywords', ''),
                    "ai_mode": data.get('data', {}).get('ai_mode', '')
                }
            else:
                print(f"❌ OpenAI 파이프라인 테스트 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                result = {
                    "test": "complete_pipeline_openai",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": round(duration, 2)
                }
            
            self.test_results["tests"].append(result)
            return result["status"] == "success"
            
        except Exception as e:
            print(f"❌ OpenAI 파이프라인 테스트 오류: {e}")
            result = {
                "test": "complete_pipeline_openai",
                "status": "error",
                "error": str(e),
                "duration": 0
            }
            self.test_results["tests"].append(result)
            return False
    
    def test_complete_pipeline_gemini(self):
        """Gemini를 사용한 전체 파이프라인 테스트"""
        print("\n🚀 Gemini 전체 파이프라인 테스트...")
        
        test_data = {
            "text": """
            Artificial Intelligence (AI) is transforming the way we live and work. 
            From virtual assistants to autonomous vehicles, AI technologies are becoming 
            increasingly integrated into our daily lives. Machine learning algorithms 
            can now process vast amounts of data to identify patterns and make predictions 
            with remarkable accuracy.
            
            The impact of AI on various industries is profound. In healthcare, AI is 
            helping doctors diagnose diseases more accurately and develop personalized 
            treatment plans. In finance, AI algorithms are detecting fraudulent transactions 
            and optimizing investment strategies. In education, AI-powered platforms are 
            providing personalized learning experiences for students.
            
            However, the rapid advancement of AI also raises important questions about 
            privacy, security, and the future of work. As AI systems become more capable, 
            we must ensure they are developed and deployed responsibly, with proper 
            safeguards to protect human rights and promote social good.
            """,
            "ai_mode": "gemini",
            "content_length": "3000",
            "rules": ["AI_SEO", "AI_SEARCH"]
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/generate-post-gemini",
                json=test_data,
                timeout=120
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Gemini 파이프라인 테스트 성공 ({duration:.2f}초)")
                print(f"   - 제목: {data.get('data', {}).get('title', 'N/A')[:50]}...")
                print(f"   - 콘텐츠 길이: {len(data.get('data', {}).get('content', ''))}자")
                print(f"   - 키워드: {data.get('data', {}).get('keywords', 'N/A')}")
                print(f"   - AI 모드: {data.get('data', {}).get('ai_mode', 'N/A')}")
                
                result = {
                    "test": "complete_pipeline_gemini",
                    "status": "success",
                    "duration": round(duration, 2),
                    "content_length": len(data.get('data', {}).get('content', '')),
                    "keywords": data.get('data', {}).get('keywords', ''),
                    "ai_mode": data.get('data', {}).get('ai_mode', '')
                }
            else:
                print(f"❌ Gemini 파이프라인 테스트 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                result = {
                    "test": "complete_pipeline_gemini",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": round(duration, 2)
                }
            
            self.test_results["tests"].append(result)
            return result["status"] == "success"
            
        except Exception as e:
            print(f"❌ Gemini 파이프라인 테스트 오류: {e}")
            result = {
                "test": "complete_pipeline_gemini",
                "status": "error",
                "error": str(e),
                "duration": 0
            }
            self.test_results["tests"].append(result)
            return False
    
    def test_complete_pipeline_gemini_2_flash(self):
        """Gemini 2.0 Flash를 사용한 전체 파이프라인 테스트"""
        print("\n⚡ Gemini 2.0 Flash 전체 파이프라인 테스트...")
        
        test_data = {
            "text": """
            Artificial Intelligence (AI) is revolutionizing the way we live and work. 
            From virtual assistants to autonomous vehicles, AI technologies are becoming 
            increasingly integrated into our daily lives. Machine learning algorithms 
            can now process vast amounts of data to identify patterns and make predictions 
            with remarkable accuracy.
            
            The impact of AI on various industries is profound. In healthcare, AI is 
            helping doctors diagnose diseases more accurately and develop personalized 
            treatment plans. In finance, AI algorithms are detecting fraudulent transactions 
            and optimizing investment strategies. In education, AI-powered platforms are 
            providing personalized learning experiences for students.
            
            However, the rapid advancement of AI also raises important questions about 
            privacy, security, and the future of work. As AI systems become more capable, 
            we must ensure they are developed and deployed responsibly, with proper 
            safeguards to protect human rights and promote social good.
            """,
            "ai_mode": "gemini_2_0_flash",
            "content_length": "5000",
            "rules": ["AI_SEO", "AI_SEARCH"]
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                json=test_data,
                timeout=120
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Gemini 2.0 Flash 파이프라인 테스트 성공 ({duration:.2f}초)")
                print(f"   - 제목: {data.get('data', {}).get('title', 'N/A')[:50]}...")
                print(f"   - 콘텐츠 길이: {len(data.get('data', {}).get('content', ''))}자")
                print(f"   - 키워드: {data.get('data', {}).get('keywords', 'N/A')}")
                print(f"   - AI 모드: {data.get('data', {}).get('ai_mode', 'N/A')}")
                
                result = {
                    "test": "complete_pipeline_gemini_2_flash",
                    "status": "success",
                    "duration": round(duration, 2),
                    "content_length": len(data.get('data', {}).get('content', '')),
                    "keywords": data.get('data', {}).get('keywords', ''),
                    "ai_mode": data.get('data', {}).get('ai_mode', '')
                }
            else:
                print(f"❌ Gemini 2.0 Flash 파이프라인 테스트 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                result = {
                    "test": "complete_pipeline_gemini_2_flash",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": round(duration, 2)
                }
            
            self.test_results["tests"].append(result)
            return result["status"] == "success"
            
        except Exception as e:
            print(f"❌ Gemini 2.0 Flash 파이프라인 테스트 오류: {e}")
            result = {
                "test": "complete_pipeline_gemini_2_flash",
                "status": "error",
                "error": str(e),
                "duration": 0
            }
            self.test_results["tests"].append(result)
            return False
    
    def test_url_crawling_pipeline(self):
        """URL 크롤링 기반 전체 파이프라인 테스트"""
        print("\n🌐 URL 크롤링 기반 파이프라인 테스트...")
        
        # 실제 작동하는 URL들로 변경
        test_urls = [
            "https://www.example.com/",
            "https://httpbin.org/html",
            "https://jsonplaceholder.typicode.com/posts/1"
        ]
        
        for test_url in test_urls:
            print(f"   시도 중: {test_url}")
            test_data = {
                "url": test_url,
                "ai_mode": "gemini_2_0_flash",
                "content_length": "4000",
                "rules": ["AI_SEO", "AI_SEARCH"]
            }
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                    json=test_data,
                    timeout=180  # URL 크롤링은 더 오래 걸릴 수 있음
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ URL 크롤링 파이프라인 테스트 성공 ({duration:.2f}초)")
                    print(f"   - 성공한 URL: {test_url}")
                    print(f"   - 제목: {data.get('data', {}).get('title', 'N/A')[:50]}...")
                    print(f"   - 콘텐츠 길이: {len(data.get('data', {}).get('content', ''))}자")
                    print(f"   - 키워드: {data.get('data', {}).get('keywords', 'N/A')}")
                    print(f"   - 소스 URL: {data.get('data', {}).get('source_url', 'N/A')}")
                    
                    result = {
                        "test": "url_crawling_pipeline",
                        "status": "success",
                        "duration": round(duration, 2),
                        "content_length": len(data.get('data', {}).get('content', '')),
                        "keywords": data.get('data', {}).get('keywords', ''),
                        "source_url": data.get('data', {}).get('source_url', ''),
                        "successful_url": test_url
                    }
                    self.test_results["tests"].append(result)
                    return True
                else:
                    print(f"   ❌ URL 실패: {response.status_code} - {response.text[:100]}...")
                    continue
                    
            except Exception as e:
                print(f"   ❌ URL 오류: {e}")
                continue
        
        # 모든 URL이 실패한 경우
        print(f"❌ 모든 URL 크롤링 시도 실패")
        result = {
            "test": "url_crawling_pipeline",
            "status": "failed",
            "error": "모든 테스트 URL에서 크롤링 실패",
            "duration": 0,
            "attempted_urls": test_urls
        }
        self.test_results["tests"].append(result)
        return False
    
    def save_results(self, filename: str = None):
        """테스트 결과를 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"complete_pipeline_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"❌ 결과 저장 실패: {e}")
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "="*60)
        print("전체 파이프라인 테스트 결과")
        print("="*60)
        
        total_tests = len(self.test_results["tests"])
        successful_tests = sum(1 for test in self.test_results["tests"] if test.get("status") == "success")
        failed_tests = total_tests - successful_tests
        
        print(f"총 테스트 수: {total_tests}")
        print(f"성공: {successful_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        if self.test_results["tests"]:
            print("\n상세 결과:")
            for i, test in enumerate(self.test_results["tests"], 1):
                print(f"{i}. {test.get('test', 'unknown')}: {test.get('status', 'unknown')}")
                if test.get('duration'):
                    print(f"   소요시간: {test['duration']}초")
                if test.get('content_length'):
                    print(f"   콘텐츠 길이: {test['content_length']}자")
                if test.get('error'):
                    print(f"   오류: {test['error']}")
        
        # 성능 비교
        successful_tests = [test for test in self.test_results["tests"] if test.get("status") == "success"]
        if len(successful_tests) > 1:
            print("\n성능 비교:")
            for test in successful_tests:
                test_name = test.get('test', 'unknown')
                duration = test.get('duration', 0)
                content_length = test.get('content_length', 0)
                print(f"   {test_name}: {duration:.2f}초 ({content_length}자)")

def main():
    """메인 테스트 함수"""
    print("전체 파이프라인 테스트를 시작합니다...")
    print("크롤링 → 번역 → 키워드 추출 → 콘텐츠 생성")
    
    # API 키 확인 - Gemini API 숨김 처리됨
    # if not settings.get_gemini_api_key():
    #     print("❌ Gemini API 키가 설정되지 않았습니다.")
    #     print("환경변수 GEMINI_API_KEY를 설정해주세요.")
    #     return
    
    if not settings.get_openai_api_key():
        print("❌ OpenAI API 키가 설정되지 않았습니다.")
        print("환경변수 OPENAI_API_KEY를 설정해주세요.")
        return
    
    print("✅ OpenAI API 키가 설정되었습니다. (Gemini API는 숨김 처리됨)")
    
    # 테스트 인스턴스 생성
    tester = CompletePipelineTest()
    
    # 1. 시스템 상태 확인
    if not tester.test_system_status():
        print("❌ 시스템이 실행되지 않고 있습니다. 먼저 서버를 시작해주세요.")
        return
    
    # 2. OpenAI 파이프라인 테스트
    tester.test_complete_pipeline_openai()
    
    # 3. Gemini 파이프라인 테스트
    tester.test_complete_pipeline_gemini()
    
    # 4. Gemini 2.0 Flash 파이프라인 테스트
    tester.test_complete_pipeline_gemini_2_flash()
    
    # 5. URL 크롤링 기반 파이프라인 테스트
    tester.test_url_crawling_pipeline()
    
    # 결과 저장 및 출력
    tester.save_results()
    tester.print_summary()
    
    print("\n✅ 전체 파이프라인 테스트가 완료되었습니다!")

if __name__ == "__main__":
    main() 