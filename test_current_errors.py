#!/usr/bin/env python3
"""
현재 시스템의 오류 확인 테스트
"""

from problem_generator import KSATMathGenerator
from latex_renderer import LaTeXRenderer
from graph_generator import MathGraphGenerator
import traceback

def test_all_components():
    print("전체 시스템 컴포넌트 테스트\n")
    print("=" * 60)
    
    errors_found = []
    
    # 1. 문제 생성기 테스트
    print("\n1. 문제 생성기 테스트")
    print("-" * 40)
    try:
        generator = KSATMathGenerator()
        
        # 각 주제별로 문제 생성 테스트
        topics = ["삼각함수", "미분과 적분", "기하와 벡터", "확률과 통계"]
        
        for topic in topics:
            print(f"  테스트: {topic}")
            try:
                problem = generator.generate_problem(
                    exam_type="가형",
                    problem_type="선택형",
                    topic=topic,
                    difficulty="중",
                    points=3
                )
                
                if 'error' in problem:
                    print(f"    ⚠ 경고: {problem['error']}")
                    errors_found.append(f"문제 생성 경고 ({topic}): {problem['error']}")
                else:
                    print(f"    ✓ 성공")
                    
                    # 그래프가 있는 경우 확인
                    if 'graph' in problem:
                        print(f"      - 그래프 포함됨")
                        
            except Exception as e:
                print(f"    ✗ 오류: {str(e)}")
                errors_found.append(f"문제 생성 오류 ({topic}): {str(e)}")
                traceback.print_exc()
                
    except Exception as e:
        print(f"  ✗ 생성기 초기화 실패: {str(e)}")
        errors_found.append(f"생성기 초기화 오류: {str(e)}")
        traceback.print_exc()
    
    # 2. LaTeX 렌더러 테스트
    print("\n2. LaTeX 렌더러 테스트")
    print("-" * 40)
    try:
        renderer = LaTeXRenderer()
        
        test_texts = [
            "함수 f(x) = x² + 2x + 1",
            "sin x + cos x = 1",
            "∫ x² dx",
            "lim_{x→0} sin x/x"
        ]
        
        for text in test_texts:
            print(f"  테스트: {text[:30]}...")
            try:
                result = renderer.render_for_streamlit(text)
                if '$' in result:
                    print(f"    ✓ 성공 (LaTeX 변환됨)")
                else:
                    print(f"    ⚠ 경고: LaTeX 변환 안됨")
                    errors_found.append(f"LaTeX 변환 실패: {text}")
            except Exception as e:
                print(f"    ✗ 오류: {str(e)}")
                errors_found.append(f"LaTeX 렌더링 오류: {str(e)}")
                
    except Exception as e:
        print(f"  ✗ 렌더러 초기화 실패: {str(e)}")
        errors_found.append(f"렌더러 초기화 오류: {str(e)}")
        traceback.print_exc()
    
    # 3. 그래프 생성기 테스트
    print("\n3. 그래프 생성기 테스트")
    print("-" * 40)
    try:
        graph_gen = MathGraphGenerator()
        
        # 다양한 그래프 타입 테스트
        test_graphs = [
            ("삼각함수", lambda: graph_gen.generate_trigonometric_graph(['sin', 'cos'])),
            ("2차 함수", lambda: graph_gen.generate_function_graph('x**2 - 2*x + 1')),
            ("매개변수 함수", lambda: graph_gen.generate_function_graph('a*x + b')),
            ("기하 도형", lambda: graph_gen.generate_geometry_figure('triangle', {'vertices': [(0,0), (1,0), (0.5,1)]}))
        ]
        
        for name, generator_func in test_graphs:
            print(f"  테스트: {name}")
            try:
                result = generator_func()
                if result:
                    print(f"    ✓ 성공")
                else:
                    print(f"    ⚠ 경고: 결과 없음")
                    errors_found.append(f"그래프 생성 경고 ({name}): 결과 없음")
            except Exception as e:
                print(f"    ✗ 오류: {str(e)}")
                errors_found.append(f"그래프 생성 오류 ({name}): {str(e)}")
                
    except Exception as e:
        print(f"  ✗ 그래프 생성기 초기화 실패: {str(e)}")
        errors_found.append(f"그래프 생성기 초기화 오류: {str(e)}")
        traceback.print_exc()
    
    # 4. 통합 테스트
    print("\n4. 통합 테스트 (문제 생성 → LaTeX 렌더링 → 그래프 생성)")
    print("-" * 40)
    try:
        generator = KSATMathGenerator()
        renderer = LaTeXRenderer()
        
        # 삼각함수 문제 생성 (그래프 포함 가능성 높음)
        print("  삼각함수 문제 생성 중...")
        problem = generator.generate_problem(
            exam_type="가형",
            problem_type="선택형",
            topic="삼각함수",
            difficulty="중",
            points=3
        )
        
        if 'error' not in problem:
            # LaTeX 렌더링
            print("  LaTeX 렌더링 중...")
            rendered_problem = renderer.process_problem_text(problem)
            
            print(f"    ✓ 문제 생성 및 렌더링 성공")
            
            if 'graph' in problem:
                print(f"    ✓ 그래프 포함됨")
            
            # 문제 내용 확인
            if '$' in rendered_problem.get('question', ''):
                print(f"    ✓ LaTeX 수식 포함됨")
            else:
                print(f"    ⚠ LaTeX 수식 없음")
                
        else:
            print(f"  ⚠ 문제 생성 오류: {problem['error']}")
            errors_found.append(f"통합 테스트 오류: {problem['error']}")
            
    except Exception as e:
        print(f"  ✗ 통합 테스트 실패: {str(e)}")
        errors_found.append(f"통합 테스트 오류: {str(e)}")
        traceback.print_exc()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    if errors_found:
        print(f"\n발견된 오류/경고: {len(errors_found)}개\n")
        for i, error in enumerate(errors_found, 1):
            print(f"{i}. {error}")
    else:
        print("\n✅ 모든 테스트 통과! 오류 없음")
    
    return len(errors_found) == 0

if __name__ == "__main__":
    success = test_all_components()
    exit(0 if success else 1)