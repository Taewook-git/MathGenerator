#!/usr/bin/env python3
"""
NameError 수정 테스트
"""

from graph_generator import MathGraphGenerator

def test_function_graphs():
    generator = MathGraphGenerator()
    
    print("함수 그래프 생성 테스트 (NameError 수정 확인)\n")
    
    test_functions = [
        # 정상적인 함수들
        ("x**2", "이차함수"),
        ("2*x + 1", "일차함수"),
        ("sin(x)", "사인함수"),
        ("x**3 - 3*x", "3차함수"),
        
        # 매개변수가 있는 함수들 (이전에 오류 발생)
        ("a*x**2", "매개변수 a가 있는 이차함수"),
        ("a*x + b", "매개변수 a, b가 있는 일차함수"),
        ("m*sin(x) + n", "매개변수가 있는 삼각함수"),
        
        # 복잡한 표현
        ("x^2 + 2*x + 1", "^ 기호 사용"),
        ("x**2 - a*x + b", "여러 매개변수"),
        
        # 특수 함수
        ("exp(x)", "지수함수"),
        ("log(x)", "로그함수"),
        ("sqrt(x)", "제곱근함수"),
    ]
    
    success_count = 0
    fail_count = 0
    
    for func_str, description in test_functions:
        print(f"테스트: {description}")
        print(f"  함수: y = {func_str}")
        
        try:
            # 그래프 생성 시도
            image_data = generator.generate_function_graph(
                function_str=func_str,
                x_range=(-5, 5),
                title=f'{description}: y = {func_str}'
            )
            
            if image_data:
                print("  ✓ 성공적으로 생성됨")
                success_count += 1
                
                # 테스트용 이미지 저장
                generator.save_graph_to_file(image_data, f'test_{func_str.replace("*", "").replace("/", "").replace("**", "pow")[:20]}.png')
            else:
                print("  ✗ 생성 실패")
                fail_count += 1
                
        except Exception as e:
            print(f"  ✗ 오류 발생: {e}")
            fail_count += 1
        
        print()
    
    print("-" * 50)
    print(f"테스트 결과: 성공 {success_count}, 실패 {fail_count}")
    print(f"성공률: {success_count/(success_count+fail_count)*100:.1f}%")
    
    # 특별 테스트: 의도적으로 정의되지 않은 변수 사용
    print("\n" + "=" * 50)
    print("의도적 오류 테스트 (정의되지 않은 변수)")
    
    error_tests = [
        ("z**2", "정의되지 않은 변수 z"),
        ("y + x", "정의되지 않은 변수 y"),
        ("undefined_var", "정의되지 않은 변수"),
    ]
    
    for func_str, description in error_tests:
        print(f"\n{description}: {func_str}")
        try:
            image_data = generator.generate_function_graph(
                function_str=func_str,
                x_range=(-5, 5),
                title=f'오류 테스트: {func_str}'
            )
            print("  오류 메시지가 포함된 그래프 생성됨")
        except Exception as e:
            print(f"  예외 발생: {e}")

if __name__ == "__main__":
    test_function_graphs()