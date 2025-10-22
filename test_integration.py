#!/usr/bin/env python3
"""
AI SEO Blogger - 콘텐츠 생성 기능 통합 테스트
크롤링, 번역, 키워드 추출, 콘텐츠 생성까지 전체 플로우를 테스트합니다.
"""

import requests
import json
import time
import sys
from datetime import datetime

# 서버 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def print_step(step, message):
    """테스트 단계를 출력합니다."""
    print(f"\n{'='*50}")
    print(f"단계 {step}: {message}")
    print(f"{'='*50}")

def test_health_check():
    """1단계: 서버 헬스체크"""
    print_step(1, "서버 헬스체크")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 서버 상태: {data['status']}")
            print(f"✅ 서버 버전: {data['version']}")
            print(f"✅ 응답 시간: {data['timestamp']}")
            return True
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return False

def test_text_generation():
    """2단계: 텍스트 입력으로 콘텐츠 생성"""
    print_step(2, "텍스트 입력으로 콘텐츠 생성")
    
    test_data = {
        "text": "Artificial Intelligence is transforming the way we work and live. Machine learning algorithms are becoming more sophisticated and are being applied to various industries including healthcare, finance, and education.",
        "keywords": "AI, machine learning, technology, innovation",
        "content_length": "2000",
        "ai_mode": "informative"
    }
    
    try:
        print("📝 테스트 데이터:")
        print(f"   텍스트 길이: {len(test_data['text'])}자")
        print(f"   키워드: {test_data['keywords']}")
        print(f"   콘텐츠 길이: {test_data['content_length']}자")
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/generate-post",
            json=test_data,
            timeout=60
        )
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 콘텐츠 생성 성공! (소요시간: {end_time - start_time:.2f}초)")
            print(f"✅ 제목: {result['title']}")
            print(f"✅ 키워드: {result['keywords']}")
            print(f"✅ 단어 수: {result['word_count']}")
            print(f"✅ 메타 설명: {result['meta_description'][:100]}...")
            return True
        else:
            print(f"❌ 콘텐츠 생성 실패: {response.status_code}")
            print(f"❌ 오류 내용: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 콘텐츠 생성 중 오류: {e}")
        return False

def test_url_crawling():
    """3단계: URL 크롤링으로 콘텐츠 생성"""
    print_step(3, "URL 크롤링으로 콘텐츠 생성")
    
    test_url = "https://www.searchengineland.com/google-core-update-may-2024-447123"
    test_data = {
        "url": test_url,
        "keywords": "Google Core Update, SEO, search algorithm",
        "content_length": "1500",
        "ai_mode": "informative"
    }
    
    try:
        print(f"🌐 크롤링 URL: {test_url}")
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/generate-post",
            json=test_data,
            timeout=90
        )
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ URL 크롤링 성공! (소요시간: {end_time - start_time:.2f}초)")
            print(f"✅ 제목: {result['title']}")
            print(f"✅ 키워드: {result['keywords']}")
            print(f"✅ 단어 수: {result['word_count']}")
            return True
        else:
            print(f"❌ URL 크롤링 실패: {response.status_code}")
            print(f"❌ 오류 내용: {response.text}")
            return False
    except Exception as e:
        print(f"❌ URL 크롤링 중 오류: {e}")
        return False

def test_streaming_generation():
    """4단계: 스트리밍 콘텐츠 생성"""
    print_step(4, "스트리밍 콘텐츠 생성")
    
    test_data = {
        "text": "The future of technology is here. Blockchain, AI, and IoT are converging to create new possibilities.",
        "keywords": "blockchain, AI, IoT, technology",
        "content_length": "1000",
        "ai_mode": "creative"
    }
    
    try:
        print("📡 스트리밍 요청 시작...")
        
        params = "&".join([f"{k}={v}" for k, v in test_data.items()])
        response = requests.get(
            f"{API_BASE}/generate-post-stream?{params}",
            stream=True,
            timeout=60
        )
        
        if response.status_code == 200:
            print("✅ 스트리밍 연결 성공!")
            content = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 'data: ' 제거
                        try:
                            data = json.loads(data_str)
                            if 'step' in data:
                                print(f"   단계 {data['step']}: {data['message']} (진행률: {data['progress']}%)")
                            elif 'error' in data:
                                print(f"❌ 오류: {data['error']}")
                                return False
                            elif 'post' in data:
                                print("✅ 스트리밍 콘텐츠 생성 완료!")
                                return True
                        except json.JSONDecodeError:
                            continue
            return True
        else:
            print(f"❌ 스트리밍 연결 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 스트리밍 중 오류: {e}")
        return False

def test_system_stats():
    """5단계: 시스템 통계 확인"""
    print_step(5, "시스템 통계 확인")
    
    try:
        response = requests.get(f"{API_BASE}/stats/dashboard", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("📊 시스템 통계:")
            print(f"   총 포스트 수: {stats['total_posts']}")
            print(f"   총 키워드 수: {stats['total_keywords']}")
            print(f"   오늘 API 호출 수: {stats['api_calls_today']}")
            print(f"   크롤링 성공률: {stats['crawl_success_rate']}%")
            print(f"   OpenAI 호출 수: {stats['openai_calls']}")
            print(f"   Gemini 호출 수: {stats['gemini_calls']}")
            print(f"   번역 호출 수: {stats['translation_calls']}")
            print(f"   데이터베이스 크기: {stats['db_size']}")
            print(f"   시스템 가동시간: {stats['system_uptime']}")
            return True
        else:
            print(f"❌ 통계 조회 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 통계 조회 중 오류: {e}")
        return False

def test_frontend_access():
    """6단계: 프론트엔드 접근 테스트"""
    print_step(6, "프론트엔드 접근 테스트")
    
    endpoints = [
        ("/", "메인 페이지"),
        ("/admin", "관리자 페이지"),
        ("/test", "테스트 페이지"),
        ("/history", "히스토리 페이지")
    ]
    
    success_count = 0
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {name} 접근 성공")
                success_count += 1
            else:
                print(f"❌ {name} 접근 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ {name} 접근 오류: {e}")
    
    return success_count == len(endpoints)

def main():
    """메인 테스트 함수"""
    print("🚀 AI SEO Blogger - 콘텐츠 생성 기능 통합 테스트")
    print(f"📅 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        test_health_check,
        test_text_generation,
        test_url_crawling,
        test_streaming_generation,
        test_system_stats,
        test_frontend_access
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 테스트 실행 중 예외 발생: {e}")
            results.append(False)
    
    # 결과 요약
    print(f"\n{'='*60}")
    print("📋 테스트 결과 요약")
    print(f"{'='*60}")
    
    test_names = [
        "서버 헬스체크",
        "텍스트 콘텐츠 생성",
        "URL 크롤링 콘텐츠 생성",
        "스트리밍 콘텐츠 생성",
        "시스템 통계 확인",
        "프론트엔드 접근"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = "✅ 통과" if result else "❌ 실패"
        print(f"   {i}. {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 전체 결과: {passed}/{len(tests)} 테스트 통과")
    
    if passed == len(tests):
        print("🎉 모든 테스트가 성공적으로 통과했습니다!")
        print("✅ 콘텐츠 생성 기능이 정상적으로 작동하고 있습니다.")
        return 0
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        print("🔧 문제가 있는 기능을 확인하고 수정해주세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 