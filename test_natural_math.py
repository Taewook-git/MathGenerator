#!/usr/bin/env python3
"""
자연스러운 수식 표현 테스트 스크립트
"""

from latex_renderer import LaTeXRenderer

def test_natural_math_rendering():
    renderer = LaTeXRenderer()
    
    print("자연스러운 수식 렌더링 테스트를 시작합니다...\n")
    
    # 다양한 수식 패턴 테스트
    test_cases = [
        {
            "name": "이차방정식",
            "input": "함수 f(x) = x² + 2x + 1에서 f'(x)를 구하시오.",
            "description": "제곱 기호 사용"
        },
        {
            "name": "분수",
            "input": "확률은 3/4이고, x/2 + y/3 = 1입니다.",
            "description": "자연스러운 분수 표현"
        },
        {
            "name": "지수와 로그",
            "input": "방정식 2^x = 8을 풀면 log_2(8) = 3입니다.",
            "description": "지수와 로그 표현"
        },
        {
            "name": "삼각함수",
            "input": "sin x + cos x = 1일 때, tan x의 값을 구하시오.",
            "description": "삼각함수 표현"
        },
        {
            "name": "적분과 극한",
            "input": "∫ x² dx를 계산하고, lim_{x→0} sin x/x = 1임을 증명하시오.",
            "description": "적분과 극한 기호"
        },
        {
            "name": "벡터",
            "input": "벡터 →a와 →b의 내적 →a·→b를 구하시오.",
            "description": "벡터 표현"
        },
        {
            "name": "집합",
            "input": "집합 A = {x | x² < 4}에서 x ∈ (-2, 2)입니다.",
            "description": "집합 표기"
        },
        {
            "name": "그리스 문자",
            "input": "각 θ에 대해 sin θ + cos θ = √2일 때, θ = π/4",
            "description": "그리스 문자 사용"
        },
        {
            "name": "미분",
            "input": "f(x) = x³일 때, f'(x) = 3x², f''(x) = 6x",
            "description": "도함수 표현"
        },
        {
            "name": "제곱근",
            "input": "방정식 √x + √(x+1) = 3의 해를 구하시오.",
            "description": "제곱근 기호"
        },
        {
            "name": "수열",
            "input": "수열 a_n = n² + 1에서 a_1 = 2, a_2 = 5입니다.",
            "description": "첨자 표현"
        },
        {
            "name": "부등호",
            "input": "x² ≤ 4이면 -2 ≤ x ≤ 2이고, x ≠ 0일 때 x² > 0",
            "description": "부등호 기호"
        },
        {
            "name": "복합 수식",
            "input": "∑_{n=1}^{∞} 1/n² = π²/6이고, ∏_{k=1}^n k = n!",
            "description": "시그마와 파이 기호"
        }
    ]
    
    print("=" * 60)
    for test in test_cases:
        print(f"\n테스트: {test['name']}")
        print(f"설명: {test['description']}")
        print(f"입력: {test['input']}")
        
        result = renderer.render_for_streamlit(test['input'])
        print(f"출력: {result}")
        print("-" * 40)
    
    # 실제 수능 스타일 문제 테스트
    print("\n" + "=" * 60)
    print("\n실제 수능 스타일 문제 테스트:")
    
    ksat_problem = {
        "question": "함수 f(x) = x³ - 3x² + 2에 대하여 f'(x) = 0을 만족하는 x의 값을 모두 구한 것은?",
        "choices": [
            "x = 0",
            "x = 2", 
            "x = 0, 2",
            "x = 1, 2",
            "x = 0, 1"
        ],
        "answer": "③",
        "solution": "f(x) = x³ - 3x² + 2이므로\nf'(x) = 3x² - 6x = 3x(x - 2)\n따라서 f'(x) = 0일 때, x = 0 또는 x = 2",
        "key_concepts": ["미분", "도함수", "극값"]
    }
    
    processed = renderer.process_problem_text(ksat_problem)
    
    print("\n처리된 문제:")
    print(f"문제: {processed['question']}")
    print("\n선택지:")
    for i, choice in enumerate(processed['choices'], 1):
        print(f"  {i}. {choice}")
    print(f"\n정답: {processed['answer']}")
    print(f"\n풀이:\n{processed['solution']}")
    print(f"\n핵심 개념: {', '.join(processed['key_concepts'])}")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")

if __name__ == "__main__":
    test_natural_math_rendering()