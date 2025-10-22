#!/usr/bin/env python3
"""
전체 시스템 최적화 테스트 최종 리포트 생성
모든 테스트 결과를 종합하여 종합적인 시스템 상태를 분석합니다.
"""
import json
import os
from datetime import datetime

def load_test_report(filename):
    """테스트 리포트 파일 로드"""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def generate_final_report():
    """최종 종합 리포트 생성"""
    print("📋 전체 시스템 최적화 테스트 최종 리포트 생성")
    print("=" * 60)
    
    # 테스트 리포트들 로드
    optimization_report = load_test_report("system_optimization_report.json")
    stress_report = load_test_report("performance_stress_test_report.json")
    
    if not optimization_report and not stress_report:
        print("❌ 테스트 리포트 파일을 찾을 수 없습니다.")
        return
    
    # 종합 분석
    final_report = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "report_type": "전체 시스템 최적화 종합 리포트",
            "available_reports": []
        },
        "system_overview": {},
        "performance_summary": {},
        "optimization_recommendations": [],
        "detailed_analysis": {}
    }
    
    # 사용 가능한 리포트 목록
    if optimization_report:
        final_report["report_metadata"]["available_reports"].append("system_optimization_report.json")
    if stress_report:
        final_report["report_metadata"]["available_reports"].append("performance_stress_test_report.json")
    
    # 시스템 개요
    if optimization_report:
        opt_summary = optimization_report.get("test_summary", {})
        opt_metrics = optimization_report.get("performance_metrics", {})
        
        final_report["system_overview"] = {
            "overall_score": opt_summary.get("overall_score", 0),
            "test_duration": opt_summary.get("total_test_time", 0),
            "test_timestamp": opt_summary.get("test_timestamp", ""),
            "api_success_rate": opt_metrics.get("api_success_rate", 0),
            "database_health": opt_metrics.get("database_health", 0),
            "memory_efficiency": opt_metrics.get("memory_efficiency", 0),
            "cpu_efficiency": opt_metrics.get("cpu_efficiency", 0),
            "concurrent_performance": opt_metrics.get("concurrent_performance", 0),
            "error_handling": opt_metrics.get("error_handling", 0)
        }
    
    # 성능 요약
    if stress_report:
        stress_summary = stress_report.get("test_summary", {})
        stress_metrics = stress_report.get("performance_metrics", {})
        
        final_report["performance_summary"] = {
            "stress_test_score": stress_summary.get("overall_score", 0),
            "single_endpoint_performance": stress_metrics.get("single_endpoint_performance", 0),
            "mixed_endpoints_performance": stress_metrics.get("mixed_endpoints_performance", 0),
            "database_performance": stress_metrics.get("database_performance", 0),
            "memory_stability": stress_metrics.get("memory_stability", 0)
        }
    
    # 상세 분석
    if optimization_report:
        final_report["detailed_analysis"]["optimization_test"] = {
            "api_endpoints": optimization_report.get("detailed_results", {}).get("api_endpoints", {}),
            "database": optimization_report.get("detailed_results", {}).get("database", {}),
            "memory": optimization_report.get("detailed_results", {}).get("memory", {}),
            "cpu": optimization_report.get("detailed_results", {}).get("cpu", {}),
            "concurrent_requests": optimization_report.get("detailed_results", {}).get("concurrent_requests", {}),
            "file_system": optimization_report.get("detailed_results", {}).get("file_system", {}),
            "error_handling": optimization_report.get("detailed_results", {}).get("error_handling", {})
        }
    
    if stress_report:
        final_report["detailed_analysis"]["stress_test"] = {
            "single_endpoint": stress_report.get("detailed_results", {}).get("single_endpoint", {}),
            "mixed_endpoints": stress_report.get("detailed_results", {}).get("mixed_endpoints", {}),
            "database_load": stress_report.get("detailed_results", {}).get("database_load", {}),
            "memory_leak": stress_report.get("detailed_results", {}).get("memory_leak", {})
        }
    
    # 최적화 권장사항 통합
    recommendations = []
    
    if optimization_report:
        opt_recs = optimization_report.get("recommendations", [])
        recommendations.extend([f"[기본 최적화] {rec}" for rec in opt_recs])
    
    if stress_report:
        stress_recs = stress_report.get("recommendations", [])
        recommendations.extend([f"[스트레스 테스트] {rec}" for rec in stress_recs])
    
    # 추가 종합 권장사항
    if optimization_report and stress_report:
        opt_score = optimization_report.get("test_summary", {}).get("overall_score", 0)
        stress_score = stress_report.get("test_summary", {}).get("overall_score", 0)
        
        if opt_score >= 80 and stress_score >= 90:
            recommendations.append("🎉 시스템이 모든 테스트를 성공적으로 통과했습니다. 현재 설정을 유지하세요.")
        elif opt_score >= 70 and stress_score >= 80:
            recommendations.append("✅ 시스템이 대부분의 테스트를 통과했습니다. 일부 최적화를 고려하세요.")
        else:
            recommendations.append("⚠️ 시스템 최적화가 필요합니다. 권장사항을 따라 개선하세요.")
    
    final_report["optimization_recommendations"] = recommendations
    
    # 시스템 상태 등급
    if optimization_report and stress_report:
        opt_score = optimization_report.get("test_summary", {}).get("overall_score", 0)
        stress_score = stress_report.get("test_summary", {}).get("overall_score", 0)
        avg_score = (opt_score + stress_score) / 2
        
        if avg_score >= 90:
            grade = "A+ (우수)"
            status = "최적 상태"
        elif avg_score >= 80:
            grade = "A (양호)"
            status = "양호 상태"
        elif avg_score >= 70:
            grade = "B (보통)"
            status = "개선 필요"
        elif avg_score >= 60:
            grade = "C (미흡)"
            status = "중요 개선 필요"
        else:
            grade = "D (불량)"
            status = "긴급 개선 필요"
        
        final_report["system_grade"] = {
            "grade": grade,
            "status": status,
            "average_score": avg_score,
            "optimization_score": opt_score,
            "stress_test_score": stress_score
        }
    
    # 리포트 저장
    with open("final_system_optimization_report.json", "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    # 결과 출력
    print_final_summary(final_report)
    
    return final_report

def print_final_summary(report):
    """최종 요약 출력"""
    print("\n" + "=" * 60)
    print("🎯 전체 시스템 최적화 테스트 최종 결과")
    print("=" * 60)
    
    # 시스템 등급
    if "system_grade" in report:
        grade_info = report["system_grade"]
        print(f"📊 시스템 등급: {grade_info['grade']}")
        print(f"📈 평균 점수: {grade_info['average_score']:.1f}/100")
        print(f"🔍 시스템 상태: {grade_info['status']}")
        print(f"   - 기본 최적화 점수: {grade_info['optimization_score']:.1f}/100")
        print(f"   - 스트레스 테스트 점수: {grade_info['stress_test_score']:.1f}/100")
    
    # 성능 지표
    if "system_overview" in report:
        overview = report["system_overview"]
        print(f"\n📈 기본 성능 지표:")
        print(f"   API 성공률: {overview.get('api_success_rate', 0):.1f}%")
        print(f"   데이터베이스 상태: {overview.get('database_health', 0):.1f}%")
        print(f"   메모리 효율성: {overview.get('memory_efficiency', 0):.1f}%")
        print(f"   CPU 효율성: {overview.get('cpu_efficiency', 0):.1f}%")
        print(f"   동시 처리 성능: {overview.get('concurrent_performance', 0):.1f}%")
        print(f"   에러 처리: {overview.get('error_handling', 0):.1f}%")
    
    if "performance_summary" in report:
        perf_summary = report["performance_summary"]
        print(f"\n🔥 스트레스 테스트 성능:")
        print(f"   단일 엔드포인트 성능: {perf_summary.get('single_endpoint_performance', 0):.1f}%")
        print(f"   혼합 엔드포인트 성능: {perf_summary.get('mixed_endpoints_performance', 0):.1f}%")
        print(f"   데이터베이스 성능: {perf_summary.get('database_performance', 0):.1f}%")
        print(f"   메모리 안정성: {perf_summary.get('memory_stability', 0):.1f}%")
    
    # 주요 성능 데이터
    print(f"\n📊 주요 성능 데이터:")
    
    if "detailed_analysis" in report:
        analysis = report["detailed_analysis"]
        
        # API 응답시간
        if "optimization_test" in analysis:
            opt_test = analysis["optimization_test"]
            api_details = opt_test.get("api_endpoints", {})
            if api_details:
                avg_response_time = api_details.get("average_response_time", 0)
                print(f"   평균 API 응답시간: {avg_response_time:.2f}ms")
        
        # 데이터베이스 정보
        if "optimization_test" in analysis:
            db_info = opt_test.get("database", {})
            if db_info:
                table_count = db_info.get("table_count", 0)
                total_records = db_info.get("total_records", 0)
                db_size = db_info.get("db_size_kb", 0)
                print(f"   데이터베이스: {table_count}개 테이블, {total_records}개 레코드, {db_size:.2f}KB")
        
        # 메모리 정보
        if "optimization_test" in analysis:
            memory_info = opt_test.get("memory", {})
            if memory_info:
                memory_percent = memory_info.get("memory_percent", 0)
                total_memory = memory_info.get("total_memory_gb", 0)
                print(f"   메모리 사용률: {memory_percent:.1f}% (전체 {total_memory:.1f}GB)")
        
        # CPU 정보
        if "optimization_test" in analysis:
            cpu_info = opt_test.get("cpu", {})
            if cpu_info:
                avg_cpu = cpu_info.get("average_cpu_percent", 0)
                cpu_cores = cpu_info.get("cpu_cores", 0)
                print(f"   CPU 사용률: {avg_cpu:.1f}% ({cpu_cores}코어)")
    
    # 최적화 권장사항
    print(f"\n💡 최적화 권장사항:")
    for i, rec in enumerate(report.get("optimization_recommendations", []), 1):
        print(f"   {i}. {rec}")
    
    print(f"\n📄 상세 리포트: final_system_optimization_report.json")
    print("=" * 60)

def main():
    """메인 함수"""
    generate_final_report()

if __name__ == "__main__":
    main() 