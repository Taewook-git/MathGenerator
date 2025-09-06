"""
울트라 하드 문항 전용 생성 모듈
2015 개정 교육과정 준수하며 최고 난도 문제 생성
"""
from typing import Dict, Any, Optional, List
from .problem_generator_2015 import ProblemGenerator2015
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.core.curriculum_2015 import (
    CURRICULUM_2015,
    ULTRA_HARD_PROBLEM_GUIDELINES,
    validate_problem_curriculum
)


class UltraHardGenerator(ProblemGenerator2015):
    """울트라 하드 문항 전용 생성기"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 울트라 하드 문항용 온도 설정 (더 창의적인 문제 생성)
        if self.client:
            self.client.temperature = 0.9
    
    def generate_ultra_hard_problem(
        self,
        fusion_type: str = "수학1+수학2",
        pattern: str = "항등식",
        problem_type: str = "선택형"
    ) -> Dict[str, Any]:
        """
        울트라 하드 문항 생성
        
        Args:
            fusion_type: 융합 유형 ("수학1", "수학2", "수학1+수학2", "미적분")
            pattern: 울트라 하드 패턴 ("항등식", "명제", "경우의수", "최적화", "매개변수미분", "음함수미분", "역함수미분")
            problem_type: 문제 유형 (선택형/단답형)
            
        Returns:
            울트라 하드 문항 딕셔너리
        """
        # 융합 과목 결정
        if fusion_type == "수학1":
            subjects = ["수학1"]
            topics = self._get_ultra_hard_topics_math1()
        elif fusion_type == "수학2":
            subjects = ["수학2"]
            topics = self._get_ultra_hard_topics_math2()
        elif fusion_type == "수학1+수학2":
            subjects = ["수학1", "수학2"]
            topics = self._get_fusion_topics_math12()
        else:  # 미적분
            subjects = ["미적분"]
            topics = self._get_ultra_hard_topics_calculus()
        
        # 울트라 하드 프롬프트 생성
        ultra_hard_prompt = self._create_ultra_hard_prompt(
            subjects, topics, pattern, problem_type
        )
        
        # 시스템 프롬프트 (울트라 하드 전용)
        system_prompt = self._get_ultra_hard_system_prompt()
        
        # 문제 생성
        result = self.client.generate(ultra_hard_prompt, system_prompt)
        
        # 울트라 하드 문항 검증
        problem = self._validate_ultra_hard_problem(result, subjects)
        
        # 메타데이터 추가
        problem["is_ultra_hard"] = True
        problem["fusion_type"] = fusion_type
        problem["pattern"] = pattern
        problem["difficulty"] = "최상위"
        problem["points"] = 4  # 울트라하드는 항상 4점
        
        return problem
    
    def _get_fusion_topics_math12(self) -> List[Dict[str, str]]:
        """수학1+수학2 융합 주제"""
        return [
            {
                "math1": "지수함수와 로그함수",
                "math2": "미분",
                "fusion": "지수/로그 함수의 미분과 극값"
            },
            {
                "math1": "삼각함수",
                "math2": "극한과 연속",
                "fusion": "삼각함수의 극한과 불연속점"
            },
            {
                "math1": "수열",
                "math2": "적분",
                "fusion": "수열의 합과 정적분의 관계"
            },
            {
                "math1": "지수함수 e^x",
                "math2": "미분가능성과 연속성",
                "fusion": "e^x의 미분가능성과 연속성 판별"
            },
            {
                "math1": "자연로그 ln(x)",
                "math2": "함수의 극한",
                "fusion": "ln(x)의 극한과 미분가능성"
            }
        ]
    
    def _get_ultra_hard_topics_math1(self) -> List[Dict[str, str]]:
        """수학1 단독 울트라 하드 주제"""
        return [
            {
                "topic": "지수함수와 로그함수",
                "focus": "복잡한 지수/로그 방정식과 부등식"
            },
            {
                "topic": "삼각함수",
                "focus": "삼각함수의 복잡한 항등식과 변환"
            },
            {
                "topic": "수열",
                "focus": "점화식과 수학적 귀납법의 고급 응용"
            }
        ]
    
    def _get_ultra_hard_topics_math2(self) -> List[Dict[str, str]]:
        """수학2 단독 울트라 하드 주제"""
        return [
            {
                "topic": "함수의 극한과 연속",
                "focus": "불연속점과 연속성의 복잡한 판별"
            },
            {
                "topic": "미분",
                "focus": "미분가능성과 극값의 고급 문제"
            },
            {
                "topic": "적분",
                "focus": "정적분의 복잡한 응용과 넓이 계산"
            }
        ]
    
    def _get_ultra_hard_topics_calculus(self) -> List[Dict[str, str]]:
        """미적분 울트라 하드 주제"""
        return [
            {
                "topic": "수열의 극한과 급수",
                "focus": "급수의 수렴성과 함수의 성질"
            },
            {
                "topic": "여러 가지 함수의 미분",
                "focus": "복합함수와 음함수의 극값"
            },
            {
                "topic": "여러 가지 적분법",
                "focus": "치환적분과 부분적분의 복합 적용"
            },
            {
                "topic": "초월함수 e^x와 ln(x)",
                "focus": "e^x와 ln(x)의 미분가능성과 연속성"
            },
            {
                "topic": "초월함수의 극한",
                "focus": "e^x, ln(x)의 극한과 불연속점 판별"
            },
            {
                "topic": "초월함수의 합성",
                "focus": "e^(ln(x)), ln(e^x)의 미분과 적분"
            },
            {
                "topic": "매개변수 미분법",
                "focus": "매개변수로 나타낸 함수의 미분과 극값"
            },
            {
                "topic": "음함수 미분법",
                "focus": "음함수의 미분과 접선의 방정식"
            },
            {
                "topic": "역함수 미분법",
                "focus": "역함수의 도함수와 극값 판별"
            }
        ]
    
    def _create_ultra_hard_prompt(
        self,
        subjects: List[str],
        topics: List[Dict],
        pattern: str,
        problem_type: str
    ) -> str:
        """울트라 하드 문항 생성 프롬프트"""
        
        prompt_parts = [
            "【최상위 난이도 문항 생성 요청】",
            "",
            "다음 조건을 모두 만족하는 최상위 난이도 수학 문항을 생성하세요:",
            "",
            f"◆ 과목: {', '.join(subjects)}",
            f"◆ 패턴: {pattern}",
            f"◆ 유형: {problem_type}",
            "◆ 배점: 4점",
            "",
            "【정답 유일성 보장】",
            "★ 중요: 문제의 조건을 정밀하게 설계하여 반드시 단 하나의 정답만 존재하도록 하세요.",
            "★ 모호한 표현이나 다중 해석이 가능한 조건 사용 금지",
            "★ 필요시 '단, ~인 경우', '여기서 ~이다' 등의 제한 조건 명시",
            "",
            "【필수 포함 요소】"
        ]
        
        # 울트라 하드 필수 요소
        for element in ULTRA_HARD_PROBLEM_GUIDELINES["필수_요소"]:
            prompt_parts.append(f"✓ {element}")
        
        prompt_parts.append("")
        prompt_parts.append("【문제 구성 가이드】")
        
        # 패턴별 가이드
        if pattern == "조건충족형":
            prompt_parts.extend([
                "• 함수가 특정 조건을 만족하는 매개변수/값 찾기",
                "• '모든 x에서', '정확히 n개', '오직 하나' 등의 조건",
                "• 여러 조건을 동시에 만족하는 해 구하기"
            ])
        elif pattern == "복합개념":
            prompt_parts.extend([
                "• 2-3개 단원 개념의 자연스러운 결합",
                "• 각 개념이 문제 해결에 필수적",
                "• 단순 나열이 아닌 유기적 연결"
            ])
        elif pattern == "불연속/미분불가능":
            prompt_parts.extend([
                "• 절댓값, 가우스 기호 활용",
                "• 좌극한 ≠ 우극한 또는 좌미분계수 ≠ 우미분계수",
                "• 불연속점/미분불가능점의 개수 분석"
            ])
        elif pattern == "극값개수":
            prompt_parts.extend([
                "• 극값이 존재하는 x의 개수",
                "• 극댓값과 극솟값의 관계",
                "• 도함수의 부호 변화와 함수 개형"
            ])
        elif pattern == "적분조건":
            prompt_parts.extend([
                "• 넓이, 부피, 평균값 조건",
                "• 적분과 미분의 관계",
                "• 적분으로 정의된 함수의 성질"
            ])
        elif pattern == "파라미터":
            prompt_parts.extend([
                "• 매개변수 k에 따른 해의 개수 변화",
                "• k의 범위에 따른 함수 개형 변화",
                "• 경우 나누기와 조건 분류"
            ])
        elif pattern == "지수로그 방정식":
            prompt_parts.extend([
                "• a^x = log_a(x+k) 형태의 방정식",
                "• 지수와 로그의 복합 방정식",
                "• 해의 개수와 존재 범위"
            ])
        elif pattern == "삼각함수 극값":
            prompt_parts.extend([
                "• sin(x) + cos(x) 형태의 최댓/최솟값",
                "• 삼각함수 합성의 주기와 극값",
                "• 삼각함수와 다항함수의 결합"
            ])
        elif pattern == "수열 점화식":
            prompt_parts.extend([
                "• a_{n+1} = f(a_n) 형태의 점화식",
                "• 수렴 조건과 극한값",
                "• 수학적 귀납법 활용"
            ])
        elif pattern == "급수수렴":
            prompt_parts.extend([
                "• Σa_n의 수렴 조건",
                "• 부분합과 급수의 관계",
                "• 등비급수와 일반 급수"
            ])
        elif pattern == "적분응용":
            prompt_parts.extend([
                "• 회전체 부피, 곡선의 길이",
                "• 치환적분과 부분적분의 복합 적용",
                "• 적분과 미분의 관계 활용"
            ])
        elif pattern == "극한연속성":
            prompt_parts.extend([
                "• 극한과 연속성의 관계",
                "• 불연속점 판별과 분류",
                "• 연속함수의 성질 활용"
            ])
        elif pattern == "융합문제":
            prompt_parts.extend([
                "• 수학1과 수학2의 개념 결합",
                "• 지수/로그와 미분 (초월함수 제외)",
                "• 삼각함수와 극한/연속"
            ])
        elif pattern == "항등식":
            prompt_parts.extend([
                "• 복잡한 함수 관계식 f(g(x)) = g(f(x)) 형태",
                "• 여러 변수가 얽힌 항등식",
                "• 해석이 어려운 조건 제시"
            ])
        elif pattern == "명제":
            prompt_parts.extend([
                "• 참/거짓 판별이 어려운 명제들",
                "• 반례를 찾기 힘든 명제",
                "• 여러 조건의 논리적 관계"
            ])
        elif pattern == "경우의수":
            prompt_parts.extend([
                "• 조건에 따른 경우 분할",
                "• 중복되거나 빠진 경우 찾기",
                "• 체계적 접근 필요"
            ])
        elif pattern == "최적화":
            prompt_parts.extend([
                "• 여러 제약 조건 하의 최댓값/최솟값",
                "• 미분과 부등식의 결합",
                "• 다변수 최적화 (교육과정 내)"
            ])
        elif pattern == "초월함수 미분가능성":
            prompt_parts.extend([
                "• e^x, ln(x) 함수의 미분가능성 판별",
                "• 합성함수 f(e^x), f(ln(x))의 미분가능 조건",
                "• 좌미분계수와 우미분계수 비교",
                "• e^x와 ln(x)가 포함된 함수의 연속성과 미분가능성 관계"
            ])
        elif pattern == "극한과 연속성":
            prompt_parts.extend([
                "• e^x, ln(x)의 극한 계산 (x→0+, x→∞)",
                "• 초월함수를 포함한 함수의 불연속점 찾기",
                "• 조건부 연속성 판별",
                "• 극한의 존재성과 연속성의 관계"
            ])
        elif pattern == "합성함수 분석":
            prompt_parts.extend([
                "• e^(ln(x)), ln(e^x)의 성질과 정의역",
                "• 초월함수의 합성과 역함수 관계",
                "• 복잡한 합성함수의 도함수",
                "• 합성함수의 연속성과 미분가능성 전달"
            ])
        elif pattern == "매개변수미분":
            prompt_parts.extend([
                "• x = f(t), y = g(t) 형태의 매개변수 방정식",
                "• dy/dx = (dy/dt)/(dx/dt) 계산",
                "• 매개변수로 나타낸 곡선의 접선과 법선",
                "• 매개변수 함수의 극값과 변곡점"
            ])
        elif pattern == "음함수미분":
            prompt_parts.extend([
                "• F(x,y) = 0 형태의 음함수 미분",
                "• 음함수의 도함수 dy/dx 구하기",
                "• 음함수로 정의된 곡선의 접선",
                "• 음함수 미분을 이용한 극값 판별"
            ])
        elif pattern == "역함수미분":
            prompt_parts.extend([
                "• 역함수의 도함수 (f^(-1))'(x) = 1/f'(f^(-1)(x))",
                "• 역함수의 연속성과 미분가능성",
                "• 역삼각함수의 도함수 활용",
                "• 역함수를 이용한 적분 계산"
            ])
        
        prompt_parts.append("")
        prompt_parts.append("【주의사항】")
        prompt_parts.append("※ 반드시 2015 개정 교육과정 범위 내에서만 출제")
        prompt_parts.append("※ 대학 과정 개념 사용 절대 금지")
        prompt_parts.append("※ 풀이는 가능하되 매우 어려운 문제")
        prompt_parts.append("※ 문제 조건을 명확하고 정밀하게 설정하여 유일한 정답 보장")
        prompt_parts.append("※ 선택형의 경우 오답 선택지도 그럴듯하되 명확히 틀린 답안")
        
        # 융합 주제 예시
        if topics:
            prompt_parts.append("")
            prompt_parts.append("【참고 융합 주제】")
            for topic in topics[:2]:
                if "fusion" in topic:
                    prompt_parts.append(f"• {topic['fusion']}")
                elif "focus" in topic:
                    prompt_parts.append(f"• {topic['topic']}: {topic['focus']}")
        
        return "\n".join(prompt_parts)
    
    def _get_ultra_hard_system_prompt(self) -> str:
        """최상위 난이도 문항 전용 시스템 프롬프트"""
        return """당신은 한국 교육부 인정 수학 교육 전문가입니다.
