#!/usr/bin/env python3
"""
극한 수식 렌더링 테스트
"""

from latex_renderer import LaTeXRenderer

def test_limit_expressions():
    renderer = LaTeXRenderer()
    
    # 다양한 극한 표현 테스트
    test_cases = [
        "lim(x→2) (x²-4)/(x-2)의 값은?",
        "lim[x→∞] (3x+1)/(2x-1) = 3/2이다.",
        "lim(x→0⁺) 1/x = ∞이고, lim(x→0⁻) 1/x = -∞이다.",
        "lim(n→∞) (1+1/n)^n = e",
        "함수 f(x) = x²에서 lim(h→0) [f(x+h) - f(x)]/h",
        "lim(x→1) (x³-1)/(x²-1)",
        "x→∞일 때 극한값",
        "단순히 lim만 쓰는 경우"
    ]
    
    print("=== 극한 표현 렌더링 테스트 ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. 원본: {test_case}")
        rendered = renderer.render_for_streamlit(test_case)
        print(f"   결과: {rendered}")
        print()
    
    # 문제 전체 데이터 테스트
    print("=== 문제 데이터 전체 처리 테스트 ===\n")
    
    sample_problem = {
        "question": "다음 극한값을 구하시오. lim(x→2) (x²-4)/(x-2)",
        "choices": [
            "lim(x→2) = 0",
            "lim(x→2) = 2", 
            "lim(x→2) = 4",
            "lim(x→2) = ∞",
            "극한값이 존재하지 않는다"
        ],
        "answer": "lim(x→2) = 4",
        "solution": "lim(x→2) (x²-4)/(x-2) = lim(x→2) (x+2)(x-2)/(x-2) = lim(x→2) (x+2) = 4",
        "key_concepts": ["극한", "인수분해", "lim 계산"]
    }
    
    processed = renderer.process_problem_text(sample_problem)
    
    print("처리된 문제:")
    for key, value in processed.items():
        print(f"{key}: {value}")
        print()

if __name__ == "__main__":
    test_limit_expressions()