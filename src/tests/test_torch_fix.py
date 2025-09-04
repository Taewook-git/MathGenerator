#!/usr/bin/env python3
"""
PyTorch 오류 해결 확인 테스트
"""

import sys
import os
# src 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import():
    """Import 테스트"""
    print("=" * 60)
    print("📚 Import 테스트")
    print("=" * 60)
    
    try:
        print("\n1. quality_validator 임포트 시도...")
        from validators.quality_validator import QualityEnhancedGenerator
        print("   ✓ quality_validator 임포트 성공")
        
        print("\n2. QualityEnhancedGenerator 초기화 시도...")
        generator = QualityEnhancedGenerator()
        print("   ✓ QualityEnhancedGenerator 초기화 성공")
        
        print("\n3. ProblemDatabase 초기화 확인...")
        from validators.quality_validator import ProblemDatabase
        db = ProblemDatabase()
        print("   ✓ ProblemDatabase 초기화 성공")
        print(f"   • Embeddings 사용: {db.use_embeddings}")
        print(f"   • Sentence model: {'없음 (Jaccard 유사도 사용)' if not db.sentence_model else '활성화됨'}")
        
        return True
        
    except Exception as e:
        print(f"\n   ✗ 오류 발생: {e}")
        return False

def test_similarity():
    """유사도 계산 테스트"""
    print("\n" + "=" * 60)
    print("🔍 유사도 계산 테스트")
    print("=" * 60)
    
    try:
        from validators.quality_validator import ProblemDatabase
        
        db = ProblemDatabase()
        
        # 테스트 문제들
        problem1 = {
            'question': '함수 f(x) = x² - 2x + 1의 최솟값을 구하시오.',
            'topic': '미분'
        }
        
        problem2 = {
            'question': '함수 g(x) = x² - 2x + 1에서 최소값은?',
            'topic': '미분'
        }
        
        problem3 = {
            'question': '삼각함수 sin(x)의 주기를 구하시오.',
            'topic': '삼각함수'
        }
        
        print("\n테스트 문제:")
        print("1. 함수 f(x) = x² - 2x + 1의 최솟값을 구하시오.")
        print("2. 함수 g(x) = x² - 2x + 1에서 최소값은?")
        print("3. 삼각함수 sin(x)의 주기를 구하시오.")
        
        # 유사도 계산
        sim1_2 = db._calculate_jaccard_similarity(
            problem1['question'], 
            problem2['question']
        )
        sim1_3 = db._calculate_jaccard_similarity(
            problem1['question'],
            problem3['question']
        )
        
        print(f"\n유사도 결과:")
        print(f"  • 문제 1 vs 문제 2: {sim1_2:.2%} (높아야 함)")
        print(f"  • 문제 1 vs 문제 3: {sim1_3:.2%} (낮아야 함)")
        
        if sim1_2 > sim1_3:
            print("\n✓ 유사도 계산이 올바르게 작동합니다.")
            return True
        else:
            print("\n⚠️ 유사도 계산 결과가 예상과 다릅니다.")
            return False
            
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        return False

def main():
    print("\n" + "="*60)
    print(" 🔧 PyTorch 오류 해결 확인")
    print("="*60)
    
    results = []
    
    # Import 테스트
    results.append(("Import 테스트", test_import()))
    
    # 유사도 테스트
    results.append(("유사도 계산", test_similarity()))
    
    print("\n" + "="*60)
    print(" 📊 테스트 결과 요약")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ 통과" if passed else "✗ 실패"
        print(f"  • {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print(" ✅ 모든 테스트 통과!")
        print("\n해결 내용:")
        print("  1. PyTorch 경고 메시지 억제")
        print("  2. Sentence transformer 임시 비활성화")
        print("  3. Jaccard 유사도로 대체 (안정적)")
        print("\n이제 torch.classes 오류 없이 정상 작동합니다.")
    else:
        print(" ⚠️ 일부 테스트 실패")
        print("\n추가 조치가 필요할 수 있습니다.")
    print("="*60)

if __name__ == "__main__":
    main()