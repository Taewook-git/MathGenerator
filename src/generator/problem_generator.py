"""
Gemini-2.5-Pro를 사용한 수학 문제 생성 모듈
2015 개정 교육과정 준수
"""
from typing import Dict, Any, List, Optional
from .gemini_client_v2 import GeminiClientV2
import json
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 프로젝트 루트 추가
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.core.curriculum_2015 import (
    CURRICULUM_2015, 
    CURRICULUM_COMPLIANCE,
    PROBLEM_GUIDELINES,
    validate_problem_curriculum
)


class ProblemGenerator:
    """수능 수학 문제 생성기"""
    
    def __init__(
        self,
        gemini_client: Optional[GeminiClientV2] = None,
        temperature: float = 0.8
    ):
        """
        Args:
            gemini_client: Gemini API 클라이언트
            temperature: 생성 다양성 (0.0~1.0)
        """
        self.client = gemini_client or GeminiClientV2(temperature=temperature)
        
    def generate_problem(
        self,
        subject: str,  # 수학1, 수학2, 미적분
        topic: str,
        difficulty: str,
        problem_type: str,
        points: int,
        reference_problems: Optional[List[Dict]] = None,
        exam_type: str = "공통"
    ) -> Dict[str, Any]:
        """
        단일 문제 생성
        
        Args:
            topic: 주제 (미적분, 확률과 통계 등)
            difficulty: 난이도 (하/중/상)
            problem_type: 문제 유형 (선택형/단답형)
            points: 배점 (2~4점)
            reference_problems: 참고 문제들
            exam_type: 시험 유형 (공통/미적분/확률과 통계/기하)
            
        Returns:
            생성된 문제 딕셔너리
        """
        # 교육과정 검증
        if subject not in CURRICULUM_2015:
            raise ValueError(f"과목 {subject}는 2015 개정 교육과정에 없습니다")
        
        prompt = self._create_generation_prompt(
            subject, topic, difficulty, problem_type, points, reference_problems, exam_type
        )
        
        # 교육과정 가이드라인 추가
        curriculum_guide = self._get_curriculum_guidelines(subject, topic, difficulty)
        
        system_prompt = f"""당신은 한국 대학수학능력시험 수학 문제 출제 전문가입니다.
2015 개정 교육과정을 철저히 준수하여 문제를 생성해주세요.

{curriculum_guide}

중요: 고난도 문제라도 반드시 2015 개정 교육과정 범위 내에서만 출제해야 합니다.
교육과정 외 개념을 사용하지 마세요.
반드시 {subject} 과목의 {topic} 내용만 사용하여 문제를 생성하세요.

【필수 응답 형식】
반드시 아래 JSON 형식으로만 응답하세요. 모든 필수 필드를 반드시 포함해야 합니다.
필드가 하나라도 누락되면 시스템이 작동하지 않습니다.

{{
    "question": "문제 지문 (필수, 반드시 포함)",
    "answer": "정답 (필수, 반드시 포함)",
    "topic": "{topic}",
    "difficulty": "{difficulty}",
    "type": "{problem_type}",
    "options": ["①...", "②...", "③...", "④...", "⑤..."] (선택형인 경우 필수 5개),
    "points": {points},
    "exam_type": "{exam_type}",
    "subject": "{subject}",
    "keywords": ["키워드1", "키워드2"] (최소 2개),
    "hint": "풀이 힌트"
}}

주의사항:
- question: {subject} 과목의 {topic}에 관한 문제를 작성하세요
- answer: 명확한 정답을 제시하세요
- topic: 반드시 "{topic}"로 설정
- difficulty: 반드시 "{difficulty}"로 설정
- type: 반드시 "{problem_type}"로 설정
- subject: 반드시 "{subject}"로 설정
- options: 선택형인 경우 반드시 5개의 선택지 제공"""
        
        result = self.client.generate(prompt, system_prompt)
        
        # 검증 및 후처리
        problem = self._validate_problem(result)
        
        # 교육과정 준수 검증
        problem["subject"] = subject
        validation = validate_problem_curriculum(
            subject, 
            problem.get("topic", topic),
            problem.get("keywords", [])
        )
        
        if not validation["valid"]:
            # 경고만 기록하고 계속 진행
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"교육과정 검증 경고: {validation['errors']}")
            problem["curriculum_check"] = validation["errors"]
            
        if validation["warnings"]:
            problem["curriculum_warnings"] = validation["warnings"]
            
        return problem
        
    def generate_exam(
        self,
        exam_type: str = "공통",
        num_problems: int = 30,
        reference_problems: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        전체 모의고사 생성
        
        Args:
            exam_type: 시험 유형 (공통/미적분/확률과 통계/기하)
            num_problems: 문제 수
            reference_problems: 참고 문제들
            
        Returns:
            문제 리스트
        """
        # 수능 형식에 맞는 문제 구성
        problem_config = self._get_exam_config(exam_type, num_problems)
        
        problems = []
        for config in problem_config:
            # 주제에 따라 과목 결정
            if exam_type in ["미적분", "확률과 통계", "기하"]:
                subject = exam_type
            else:
                # 공통의 경우 주제에 따라 수학1 또는 수학2 결정
                if config["topic"] in ["지수와 로그", "지수함수와 로그함수", "삼각함수", "수열"]:
                    subject = "수학1"
                else:
                    subject = "수학2"
            
            problem = self.generate_problem(
                subject=subject,
                topic=config["topic"],
                difficulty=config["difficulty"],
                problem_type=config["type"],
                points=config["points"],
                reference_problems=reference_problems,
                exam_type=exam_type
            )
            problem["number"] = config["number"]
            problems.append(problem)
            
        return problems
    
    def _create_generation_prompt(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        problem_type: str,
        points: int,
        reference_problems: Optional[List[Dict]],
        exam_type: str
    ) -> str:
        """문제 생성 프롬프트 생성"""
        prompt_parts = [
            f"다음 조건에 맞는 수학 문제를 생성해주세요:",
            f"- 과목: {subject}",
            f"- 주제: {topic}",
            f"- 난이도: {difficulty}",
            f"- 유형: {problem_type}",
            f"- 배점: {points}점",
            f"- 2015 개정 교육과정 준수: 필수",
            ""
        ]
        
        if reference_problems:
            prompt_parts.append("참고할 유사 문제들:")
            for i, ref in enumerate(reference_problems[:3], 1):
                prompt_parts.append(f"\n참고 문제 {i}:")
                if "question" in ref:
                    prompt_parts.append(f"문제: {ref['question']}")
                if "answer" in ref:
                    prompt_parts.append(f"정답: {ref['answer']}")
            prompt_parts.append("\n위 문제들을 참고하여 비슷한 스타일의 새로운 문제를 생성해주세요.")
            prompt_parts.append("단, 문제와 숫자는 완전히 다르게 만들어주세요.")
        
        if problem_type == "선택형":
            prompt_parts.append("\n5개의 선택지를 제공해주세요. (①~⑤)")
        else:
            prompt_parts.append("\n정답은 999 이하의 자연수여야 합니다.")
            
        return "\n".join(prompt_parts)
    
    def _validate_problem(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """생성된 문제 검증 및 보정"""
        # 필수 필드와 기본값
        field_defaults = {
            "question": "문제가 생성되지 않았습니다.",
            "answer": "정답 없음",
            "topic": "일반 수학",
            "difficulty": "중",
            "type": "선택형"
        }
        
        # 누락된 필드에 기본값 설정
        for field, default_value in field_defaults.items():
            if field not in problem or problem[field] is None:
                logger.warning(f"필드 '{field}'이(가) 누락되어 기본값으로 설정: {default_value}")
                problem[field] = default_value
                
        # 선택형 문제 검증
        if problem.get("type") == "선택형":
            if "options" not in problem or len(problem["options"]) != 5:
                # 기본 선택지 생성
                problem["options"] = ["①", "②", "③", "④", "⑤"]
                
        # 단답형 문제 검증
        elif problem.get("type") == "단답형":
            try:
                answer_val = int(problem["answer"])
                if answer_val < 0 or answer_val > 999:
                    problem["answer"] = str(abs(answer_val) % 1000)
            except (ValueError, TypeError):
                problem["answer"] = "1"  # 기본값
                
        return problem
    
    def _get_exam_config(
        self,
        exam_type: str,
        num_problems: int
    ) -> List[Dict[str, Any]]:
        """시험 문제 구성 생성 (2015 개정 교육과정 기준)"""
        
        # 2015 개정 교육과정 과목별 주제
        subjects_topics = {
            "수학1": list(CURRICULUM_2015["수학1"]["chapters"].keys()) if "수학1" in CURRICULUM_2015 else [],
            "수학2": list(CURRICULUM_2015["수학2"]["chapters"].keys()) if "수학2" in CURRICULUM_2015 else [],
            "미적분": list(CURRICULUM_2015["미적분"]["chapters"].keys()) if "미적분" in CURRICULUM_2015 else [],
            "확률과 통계": list(CURRICULUM_2015["확률과 통계"]["chapters"].keys()) if "확률과 통계" in CURRICULUM_2015 else [],
            "기하": list(CURRICULUM_2015["기하"]["chapters"].keys()) if "기하" in CURRICULUM_2015 else []
        }
        
        # 2015 개정 교육과정: 공통+선택 구조
        if exam_type == "공통":
            # 공통 과목: 수학1, 수학2
            all_topics = subjects_topics["수학1"] + subjects_topics["수학2"]
        elif exam_type == "미적분":
            # 선택 과목: 공통 + 미적분
            all_topics = subjects_topics["수학1"] + subjects_topics["수학2"] + subjects_topics["미적분"]
        elif exam_type == "확률과 통계":
            # 선택 과목: 공통 + 확률과 통계
            all_topics = subjects_topics["수학1"] + subjects_topics["수학2"] + subjects_topics["확률과 통계"]
        elif exam_type == "기하":
            # 선택 과목: 공통 + 기하
            all_topics = subjects_topics["수학1"] + subjects_topics["수학2"] + subjects_topics["기하"]
        else:
            # 기본값: 공통
            all_topics = subjects_topics["수학1"] + subjects_topics["수학2"]
        
        # 주제가 비어있으면 기본값 설정
        if not all_topics:
            all_topics = ["지수와 로그", "삼각함수", "수열", "함수의 극한", "미분", "적분"]
            
        config = []
        
        # 선택형 (1~21번)
        for i in range(1, min(22, num_problems + 1)):
            if i <= 5:
                difficulty = "하"
                points = 2
            elif i <= 15:
                difficulty = "중"
                points = 3
            else:
                difficulty = "상"
                points = 4
                
            config.append({
                "number": i,
                "topic": all_topics[i % len(all_topics)],
                "difficulty": difficulty,
                "type": "선택형",
                "points": points
            })
            
        # 단답형 (22~30번)
        for i in range(22, min(31, num_problems + 1)):
            if i <= 25:
                difficulty = "중"
                points = 3
            else:
                difficulty = "상"
                points = 4
                
            config.append({
                "number": i,
                "topic": all_topics[i % len(all_topics)],
                "difficulty": difficulty,
                "type": "단답형",
                "points": points
            })
            
        return config[:num_problems]
    
    def _get_curriculum_guidelines(self, subject: str, topic: str, difficulty: str) -> str:
        """교육과정 가이드라인 생성"""
        guidelines = []
        
        if subject in CURRICULUM_2015:
            curriculum = CURRICULUM_2015[subject]
            guidelines.append(f"과목: {subject}")
            guidelines.append(f"교육과정: {curriculum.get('description', '')}")
            
            # 주제별 세부 내용
            for chapter, details in curriculum.get("chapters", {}).items():
                if topic in chapter or topic in str(details.get("topics", [])):
                    guidelines.append(f"\n주제 '{topic}' 관련 내용:")
                    if "topics" in details:
                        for t in details["topics"]:
                            guidelines.append(f"  - {t}")
                    break
        
        # 난이도별 가이드
        if difficulty == "하":
            guidelines.append("\n난이도 하: 기본 개념 이해와 직접 적용")
        elif difficulty == "중":
            guidelines.append("\n난이도 중: 개념의 응용과 문제 해결")
        elif difficulty == "상":
            guidelines.append("\n난이도 상: 복합적 사고와 창의적 해결")
        
        return "\n".join(guidelines) if guidelines else "2015 개정 교육과정 준수"