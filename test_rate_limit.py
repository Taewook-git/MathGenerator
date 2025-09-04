#!/usr/bin/env python3
"""
API 할당량 제한 처리 테스트
"""

from problem_generator import KSATMathGenerator
import time

def test_rate_limiting():
    generator = KSATMathGenerator()
    
    print("Rate limiting 테스트 시작...")
    print("Note: 실제 API를 호출하므로 시간이 걸릴 수 있습니다.\n")
    
    # 간단한 문제 몇 개 생성해서 rate limiting이 작동하는지 확인
    for i in range(3):
        print(f"=== 문제 {i+1} 생성 ===")
        start_time = time.time()
        
        problem = generator.generate_problem(
            exam_type="가형",
            problem_type="선택형", 
            topic="함수와 그래프",
            difficulty="중",
            points=3
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        if "error" in problem:
            print(f"오류: {problem['error']}")
            if "suggestion" in problem:
                print(f"제안: {problem['suggestion']}")
        else:
            print(f"성공: 문제 생성됨 (소요시간: {elapsed:.1f}초)")
            print(f"질문: {problem['question'][:100]}...")
        
        print()

if __name__ == "__main__":
    test_rate_limiting()