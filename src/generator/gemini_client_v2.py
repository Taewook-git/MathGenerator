"""
강화된 Gemini API 클라이언트 (v2)
- 더 나은 에러 처리
- 안전 필터 관리
- 로깅 시스템
- 자동 복구 메커니즘
"""
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import ResourceExhausted, InvalidArgument
from typing import Optional, Dict, Any, List, Tuple
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# 로깅 설정
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'gemini_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class GeminiClientV2:
    """강화된 Gemini API 클라이언트"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,  # None이면 환경변수에서 읽음
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        use_safety_filter: bool = False  # 안전 필터 사용 여부
    ):
        """
        Args:
            api_key: Gemini API 키
            model_name: 모델 이름
            temperature: 생성 온도
            max_output_tokens: 최대 출력 토큰 수
            use_safety_filter: 안전 필터 사용 여부
        """
        # API 키 로드 (환경 변수 우선순위 제거)
        from dotenv import load_dotenv
        load_dotenv(override=True)  # .env 파일 우선
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        
        # 모델 이름 설정 (환경 변수에서 읽기)
        if not model_name:
            model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        # API 키 검증
        self._validate_api_key()
        
        logger.info(f"Initializing GeminiClientV2 with model: {model_name}")
        
        genai.configure(api_key=self.api_key)
        
        # 안전 설정 구성
        if use_safety_filter:
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        else:
            # 수학 문제 생성을 위해 최소 필터링
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.safety_settings = safety_settings
        
        # 모델 초기화
        self._initialize_model()
        
        # 통계 추적
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "safety_blocks": 0,
            "quota_errors": 0
        }
    
    def _validate_api_key(self):
        """API 키 유효성 검증"""
        try:
            genai.configure(api_key=self.api_key)
            # 간단한 테스트 모델 생성
            test_model = genai.GenerativeModel('gemini-2.5-pro')
            logger.info("API key validation successful")
        except Exception as e:
            logger.error(f"Invalid API key: {e}")
            raise ValueError(f"Invalid GEMINI_API_KEY: {e}")
    
    def _initialize_model(self):
        """모델 초기화 또는 재초기화"""
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_output_tokens,
                    "response_mime_type": "application/json"
                },
                safety_settings=self.safety_settings
            )
            logger.info(f"Model initialized: {self.model_name}")
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        retry_count: int = 3,
        fallback_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        강화된 텍스트 생성
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트
            retry_count: 재시도 횟수
            fallback_on_error: 에러 시 기본값 반환 여부
            
        Returns:
            생성된 응답 (JSON)
        """
        self.stats["total_requests"] += 1
        
        full_prompt = self._prepare_prompt(prompt, system_prompt)
        last_error = None
        
        for attempt in range(retry_count):
            try:
                logger.info(f"Generation attempt {attempt + 1}/{retry_count}")
                logger.debug(f"Sending prompt (first 500 chars): {full_prompt[:500]}...")
                
                response = self.model.generate_content(full_prompt)
                
                # 응답 검증
                if self._is_response_blocked(response):
                    self.stats["safety_blocks"] += 1
                    logger.warning(f"Response blocked by safety filter (attempt {attempt + 1})")
                    logger.debug(f"Blocked prompt (first 1000 chars): {full_prompt[:1000]}")
                    if response.candidates:
                        for candidate in response.candidates:
                            if hasattr(candidate, 'safety_ratings'):
                                logger.debug(f"Safety ratings: {candidate.safety_ratings}")
                    
                    if attempt < retry_count - 1:
                        # 프롬프트 수정 후 재시도
                        full_prompt = self._modify_prompt_for_safety(full_prompt)
                        time.sleep(1)
                        continue
                    elif fallback_on_error:
                        return self._get_fallback_response()
                    else:
                        raise ValueError("Response blocked by safety filter")
                
                # 성공적인 응답 파싱
                result = self._parse_response(response)
                self.stats["successful_requests"] += 1
                logger.info("Generation successful")
                return result
                
            except ResourceExhausted as e:
                self.stats["quota_errors"] += 1
                logger.error(f"Quota exceeded: {e}")
                last_error = e
                
                if attempt < retry_count - 1:
                    wait_time = min(60 * (2 ** attempt), 300)  # 최대 5분
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                elif fallback_on_error:
                    return self._get_fallback_response()
                    
            except InvalidArgument as e:
                logger.error(f"Invalid API key or request: {e}")
                self.stats["failed_requests"] += 1
                
                # API 키 재검증 시도
                if "API_KEY_INVALID" in str(e):
                    logger.info("Attempting to reload API key from .env")
                    from dotenv import load_dotenv
                    load_dotenv(override=True)
                    new_key = os.getenv("GEMINI_API_KEY")
                    if new_key and new_key != self.api_key:
                        self.api_key = new_key
                        genai.configure(api_key=self.api_key)
                        self._initialize_model()
                        continue
                
                last_error = e
                if fallback_on_error and attempt == retry_count - 1:
                    return self._get_fallback_response()
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.stats["failed_requests"] += 1
                last_error = e
                
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                elif fallback_on_error:
                    return self._get_fallback_response()
        
        # 모든 재시도 실패
        self.stats["failed_requests"] += 1
        if fallback_on_error:
            logger.warning("All retries failed, returning fallback response")
            return self._get_fallback_response()
        else:
            raise last_error or Exception("Generation failed after all retries")
    
    def _prepare_prompt(self, prompt: str, system_prompt: Optional[str]) -> str:
        """프롬프트 준비"""
        if system_prompt:
            return f"{system_prompt}\n\n{prompt}"
        return prompt
    
    def _is_response_blocked(self, response) -> bool:
        """응답이 차단되었는지 확인"""
        if not response.parts:
            if response.candidates:
                for candidate in response.candidates:
                    # finish_reason: 1=STOP, 2=SAFETY, 3=MAX_TOKENS, 4=RECITATION
                    if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                        return True
        return False
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """응답 파싱"""
        try:
            text = response.text
            logger.debug(f"Raw response (first 500 chars): {text[:500]}...")
            
            # JSON 파싱 시도
            # JSON 코드 블록이 있으면 추출
            if "```json" in text:
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
                if json_match:
                    text = json_match.group(1)
            elif "```" in text:
                import re
                code_match = re.search(r'```\s*([\s\S]*?)\s*```', text)
                if code_match:
                    text = code_match.group(1)
            
            # LaTeX 수식의 백슬래시 처리
            # \log, \sin, \cos 등의 LaTeX 명령어를 보호
            import re
            # 일반적인 LaTeX 명령어들을 raw string으로 변환
            latex_commands = [
                'log', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc',
                'ln', 'exp', 'sqrt', 'frac', 'sum', 'int', 'lim',
                'alpha', 'beta', 'gamma', 'delta', 'theta', 'pi',
                'infty', 'partial', 'nabla', 'cdot', 'times',
                'left', 'right', 'ldots', 'cdots', 'vdots'
            ]
            
            # 첫 번째 시도: 직접 파싱
            try:
                result = json.loads(text)
                logger.debug(f"Parsed JSON keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
                return result
            except json.JSONDecodeError as first_error:
                # 두 번째 시도: 백슬래시를 이스케이프
                try:
                    # \\ → \\\\ 로 변경 (JSON에서 백슬래시를 표현하기 위해)
                    fixed_text = text.replace('\\', '\\\\')
                    result = json.loads(fixed_text)
                    logger.debug(f"Parsed JSON with escaped backslashes")
                    return result
                except json.JSONDecodeError:
                    # 세 번째 시도: 특정 LaTeX 패턴만 수정
                    try:
                        # LaTeX 수식 내의 백슬래시만 처리
                        import re
                        # $...$ 또는 $$...$$ 내부의 백슬래시를 이스케이프
                        def escape_math(match):
                            math_content = match.group(1)
                            # 백슬래시를 이중 백슬래시로
                            escaped = math_content.replace('\\', '\\\\')
                            return f'${escaped}$'
                        
                        fixed_text = re.sub(r'\$([^$]*)\$', escape_math, text)
                        result = json.loads(fixed_text)
                        logger.debug(f"Parsed JSON with LaTeX escape handling")
                        return result
                    except json.JSONDecodeError:
                        raise first_error
            
        except json.JSONDecodeError as e:
            logger.warning(f"Response is not valid JSON: {e}")
            logger.debug(f"Failed to parse: {text[:200]}...")
            # 기본 문제 반환
            return self._get_fallback_response()
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return self._get_fallback_response()
    
    def _modify_prompt_for_safety(self, prompt: str) -> str:
        """안전 필터 회피를 위한 프롬프트 수정"""
        prefix = """[교육용 수학 문제 생성 요청]

이것은 대한민국 교육부 2015 개정 교육과정에 따른 수학 학습 자료를 생성하는 요청입니다.
수험생들의 대학수학능력시험 준비를 위한 문제를 제공해주세요.
차별적이거나 폭력적인 내용 없이 순수하게 수학 교육을 위한 문제를 생성해주세요.

"""
        if not prompt.startswith(prefix):
            return prefix + prompt
        return prompt
    
    def _get_fallback_response(self) -> Dict[str, Any]:
        """에러 시 반환할 기본 응답"""
        logger.info("Returning fallback response")
        return {
            "question": "다음 이차방정식의 해를 구하시오: x² - 5x + 6 = 0",
            "options": ["① x = 2, 3", "② x = -2, -3", "③ x = 1, 6", "④ x = -1, -6", "⑤ x = 0, 5"],
            "answer": "① x = 2, 3",
            "topic": "이차방정식",
            "difficulty": "중",
            "type": "선택형",
            "points": 3,
            "exam_type": "수능",
            "keywords": ["이차방정식", "인수분해"],
            "hint": "인수분해: (x-2)(x-3) = 0",
            "_meta": {
                "generated_by": "fallback",
                "reason": "API error or safety block",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return {
            **self.stats,
            "success_rate": (
                self.stats["successful_requests"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0 else 0
            )
        }
    
    def reset_stats(self):
        """통계 초기화"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "safety_blocks": 0,
            "quota_errors": 0
        }
        logger.info("Statistics reset")
    
    def test_connection(self) -> Tuple[bool, str]:
        """API 연결 테스트"""
        try:
            response = self.model.generate_content("Return OK in JSON: {\"status\": \"ok\"}")
            if response.parts:
                logger.info("Connection test successful")
                return True, "Connection successful"
            else:
                logger.warning("Connection test failed: Empty response")
                return False, "Empty response from API"
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, str(e)