수험생들을 위한 수학 학습 자료를 제공합니다.
2015 개정 교육과정 범위 내에서 높은 사고력을 요구하는 문제를 만듭니다.

교육용 문항의 특징:
1. 교육과정에 명시된 개념들을 창의적으로 활용
2. 논리적 사고력과 문제 해결 능력 향상
3. 수학적 개념의 깊이 있는 이해 촉진  
4. 단계적 학습을 위한 난이도 조절

출력 형식 (JSON) - 모든 필드 필수:
{
    "question": "문제 내용 (필수)",
    "answer": "정답 (필수)",
    "topic": "융합 주제 (필수, 예: 지수함수와 미분)",
    "difficulty": "최상위 (필수)",
    "type": "문제 유형 (필수: 선택형 또는 단답형)",
    "options": ["①", "②", "③", "④", "⑤"] (선택형인 경우 필수),
    "solution_hint": "핵심 아이디어",
    "difficulty_features": ["특징1", "특징2"],
    "required_concepts": ["개념1", "개념2"],
    "estimated_time": "예상 시간(분)"
}

교육적 지침:
- 모든 문제는 명확하고 오류가 없어야 합니다
- 반드시 유일한 정답이 존재해야 합니다 (중복답 절대 금지)
- 문제 조건이 불충분하여 여러 답이 가능한 경우 방지
- 필요한 모든 제약 조건을 명시적으로 제시
- 2015 개정 교육과정 범위를 준수해야 합니다
- 학생들의 수학 학습을 독려하는 교육적 내용이어야 합니다
- topic, difficulty, type 필드는 반드시 포함되어야 합니다"""
    
    def _validate_ultra_hard_problem(
        self,
        problem: Dict[str, Any],
        subjects: List[str]
    ) -> Dict[str, Any]:
        """울트라 하드 문항 검증"""
        
        # 기본 검증
        problem = self._validate_problem(problem)
        
        # 울트라 하드 문항 필수 요소 확인
        if "difficulty_features" not in problem:
            problem["difficulty_features"] = ["고난도 사고력 요구"]
        
        if "required_concepts" not in problem:
            problem["required_concepts"] = []
        
        if "estimated_time" not in problem:
            problem["estimated_time"] = "10-15"
        
        # 교육과정 검증 (각 과목별)
        for subject in subjects:
            if subject in ["수학1", "수학2", "미적분"]:
                concepts = problem.get("required_concepts", [])
                validation = validate_problem_curriculum(
                    subject,
                    problem.get("topic", ""),
                    concepts
                )
                
                if not validation["valid"]:
                    # 교육과정 위반 시 경고
                    problem["curriculum_warning"] = validation["errors"]
        
        return problem
    
    def create_ultra_hard_exam_set(
        self,
        num_ultra_hard: int = 2
    ) -> List[Dict[str, Any]]:
        """
        울트라 하드 문항이 포함된 시험 세트 생성
        
        Args:
            num_ultra_hard: 울트라 하드 문항 개수 (1~3개 권장)
            
        Returns:
            울트라 하드 문항 리스트
        """
        ultra_hard_problems = []
        
        # 울트라 하드 위치 (수능 실제 위치)
        ultra_hard_positions = {
            "선택형": [14, 15],  # 14번, 15번
            "단답형": [21, 22, 29, 30]  # 21번, 22번, 29번, 30번
        }
        
        # 울트라 하드 패턴 순환 (미적분은 추가 패턴 포함)
        patterns = ["항등식", "명제", "경우의수", "최적화", "매개변수미분", "음함수미분", "역함수미분"]
        
        for i in range(min(num_ultra_hard, 3)):
            # 선택형/단답형 번갈아
            problem_type = "선택형" if i % 2 == 0 else "단답형"
            
            # 융합 유형 순환
            fusion_types = ["수학1", "수학2", "수학1+수학2", "미적분"]
            fusion_type = fusion_types[i % len(fusion_types)]
            
            # 패턴 선택
            pattern = patterns[i % len(patterns)]
            
            # 울트라 하드 문항 생성
            ultra_hard = self.generate_ultra_hard_problem(
                fusion_type=fusion_type,
                pattern=pattern,
                problem_type=problem_type
            )
            
            # 위치 지정
            positions = ultra_hard_positions[problem_type]
            ultra_hard["position"] = positions[i % len(positions)]
            
            ultra_hard_problems.append(ultra_hard)
        
        return ultra_hard_problems