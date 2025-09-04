#!/usr/bin/env python3
"""
보수적 그래프 생성 테스트
"""

from problem_generator import KSATMathGenerator
import json

def test_conservative_graph_generation():
    generator = KSATMathGenerator()
    
    print("보수적 그래프 생성 테스트...")
    print("대부분의 문제에서 그래프가 생성되지 않아야 합니다.\n")
    
    test_topics = [
        "미적분",
        "확률과 통계", 
        "수열",
        "함수와 그래프",
        "삼각함수"
    ]
    
    graph_count = 0
    total_count = 0
    
    for topic in test_topics:
        print(f"=== {topic} 문제 테스트 ===")
        try:
            problem = generator.generate_problem(
                exam_type="가형",
                problem_type="선택형",
                topic=topic,
                difficulty="중",
                points=3
            )
            
            total_count += 1
            
            if "error" in problem:
                print(f"오류: {problem['error']}")
                continue
                
            has_graph = "graph" in problem
            requires_graph = problem.get("requires_graph", False)
            
            if has_graph:
                graph_count += 1
                print(f"✓ 그래프 생성됨 (requires_graph: {requires_graph})")
            else:
                print(f"○ 그래프 없음 (requires_graph: {requires_graph})")
                
            print(f"질문: {problem['question'][:150]}...")
            print()
            
        except Exception as e:
            print(f"테스트 중 오류: {str(e)}")
            continue
    
    print(f"\n=== 결과 요약 ===")
    print(f"전체 문제: {total_count}개")
    print(f"그래프 생성: {graph_count}개")
    print(f"그래프 생성 비율: {(graph_count/total_count)*100:.1f}%" if total_count > 0 else "계산 불가")
    print("목표: 그래프 생성 비율이 10% 미만이어야 함")

if __name__ == "__main__":
    test_conservative_graph_generation()