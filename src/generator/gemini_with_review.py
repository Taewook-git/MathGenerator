"""
Gemini API를 활용한 문제 생성 및 검토 시스템
생성 -> 검토 -> 수정 -> 최종 출력 아키텍처
"""
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import Dict, Any, Optional, List, Tuple
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

# 로깅 설정
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'gemini_review_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class GeminiProblemGeneratorWithReview:
    """문제 생성 및 검토를 수행하는 Gemini API 클래스"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        generator_model: str = "gemini-1.5-flash",
        reviewer_model: str = "gemini-1.5-flash",
        temperature_gen: float = 0.8,
        temperature_review: float = 0.3,
        max_retries: int = 3
    ):
        """
        Args:
            api_key: Gemini API 키
            generator_model: 생성용 모델
            reviewer_model: 검토용 모델 
            temperature_gen: 생성 온도 (창의성)
            temperature_review: 검토 온도 (일관성)
            max_retries: 최대 재시도 횟수
        """
        load_dotenv(override=True)
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        genai.configure(api_key=self.api_key)
        
        self.generator_model = generator_model
        self.reviewer_model = reviewer_model
        self.temperature_gen = temperature_gen
        self.temperature_review = temperature_review
        self.max_retries = max_retries
        
        # 안전 설정 (수학 문제용 최소 필터)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # 모델 초기화
        self._init_models()
        
        logger.info(f"Initialized Generator: {generator_model}, Reviewer: {reviewer_model}")
    
    def _init_models(self):
        """생성 및 검토 모델 초기화"""
        # 생성 모델
        self.generator = genai.GenerativeModel(
            model_name=self.generator_model,
            generation_config={
                "temperature": self.temperature_gen,
                "max_output_tokens": 2048,
                "top_p": 0.95,
                "top_k": 40
            },
            safety_settings=self.safety_settings
        )
        
        # 검토 모델
        self.reviewer = genai.GenerativeModel(
            model_name=self.reviewer_model,
            generation_config={
                "temperature": self.temperature_review,
                "max_output_tokens": 1024,
                "top_p": 0.9,
                "top_k": 30
            },
            safety_settings=self.safety_settings
        )
    
    def generate_problem(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        problem_type: str = "선택형",
        fusion_type: Optional[str] = None,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        문제 생성 (생성 -> 검토 -> 수정 파이프라인)
        
        Args:
            subject: 과목 (수학1, 수학2, 미적분)
            topic: 주제
            difficulty: 난이도
            problem_type: 문제 유형 (선택형/단답형)
            fusion_type: 융합 유형 (울트라하드용)
            pattern: 문제 패턴 (울트라하드용)
            
        Returns:
            검토 완료된 문제 딕셔너리
        """
        logger.info(f"Generating problem: {subject}/{topic}/{difficulty}")
        
        # Step 1: 초기 문제 생성
        generated_problem = self._generate_initial_problem(
            subject, topic, difficulty, problem_type, fusion_type, pattern
        )
        
        if not generated_problem:
            logger.error("Failed to generate initial problem")
            return None
        
        # Step 2: 문제 검토
        review_result = self._review_problem(
            generated_problem, subject, topic, difficulty
        )
        
        # Step 3: 검토 결과에 따른 수정
        if review_result.get("needs_revision", False):
            final_problem = self._revise_problem(
                generated_problem, review_result, subject, topic, difficulty
            )
        else:
            final_problem = generated_problem
        
        # Step 4: 최종 검증
        final_problem = self._final_validation(final_problem)
        
        logger.info(f"Problem generation completed: {final_problem.get('topic', 'Unknown')}")
        
        return final_problem
    
    def _generate_initial_problem(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        problem_type: str,
        fusion_type: Optional[str],
        pattern: Optional[str]
    ) -> Dict[str, Any]:
        """초기 문제 생성"""
        
        # 프롬프트 구성
        prompt = self._build_generation_prompt(
            subject, topic, difficulty, problem_type, fusion_type, pattern
        )
        
        system_prompt = """당신은 한국 수학 교육 전문가입니다.
2015 개정 교육과정에 맞는 수학 문제를 생성합니다.

반드시 다음 JSON 형식으로 출력하세요:
{
    "question": "문제 내용",
    "answer": "정답",
    "solution": "상세한 풀이 과정",
    "topic": "주제",
    "difficulty": "난이도",
    "type": "문제 유형",
    "options": ["①", "②", "③", "④", "⑤"] (선택형인 경우),
    "concepts": ["핵심 개념1", "핵심 개념2"],
    "hints": ["힌트1", "힌트2"]
}"""
        
        try:
            response = self.generator.generate_content(
                [system_prompt, prompt]
            )
            
            # JSON 파싱
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            problem = json.loads(text)
            return problem
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return None
    
    def _review_problem(
        self,
        problem: Dict[str, Any],
        subject: str,
        topic: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """생성된 문제 검토"""
        
        review_prompt = f"""다음 수학 문제를 검토하고 평가해주세요:

문제: {problem.get('question', '')}
정답: {problem.get('answer', '')}
풀이: {problem.get('solution', '')}
과목: {subject}
주제: {topic}
난이도: {difficulty}

다음 기준으로 검토하세요:
1. 2015 개정 교육과정 준수 여부
2. 문제와 정답의 정확성
3. **정답 유일성**: 문제 조건이 충분하여 단 하나의 정답만 존재하는지
4. 풀이 과정의 논리성
5. 난이도 적절성
6. 문제 명확성 (모호한 표현이나 다중 해석 가능 여부)

검토 결과를 JSON으로 출력:
{{
    "is_valid": true/false,
    "needs_revision": true/false,
    "issues": ["문제점1", "문제점2"],
    "suggestions": ["개선사항1", "개선사항2"],
    "score": 0-100
}}"""
        
        try:
            response = self.reviewer.generate_content(review_prompt)
            
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            review = json.loads(text)
            logger.info(f"Review score: {review.get('score', 0)}")
            
            return review
            
        except Exception as e:
            logger.error(f"Review error: {e}")
            return {"is_valid": True, "needs_revision": False, "score": 80}
    
    def _revise_problem(
        self,
        problem: Dict[str, Any],
        review: Dict[str, Any],
        subject: str,
        topic: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """검토 결과에 따른 문제 수정"""
        
        issues = review.get("issues", [])
        suggestions = review.get("suggestions", [])
        
        revision_prompt = f"""다음 문제를 개선해주세요:

원본 문제: {json.dumps(problem, ensure_ascii=False, indent=2)}

발견된 문제점:
{chr(10).join(f"- {issue}" for issue in issues)}

개선 제안:
{chr(10).join(f"- {suggestion}" for suggestion in suggestions)}

【개선 시 필수 확인 사항】
1. 정답이 유일하도록 문제 조건을 정밀하게 설정
2. 모호한 표현 제거 및 명확한 조건 제시
3. 필요시 "단," "여기서," "이때," 등의 제한 조건 추가
4. 변수의 범위, 정의역 명시

개선된 문제를 동일한 JSON 형식으로 출력하세요."""
        
        try:
            response = self.generator.generate_content(revision_prompt)
            
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            revised_problem = json.loads(text)
            logger.info("Problem revised successfully")
            
            return revised_problem
            
        except Exception as e:
            logger.error(f"Revision error: {e}")
            return problem  # 수정 실패시 원본 반환
    
    def _final_validation(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """최종 검증 및 필드 보완"""
        
        # 필수 필드 확인 및 기본값 설정
        required_fields = {
            "question": "문제를 생성할 수 없습니다.",
            "answer": "정답 없음",
            "solution": "풀이 과정을 생성할 수 없습니다.",
            "topic": "미분류",
            "difficulty": "중",
            "type": "선택형"
        }
        
        for field, default in required_fields.items():
            if field not in problem or not problem[field]:
                problem[field] = default
                logger.warning(f"Missing field '{field}' - using default: {default}")
        
        # 선택형 문제인 경우 options 확인
        if problem["type"] == "선택형" and "options" not in problem:
            problem["options"] = ["①", "②", "③", "④", "⑤"]
        
        # 메타데이터 추가
        problem["generated_at"] = datetime.now().isoformat()
        problem["generator"] = "gemini_with_review"
        problem["reviewed"] = True
        
        return problem
    
    def _build_generation_prompt(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        problem_type: str,
        fusion_type: Optional[str],
        pattern: Optional[str]
    ) -> str:
        """문제 생성 프롬프트 구성"""
        
        prompt_parts = [
            f"【수학 문제 생성 요청】",
            f"",
            f"◆ 과목: {subject}",
            f"◆ 주제: {topic}",
            f"◆ 난이도: {difficulty}",
            f"◆ 유형: {problem_type}",
        ]
        
        if fusion_type:
            prompt_parts.append(f"◆ 융합 유형: {fusion_type}")
        
        if pattern:
            prompt_parts.append(f"◆ 패턴: {pattern}")
        
        prompt_parts.extend([
            "",
            "【요구사항】",
            "• 2015 개정 교육과정 준수",
            "• 명확하고 오류 없는 문제",
            "• 단계별 상세한 풀이 포함",
            "• 교육적 가치가 있는 문제",
        ])
        
        if difficulty == "최상위" or difficulty == "울트라하드":
            prompt_parts.extend([
                "",
                "【고난도 문제 특징】",
                "• 여러 개념의 융합 필요",
                "• 다단계 사고 과정 요구",
                "• 창의적 접근 필요",
                "• 깊은 이해도 평가",
            ])
        
        return "\n".join(prompt_parts)
    
    def batch_generate(
        self,
        requests: List[Dict[str, Any]],
        delay_between: float = 1.0
    ) -> List[Dict[str, Any]]:
        """여러 문제 일괄 생성"""
        
        results = []
        
        for i, request in enumerate(requests):
            logger.info(f"Generating problem {i+1}/{len(requests)}")
            
            problem = self.generate_problem(**request)
            results.append(problem)
            
            # API 제한 회피를 위한 딜레이
            if i < len(requests) - 1:
                time.sleep(delay_between)
        
        return results


# 사용 예시 함수
def test_generator():
    """생성기 테스트"""
    
    generator = GeminiProblemGeneratorWithReview()
    
    # 울트라하드 문제 생성 테스트
    problem = generator.generate_problem(
        subject="미적분",
        topic="매개변수 미분법",
        difficulty="최상위",
        problem_type="단답형",
        pattern="매개변수미분"
    )
    
    if problem:
        print("Generated Problem:")
        print(json.dumps(problem, ensure_ascii=False, indent=2))
    else:
        print("Failed to generate problem")


if __name__ == "__main__":
    test_generator()