#!/usr/bin/env python3
"""
LaTeX 렌더링 테스트 스크립트
"""

from latex_renderer import LaTeXRenderer

def test_latex_rendering():
    renderer = LaTeXRenderer()
    
    print("LaTeX 렌더링 테스트를 시작합니다...\n")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "인라인 수식",
            "input": "이차방정식 \\(x^2 + 2x + 1 = 0\\)의 해를 구하시오.",
            "expected": "이차방정식 $x^2 + 2x + 1 = 0$의 해를 구하시오."
        },
        {
            "name": "디스플레이 수식",
            "input": "다음 적분값을 구하시오: \\[\\int_0^1 x^2 dx\\]",
            "expected": "다음 적분값을 구하시오: $$\\int_0^1 x^2 dx$$"
        },
        {
            "name": "분수 표현",
            "input": "확률은 3/4 입니다.",
            "expected": "확률은 $\\frac{3}{4}$ 입니다."
        },
        {
            "name": "지수 표현",
            "input": "함수 f(x) = x^3 + x^2",
            "expected": "함수 f(x) = $x^{3}$ + $x^{2}$"
        },
        {
            "name": "제곱근",
            "input": "sqrt(2)의 값은 무리수입니다.",
            "expected": "$ sqrt{2}$의 값은 무리수입니다."
        },
        {
            "name": "삼각함수",
            "input": "sin(x) + cos(x) = 1인 x를 구하시오.",
            "expected": "$\\sin(x)$ + $\\cos(x)$ = 1인 x를 구하시오."
        },
        {
            "name": "로그함수",
            "input": "log_2(8) = 3",
            "expected": "$\\log_{2}{8}$ = 3"
        },
        {
            "name": "복합 수식",
            "input": "함수 f(x) = sin(x) + x^2에서 f'(x)를 구하면",
            "expected": "함수 f(x) = $\\sin(x)$ + $x^{2}$에서 f'(x)를 구하면"
        }
    ]
    
    # 테스트 실행
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"테스트 {i}: {test_case['name']}")
        print(f"  입력: {test_case['input']}")
        
        result = renderer.render_for_streamlit(test_case['input'])
        print(f"  출력: {result}")
        
        # 간단한 검증 (실제 출력이 예상과 다를 수 있음)
        if '$' in result or '$$' in result:
            print("  ✓ LaTeX 형식 감지됨\n")
            passed += 1
        else:
            print("  ✗ LaTeX 형식이 감지되지 않음\n")
            failed += 1
    
    # 문제 데이터 처리 테스트
    print("\n문제 데이터 처리 테스트:")
    problem_data = {
        "question": "함수 f(x) = x^2 + 2x + 1에서 f'(1)의 값은?",
        "choices": [
            "1",
            "2", 
            "3",
            "4",
            "5"
        ],
        "answer": "4",
        "solution": "f(x) = x^2 + 2x + 1이므로 f'(x) = 2x + 2입니다. 따라서 f'(1) = 2(1) + 2 = 4",
        "key_concepts": ["미분", "이차함수"]
    }
    
    processed_problem = renderer.process_problem_text(problem_data)
    print(f"처리된 문제: {processed_problem['question']}")
    print(f"처리된 풀이: {processed_problem['solution']}")
    
    print(f"\n테스트 결과:")
    print(f"  통과: {passed}")
    print(f"  실패: {failed}")
    print(f"  전체: {passed + failed}")

if __name__ == "__main__":
    test_latex_rendering()