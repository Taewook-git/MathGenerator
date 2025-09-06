"""
2015 개정 교육과정 특화 문제 생성 모듈
수학1, 수학2, 미적분 전용 생성기
"""
from typing import Dict, Any, List, Optional
from .problem_generator import ProblemGenerator
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.core.curriculum_2015 import (
    CURRICULUM_2015,
    PROBLEM_GUIDELINES,
    CURRICULUM_COMPLIANCE,
    validate_problem_curriculum,
    get_curriculum_info
)


class ProblemGenerator2015(ProblemGenerator):
    """2015 개정 교육과정 특화 문제 생성기"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subjects = ["수학1", "수학2", "미적분"]
        
    def generate_curriculum_problem(
        self,
        subject: str,
        chapter: str,
        section: Optional[str] = None,
        difficulty: str = "중",
        problem_type: str = "선택형"
    ) -> Dict[str, Any]:
        """
        교육과정 기반 문제 생성
        
        Args:
            subject: 과목명 (수학1/수학2/미적분)
            chapter: 대단원
            section: 소단원 (선택사항)
            difficulty: 난이도 (하/중/상)
            problem_type: 문제 유형 (선택형/단답형)
            
        Returns:
            생성된 문제
        """
        if subject not in CURRICULUM_2015:
            raise ValueError(f"{subject}는 지원되지 않는 과목입니다")
            
        chapter_data = CURRICULUM_2015[subject]["chapters"].get(chapter)
        if not chapter_data:
            raise ValueError(f"{subject}의 {chapter} 단원을 찾을 수 없습니다")
            
        # 배점 결정
        if difficulty == "하":
            points = 2
        elif difficulty == "중":
            points = 3
        else:  # 상
            points = 4
            
        # 핵심 개념과 제한사항 추출
        core_concepts = chapter_data.get("core_concepts", [])
        limits = chapter_data.get("curriculum_limits", [])
        
        # 교육과정 준수 프롬프트
        curriculum_prompt = self._create_curriculum_prompt(
            subject, chapter, section, core_concepts, limits, difficulty
        )
        
        # 문제 생성
        problem = self.generate_problem(
            subject=subject,
            topic=section or chapter,
            difficulty=difficulty,
            problem_type=problem_type,
            points=points
        )
        
        # 추가 메타데이터
        problem["chapter"] = chapter
        problem["section"] = section
        problem["curriculum_concepts"] = core_concepts[:3]  # 주요 개념 3개
        
        return problem
        
    def generate_unit_test(
        self,
        subject: str,
        chapter: str,
        num_problems: int = 10
    ) -> List[Dict[str, Any]]:
        """
        단원 평가 문제 세트 생성
        
        Args:
            subject: 과목명
            chapter: 단원명
            num_problems: 문제 수
            
        Returns:
            문제 리스트
        """
        if subject not in CURRICULUM_2015:
            raise ValueError(f"{subject}는 지원되지 않는 과목입니다")
            
        chapter_data = CURRICULUM_2015[subject]["chapters"].get(chapter)
        if not chapter_data:
            raise ValueError(f"{chapter} 단원을 찾을 수 없습니다")
            
        sections = chapter_data.get("sections", [])
        problems = []
        
        # 난이도 분포 (30% 하, 50% 중, 20% 상)
        difficulty_dist = {
            "하": int(num_problems * 0.3),
            "중": int(num_problems * 0.5),
            "상": num_problems - int(num_problems * 0.3) - int(num_problems * 0.5)
        }
        
        problem_count = 0
        for difficulty, count in difficulty_dist.items():
            for _ in range(count):
                # 섹션 순환
                section = sections[problem_count % len(sections)] if sections else None
                
                # 문제 유형 (70% 선택형, 30% 단답형)
                problem_type = "선택형" if problem_count < num_problems * 0.7 else "단답형"
                
                problem = self.generate_curriculum_problem(
                    subject=subject,
                    chapter=chapter,
                    section=section,
                    difficulty=difficulty,
                    problem_type=problem_type
                )
                
                problem["number"] = problem_count + 1
                problems.append(problem)
                problem_count += 1
                
        return problems
        
    def generate_integrated_problem(
        self,
        subjects: List[str],
        difficulty: str = "상"
    ) -> Dict[str, Any]:
        """
        과목 융합 문제 생성
        
        Args:
            subjects: 융합할 과목 리스트
            difficulty: 난이도
            
        Returns:
            융합 문제
        """
        # 유효한 과목만 필터링
        valid_subjects = [s for s in subjects if s in self.subjects]
        if not valid_subjects:
            raise ValueError("유효한 과목이 없습니다")
            
        # 융합 주제 선택
        if "수학1" in valid_subjects and "수학2" in valid_subjects:
            topic = "지수함수와 로그함수의 미분"
        elif "수학2" in valid_subjects and "미적분" in valid_subjects:
            topic = "미적분학의 심화 응용"
        else:
            topic = "종합 문제"
            
        # 융합 문제 생성
        problem = self.generate_problem(
            subject="+".join(valid_subjects),
            topic=topic,
            difficulty=difficulty,
            problem_type="단답형",  # 융합 문제는 주로 단답형
            points=4  # 고정 4점
        )
        
        problem["integrated"] = True
        problem["subjects"] = valid_subjects
        
        return problem
        
    def _create_curriculum_prompt(
        self,
        subject: str,
        chapter: str,
        section: Optional[str],
        core_concepts: List[str],
        limits: List[str],
        difficulty: str
    ) -> str:
        """교육과정 준수 프롬프트 생성"""
        
        guidelines = PROBLEM_GUIDELINES.get(subject, {}).get(
            chapter.replace(" ", "_"), {}
        )
        
        prompt_parts = [
            f"[2015 개정 교육과정 {subject} - {chapter}]",
            "",
            "핵심 개념:",
        ]
        
        for concept in core_concepts[:5]:
            prompt_parts.append(f"- {concept}")
            
        prompt_parts.append("")
        prompt_parts.append("교육과정 제한사항:")
        for limit in limits:
            prompt_parts.append(f"- {limit}")
            
        if difficulty in guidelines:
            prompt_parts.append("")
            prompt_parts.append(f"{difficulty} 난이도 가이드:")
            prompt_parts.append(guidelines[difficulty])
            
        # 금지 사항 명시
        if "금지" in guidelines:
            prompt_parts.append("")
            prompt_parts.append("절대 사용하지 말아야 할 개념:")
            prompt_parts.append(f"- {guidelines['금지']}")
            
        prompt_parts.append("")
        prompt_parts.append("중요: 위 제한사항을 반드시 준수하여 문제를 생성하세요.")
        
        return "\n".join(prompt_parts)
        
    def _get_curriculum_guidelines(
        self,
        subject: str,
        topic: str,
        difficulty: str
    ) -> str:
        """교육과정 가이드라인 생성"""
        
        # 기본 준수 사항
        guidelines = [
            "[2015 개정 교육과정 준수 사항]",
            ""
        ]
        
        # 필수 준수 사항
        for item in CURRICULUM_COMPLIANCE["필수_준수_사항"]:
            guidelines.append(f"✓ {item}")
            
        guidelines.append("")
        guidelines.append("[금지 사항]")
        
        # 금지 사항
        for item in CURRICULUM_COMPLIANCE["금지_사항"]:
            guidelines.append(f"✗ {item}")
            
        # 고난도 문제 원칙
        if difficulty == "상":
            guidelines.append("")
            guidelines.append("[고난도 문제 작성 원칙]")
            for item in CURRICULUM_COMPLIANCE["고난도_문제_원칙"]:
                guidelines.append(f"• {item}")
                
        return "\n".join(guidelines)
        
    def validate_generated_problem(
        self,
        problem: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        생성된 문제의 교육과정 준수 여부 검증
        
        Args:
            problem: 생성된 문제
            
        Returns:
            검증 결과
        """
        subject = problem.get("subject", "")
        topic = problem.get("topic", "")
        keywords = problem.get("keywords", [])
        question = problem.get("question", "")
        
        # 기본 검증
        validation = validate_problem_curriculum(subject, topic, keywords)
        
        # 추가 검증: 문제 텍스트에서 금지된 용어 확인
        forbidden_terms = {
            "수학1": ["극한", "미분", "적분", "역삼각함수"],
            "수학2": ["치환적분", "부분적분", "테일러", "매개변수"],
            "미적분": ["편미분", "중적분", "벡터장", "발산정리"]
        }
        
        if subject in forbidden_terms:
            for term in forbidden_terms[subject]:
                if term in question:
                    validation["valid"] = False
                    validation["errors"].append(
                        f"문제에 교육과정 외 용어 '{term}'이(가) 포함되어 있습니다"
                    )
                    
        return validation