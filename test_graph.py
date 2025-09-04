#!/usr/bin/env python3
"""
그래프 생성 기능 테스트 스크립트
"""

from graph_generator import MathGraphGenerator
import os

def test_graph_generator():
    generator = MathGraphGenerator()
    
    print("그래프 생성 테스트를 시작합니다...\n")
    
    # 1. 삼각함수 그래프 테스트
    print("1. 삼각함수 그래프 생성 중...")
    trig_graph = generator.generate_trigonometric_graph(
        functions=['sin', 'cos'],
        title='sin(x)와 cos(x) 그래프'
    )
    generator.save_graph_to_file(trig_graph, 'test_trig.png')
    print("   ✓ test_trig.png 저장 완료\n")
    
    # 2. 기하 도형 테스트 - 삼각형
    print("2. 삼각형 도형 생성 중...")
    triangle_graph = generator.generate_geometry_figure(
        figure_type='triangle',
        params={
            'vertices': [(0, 0), (3, 0), (1.5, 2.6)],
            'title': '정삼각형',
            'show_sides': True
        }
    )
    generator.save_graph_to_file(triangle_graph, 'test_triangle.png')
    print("   ✓ test_triangle.png 저장 완료\n")
    
    # 3. 원 도형 테스트
    print("3. 원 도형 생성 중...")
    circle_graph = generator.generate_geometry_figure(
        figure_type='circle',
        params={
            'center': (0, 0),
            'radius': 2,
            'title': '원',
            'show_radius': True
        }
    )
    generator.save_graph_to_file(circle_graph, 'test_circle.png')
    print("   ✓ test_circle.png 저장 완료\n")
    
    # 4. 2차 함수 그래프 테스트
    print("4. 2차 함수 그래프 생성 중...")
    quadratic_graph = generator.generate_function_graph(
        function_str='x**2 - 4*x + 3',
        x_range=(-1, 5),
        title='f(x) = x² - 4x + 3'
    )
    generator.save_graph_to_file(quadratic_graph, 'test_quadratic.png')
    print("   ✓ test_quadratic.png 저장 완료\n")
    
    # 5. 벡터 다이어그램 테스트
    print("5. 벡터 다이어그램 생성 중...")
    vector_graph = generator.generate_vector_diagram(
        vectors=[(3, 2, 'a'), (1, 4, 'b'), (4, 6, 'a+b')],
        title='벡터 합성'
    )
    generator.save_graph_to_file(vector_graph, 'test_vector.png')
    print("   ✓ test_vector.png 저장 완료\n")
    
    # 6. 복합 삼각함수 테스트 (tan 포함)
    print("6. 복합 삼각함수 그래프 생성 중...")
    complex_trig = generator.generate_trigonometric_graph(
        functions=['sin', 'cos', 'tan'],
        title='삼각함수 sin(x), cos(x), tan(x)'
    )
    generator.save_graph_to_file(complex_trig, 'test_complex_trig.png')
    print("   ✓ test_complex_trig.png 저장 완료\n")
    
    print("모든 테스트가 완료되었습니다!")
    print("생성된 이미지 파일:")
    for file in ['test_trig.png', 'test_triangle.png', 'test_circle.png', 
                 'test_quadratic.png', 'test_vector.png', 'test_complex_trig.png']:
        if os.path.exists(file):
            print(f"  - {file}")

if __name__ == "__main__":
    test_graph_generator()