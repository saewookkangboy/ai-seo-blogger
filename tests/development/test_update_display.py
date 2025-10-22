#!/usr/bin/env python3
"""
업데이트 이력 표시 문제 테스트 스크립트
날짜 파싱 및 통계 표시 확인
"""
import requests
import json
from datetime import datetime

def test_date_parsing():
    """날짜 파싱 테스트"""
    print("=== 날짜 파싱 테스트 ===")
    
    # API에서 업데이트 데이터 가져오기
    response = requests.get('http://localhost:8000/api/v1/feature-updates/history')
    if response.status_code != 200:
        print("❌ API 응답 오류:", response.status_code)
        return
    
    updates = response.json()
    print(f"총 업데이트: {len(updates)}개")
    
    # 샘플 업데이트의 날짜 확인
    sample_updates = updates[:5]
    for i, update in enumerate(sample_updates):
        date_str = update.get('date') or update.get('created_at')
        print(f"업데이트 {i+1}: {date_str}")
        
        # 날짜 파싱 테스트
        if date_str and isinstance(date_str, str):
            if '.' in date_str:
                # YYYY.MM.DD 형식을 YYYY-MM-DD로 변환
                converted_date = date_str.replace('.', '-')
                try:
                    parsed_date = datetime.strptime(converted_date, '%Y-%m-%d')
                    print(f"  ✅ 파싱 성공: {parsed_date.strftime('%Y년 %m월 %d일')}")
                except ValueError as e:
                    print(f"  ❌ 파싱 실패: {e}")
            else:
                print(f"  ℹ️  다른 형식: {date_str}")

def test_statistics():
    """통계 계산 테스트"""
    print("\n=== 통계 계산 테스트 ===")
    
    response = requests.get('http://localhost:8000/api/v1/feature-updates/history')
    if response.status_code != 200:
        print("❌ API 응답 오류:", response.status_code)
        return
    
    updates = response.json()
    
    # 카테고리별 통계
    categories = {}
    importance = {}
    
    for update in updates:
        cat = update.get('category', '기타')
        categories[cat] = categories.get(cat, 0) + 1
        
        imp = update.get('importance', '낮음')
        importance[imp] = importance.get(imp, 0) + 1
    
    print(f"총 업데이트: {len(updates)}개")
    print("\n카테고리별 통계:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}개")
    
    print("\n중요도별 통계:")
    for imp, count in sorted(importance.items()):
        print(f"  {imp}: {count}개")

def test_api_endpoints():
    """API 엔드포인트 테스트"""
    print("\n=== API 엔드포인트 테스트 ===")
    
    endpoints = [
        '/api/v1/feature-updates/history',
        '/api/v1/feature-updates/statistics',
        '/api/v1/feature-updates/trends'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}')
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✅ {endpoint}: {len(data)}개 항목")
                else:
                    print(f"✅ {endpoint}: {type(data).__name__}")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def main():
    """메인 함수"""
    print("🚀 업데이트 이력 표시 문제 테스트 시작")
    
    try:
        test_date_parsing()
        test_statistics()
        test_api_endpoints()
        
        print("\n✅ 모든 테스트 완료!")
        print("\n💡 브라우저에서 http://localhost:8000/admin 접속 후 '업데이트 이력' 탭을 확인하세요.")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    main() 