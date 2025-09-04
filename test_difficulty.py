#!/usr/bin/env python3
"""
난이도 향상 테스트
"""

from problem_generator import KSATMathGenerator
import json

def test_difficulty_levels():
    print("=" * 60)
    print("난이도별 문제 생성 테스트")
    print("=" * 60)
    
    generator = KSATMathGenerator()
    
    # 난이도별로 각 주제에 대한 문제 생성
    difficulty_levels = ["하", "중", "상"]
    test_topics = [
        "미분과 적분",
        "삼각함수",
        "확률과 통계",
        "함수의 극한과 연속성",  # 심화 주제
        "조건부 확률과 베이즈 정리"  # 심화 주제
    ]
    
    for difficulty in difficulty_levels:
        print(f"\n{'='*20} {difficulty} 난이도 {'='*20}")
        
        for topic in test_topics[:3]:  # 기본 주제만 테스트
            print(f"\n주제: {topic} (난이도: {difficulty})")
            print("-" * 40)
            
            try:
                problem = generator.generate_problem(
                    exam_type="가형",
                    problem_type="선택형",
                    topic=topic,
                    difficulty=difficulty,
                    points=4 if difficulty == "상" else 3
                )
                
                if 'error' in problem:
                    print(f"⚠ 오류: {problem['error']}")
                else:
                    print(f"✓ 문제 생성 성공")
                    print(f"  문제: {problem['question'][:100]}...")
                    
                    # 난이도 특성 확인
                    solution = problem.get('solution', '')
                    steps = solution.count('단계') + solution.count('Step') + solution.count('따라서')
                    print(f"  추정 풀이 단계: 약 {steps}단계")
                    
                    if problem.get('requires_graph'):
                        print("  ✓ 그래프 포함")
                    
                    key_concepts = problem.get('key_concepts', [])
                    if key_concepts:
                        print(f"  핵심 개념: {', '.join(key_concepts[:3])}")
                    
            except Exception as e:
                print(f"✗ 오류: {str(e)}")
    
    # 상 난이도 심화 주제 테스트
    print(f"\n{'='*20} 심화 주제 (상 난이도) {'='*20}")
    
    advanced_topics = [
        "함수의 극한과 연속성",
        "이계미분과 최댓값/최솟값",
        "조건부 확률과 베이즈 정리",
        "공간벡터와 외적"
    ]
    
    for topic in advanced_topics:
        print(f"\n심화 주제: {topic}")
        print("-" * 40)
        
        try:
            problem = generator.generate_problem(
                exam_type="가형",
                problem_type="단답형",  # 단답형으로 더 어렵게
                topic=topic,
                difficulty="상",
                points=4
            )
            
            if 'error' in problem:
                print(f"⚠ 오류: {problem['error']}")
            else:
                print(f"✓ 문제 생성 성공")
                print(f"  문제: {problem['question'][:150]}...")
                print(f"  정답: {problem.get('answer', 'N/A')}")
                
        except Exception as e:
            print(f"✗ 오류: {str(e)}")
    
    print("\n" + "=" * 60)
    print("난이도 테스트 완료")
    print("=" * 60)

def test_type_error_fix():
    """TypeError 수정 확인"""
    print("\nTypeError 수정 테스트")
    print("-" * 40)
    
    generator = KSATMathGenerator()
    
    # 정수형 답변이 나올 수 있는 문제 생성
    problem = generator.generate_problem(
        exam_type="가형",
        problem_type="단답형",
        topic="수열과 급수",
        difficulty="상",
        points=4
    )
    
    if 'error' not in problem:
        print("✓ 문제 생성 성공")
        # LaTeX 렌더러 테스트
        from latex_renderer import LaTeXRenderer
        renderer = LaTeXRenderer()
        
        try:
            rendered = renderer.process_problem_text(problem)
            print("✓ LaTeX 렌더링 성공 (TypeError 해결됨)")
        except TypeError as e:
            print(f"✗ TypeError 발생: {e}")
    else:
        print(f"⚠ 문제 생성 오류: {problem['error']}")

if __name__ == "__main__":
    # TypeError 수정 테스트
    test_type_error_fix()
    
    # 난이도별 문제 생성 테스트
    test_difficulty_levels()