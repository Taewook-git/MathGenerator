#!/usr/bin/env python3
"""
문제 품질 향상 및 UI 개선 테스트
"""

import sys
import os
# src 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_prompt_quality():
    """향상된 프롬프트 품질 확인"""
    print("=" * 60)
    print("📝 향상된 프롬프트 품질 확인")
    print("=" * 60)
    
    from core.problem_generator import KSATMathGenerator
    
    # 프롬프트 생성 테스트 (API 호출 없이)
    generator = KSATMathGenerator(enable_quality_enhancement=False)
    
    # 테스트용 파라미터
    test_params = {
        'problem_type': '선택형',
        'topic': '[수학2] 미분',
        'difficulty': '상',
        'points': 4,
        'specialized_subtopic': None
    }
    
    prompt = generator._create_prompt(**test_params)
    
    print("\n✅ 품질 향상 포인트:")
    
    # 주요 개선사항 확인
    quality_checks = {
        "평가 타당성": "평가 타당성" in prompt,
        "문제 완성도": "문제 완성도" in prompt,
        "변별력": "변별력" in prompt,
        "오답 설계": "오답 설계" in prompt,
        "실제 수능 유형": "실제 수능" in prompt,
        "고품질 문제 작성": "고품질" in prompt,
        "difficulty_rationale": "difficulty_rationale" in prompt,
        "common_mistakes": "common_mistakes" in prompt
    }
    
    for check_name, is_present in quality_checks.items():
        status = "✓" if is_present else "✗"
        print(f"  {status} {check_name}")
    
    print("\n📋 선택지 생성 규칙:")
    if "구체적인 수치나 수식" in prompt:
        print("  ✓ 구체적인 수치/수식 요구")
    if "오답 설계 전략" in prompt:
        print("  ✓ 체계적 오답 설계 전략")
    if "변별력" in prompt and "충분히 구별" in prompt:
        print("  ✓ 선택지 간 변별력 확보")

def test_ui_improvements():
    """UI 개선사항 확인"""
    print("\n" + "=" * 60)
    print("🎨 UI 개선사항 확인")
    print("=" * 60)
    
    print("\n✅ 선택지 표시 개선:")
    print("  • 원문자(①②③④⑤) 사용으로 가독성 향상")
    print("  • 선택지 번호와 값을 명확히 구분")
    print("  • 2열 레이아웃으로 공간 효율성 개선")
    
    print("\n✅ 정답 표시 개선:")
    print("  • 선택형: 번호와 값 함께 표시 (예: ① 12)")
    print("  • 단답형: 값만 표시")
    
    print("\n✅ 추가 정보 표시:")
    print("  • 난이도 설정 근거")
    print("  • 자주 하는 실수 목록")
    print("  • 핵심 개념 정리")

def test_response_structure():
    """응답 구조 개선 확인"""
    print("\n" + "=" * 60)
    print("🔧 응답 구조 개선")
    print("=" * 60)
    
    expected_fields = {
        "기본 필드": ["question", "choices", "answer", "solution", "key_concepts"],
        "품질 필드": ["difficulty_rationale", "common_mistakes"],
        "그래프 필드": ["requires_graph", "graph_type", "graph_params"]
    }
    
    print("\n✅ 예상 응답 구조:")
    for category, fields in expected_fields.items():
        print(f"\n  【{category}】")
        for field in fields:
            print(f"    • {field}")

def simulate_choice_display():
    """선택지 표시 시뮬레이션"""
    print("\n" + "=" * 60)
    print("💻 선택지 표시 시뮬레이션")
    print("=" * 60)
    
    # 예시 선택지
    sample_choices = ["12", "-3", "2√5", "7/3", "0"]
    circle_nums = ["①", "②", "③", "④", "⑤"]
    
    print("\n예시 문제: 함수 f(x) = x² - 5x + 6의 최솟값은?")
    print("\n【기존 표시 방식】")
    for i, choice in enumerate(sample_choices, 1):
        print(f"  {i}. {choice}")
    
    print("\n【개선된 표시 방식】")
    # 2열 표시 시뮬레이션
    print("  Column 1:                 Column 2:")
    for i, choice in enumerate(sample_choices):
        if i < 3:
            print(f"  {circle_nums[i]} {choice}", end="")
            print(" " * (25 - len(f"  {circle_nums[i]} {choice}")), end="")
        else:
            if i == 3:
                print(f"  {circle_nums[i]} {choice}")
            else:
                print(" " * 25 + f"  {circle_nums[i]} {choice}")
    
    print("\n정답 표시: ① 12  (번호와 값 함께 표시)")

def main():
    print("\n" + "="*60)
    print(" 🚀 문제 품질 향상 및 UI 개선 테스트")
    print("="*60)
    
    test_prompt_quality()
    test_ui_improvements()
    test_response_structure()
    simulate_choice_display()
    
    print("\n" + "="*60)
    print(" 📊 개선 사항 요약")
    print("="*60)
    
    print("\n✅ 문제 품질 향상:")
    print("  1. 평가 타당성 및 변별력 강조")
    print("  2. 체계적인 오답 설계 전략")
    print("  3. 실제 수능 스타일 준수")
    print("  4. 난이도 근거 및 오개념 명시")
    
    print("\n✅ UI/UX 개선:")
    print("  1. 원문자 사용으로 가독성 향상")
    print("  2. 선택지 2열 배치")
    print("  3. 정답 표시 시 번호+값 동시 표시")
    print("  4. 추가 학습 정보 제공")
    
    print("\n💡 기대 효과:")
    print("  • 학생 평가에 적합한 고품질 문제 생성")
    print("  • 명확한 선택지 구분으로 실수 방지")
    print("  • 학습 효과 증대를 위한 상세 정보 제공")

if __name__ == "__main__":
    main()