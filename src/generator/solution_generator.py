"""
Gemini API를 사용한 수학 문제 풀이 생성기
"""
import google.generativeai as genai
from typing import Dict, Any, Optional
import json
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
        logging.FileHandler(log_dir / f'solution_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class GeminiSolutionGenerator:
    """Gemini API를 사용한 수학 문제 풀이 생성기"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-flash",
        temperature: float = 0.3  # 풀이는 정확성이 중요하므로 낮은 온도
    ):
        """
        Args:
            api_key: Gemini API 키
            model_name: 사용할 모델
            temperature: 생성 온도 (낮을수록 일관성 있음)
        """
        load_dotenv(override=True)
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        genai.configure(api_key=self.api_key)
        
        self.model_name = model_name
        self.temperature = temperature
        
        # 안전 설정 (수학 문제용 최소 필터)
        self.safety_settings = {
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        }
        
        # 모델 초기화
        self._init_model()
        
        logger.info(f"Solution Generator initialized with model: {model_name}")
    
    def _init_model(self):
        """모델 초기화"""
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": 4096,  # 풀이는 길 수 있으므로 충분한 토큰
                "top_p": 0.9,
                "top_k": 40
            },
            safety_settings=self.safety_settings
        )
    
    def generate_solution(
        self,
        question: str,
        answer: str,
        problem_type: str = "선택형",
        options: Optional[list] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        문제에 대한 상세 풀이 생성
        
        Args:
            question: 문제 내용
            answer: 정답
            problem_type: 문제 유형 (선택형/단답형)
            options: 선택지 (선택형인 경우)
            subject: 과목 (수학1/수학2/미적분)
            topic: 주제
            
        Returns:
            풀이 정보 딕셔너리
        """
        logger.info(f"Generating solution for: {topic if topic else 'Unknown topic'}")
        
        # 프롬프트 구성
        prompt = self._build_solution_prompt(
            question, answer, problem_type, options, subject, topic
        )
        
        try:
            response = self.model.generate_content(prompt)
            
            # 응답 파싱
            text = response.text.strip()
            
            # JSON 형식으로 반환된 경우 파싱
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            # JSON 파싱 시도
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                # JSON이 아닌 경우 텍스트로 처리
                result = {
                    "solution": text,
                    "steps": [],
                    "key_concepts": [],
                    "tips": []
                }
            
            # 필수 필드 확인
            if "solution" not in result:
                result["solution"] = text
            
            logger.info("Solution generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Solution generation error: {e}")
            return {
                "solution": "풀이 생성 중 오류가 발생했습니다.",
                "error": str(e)
            }
    
    def _build_solution_prompt(
        self,
        question: str,
        answer: str,
        problem_type: str,
        options: Optional[list],
        subject: Optional[str],
        topic: Optional[str]
    ) -> str:
        """풀이 생성 프롬프트 구성"""
        
        prompt = f"""다음 수학 문제에 대한 상세한 풀이를 작성해주세요.

【문제 정보】
과목: {subject if subject else '미지정'}
주제: {topic if topic else '미지정'}
유형: {problem_type}

【문제】
{question}
"""
        
        if problem_type == "선택형" and options:
            prompt += "\n【선택지】\n"
            for i, option in enumerate(options, 1):
                prompt += f"{i}. {option}\n"
        
        prompt += f"""
【정답】
{answer}

【풀이 요구사항】
1. 단계별 상세 풀이
   - 각 단계를 명확히 구분
   - 수식과 설명을 함께 제공
   - 논리적 흐름 유지

2. 핵심 개념 설명
   - 문제 해결에 필요한 주요 개념
   - 공식이나 정리 명시

3. 주의사항
   - 실수하기 쉬운 부분 언급
   - 다른 접근 방법 제시 (가능한 경우)

4. 형식
   - 수식은 LaTeX 형식 사용 ($수식$ 또는 $$수식$$)
   - 한글과 수식 적절히 혼용
   - 읽기 쉽게 문단 구분

【출력 형식】
다음 JSON 형식으로 출력하세요:
{{
    "solution": "전체 풀이 내용 (마크다운 형식)",
    "steps": [
        {{
            "step": 1,
            "description": "단계 설명",
            "calculation": "계산 과정"
        }},
        ...
    ],
    "key_concepts": ["핵심 개념1", "핵심 개념2", ...],
    "tips": ["팁1", "팁2", ...],
    "alternative_methods": "다른 풀이 방법 (선택사항)"
}}
"""
        
        return prompt
    
    def enhance_existing_solution(
        self,
        question: str,
        existing_solution: str,
        answer: str
    ) -> str:
        """
        기존 풀이를 개선하거나 보완
        
        Args:
            question: 문제 내용
            existing_solution: 기존 풀이
            answer: 정답
            
        Returns:
            개선된 풀이
        """
        prompt = f"""다음 수학 문제의 풀이를 개선해주세요.

【문제】
{question}

【정답】
{answer}

【기존 풀이】
{existing_solution}

【개선 요구사항】
1. 불명확한 부분을 명확하게
2. 빠진 단계 추가
3. 수식 표현 개선 (LaTeX 사용)
4. 설명 보완
5. 오류 수정 (있는 경우)

개선된 풀이를 마크다운 형식으로 작성하세요.
수식은 $수식$ 또는 $$수식$$ 형태로 표현하세요."""
        
        try:
            response = self.model.generate_content(prompt)
            enhanced_solution = response.text.strip()
            
            # 코드 블록 제거
            if enhanced_solution.startswith("```"):
                lines = enhanced_solution.split('\n')
                enhanced_solution = '\n'.join(lines[1:-1])
            
            return enhanced_solution
            
        except Exception as e:
            logger.error(f"Solution enhancement error: {e}")
            return existing_solution  # 오류 시 기존 풀이 반환
    
    def format_solution_for_display(self, solution: str) -> str:
        """
        풀이를 UI 표시용으로 포맷팅
        
        Args:
            solution: 원본 풀이 텍스트
            
        Returns:
            포맷팅된 풀이
        """
        # 기본 이스케이프 문자 처리
        formatted = solution.replace('\\n', '\n')
        formatted = formatted.replace('\\t', '  ')
        formatted = formatted.replace('\\\\', '\\')
        
        # 수식 구분자 정리
        formatted = formatted.replace('\\(', '$')
        formatted = formatted.replace('\\)', '$')
        formatted = formatted.replace('\\[', '$$')
        formatted = formatted.replace('\\]', '$$')
        
        # 번호 매기기 스타일 개선
        lines = formatted.split('\n')
        improved_lines = []
        
        for line in lines:
            # 단계 표시 개선
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                improved_lines.append(f"\n**{line.strip()}**")
            # 부제목 강조
            elif line.strip().startswith(('[', '【')):
                improved_lines.append(f"\n### {line.strip()}")
            else:
                improved_lines.append(line)
        
        return '\n'.join(improved_lines)


# 싱글톤 인스턴스
_solution_generator = None

def get_solution_generator() -> GeminiSolutionGenerator:
    """싱글톤 풀이 생성기 반환"""
    global _solution_generator
    if _solution_generator is None:
        _solution_generator = GeminiSolutionGenerator()
    return _solution_generator


# 사용 예시
if __name__ == "__main__":
    generator = get_solution_generator()
    
    # 테스트 문제
    test_question = """
    함수 f(x) = x³ - 3x² + 2에 대하여,
    f(x) = 0이 되는 x의 개수를 구하시오.
    """
    
    test_answer = "3"
    
    result = generator.generate_solution(
        question=test_question,
        answer=test_answer,
        problem_type="단답형",
        subject="수학2",
        topic="미분"
    )
    
    if "error" not in result:
        print("생성된 풀이:")
        print(result.get("solution", "풀이 없음"))
        print("\n핵심 개념:")
        for concept in result.get("key_concepts", []):
            print(f"- {concept}")
    else:
        print(f"오류: {result['error']}")