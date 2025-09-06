"""
Gemini-2.5-Pro API 클라이언트
"""
import google.generativeai as genai
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
import json
import time
from google.api_core.exceptions import ResourceExhausted

load_dotenv()


class QuotaExceededException(Exception):
    """API 할당량 초과 예외"""
    pass


class GeminiClient:
    """Gemini-2.5-Pro API 래퍼"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-pro",
        temperature: float = 0.7,
        max_output_tokens: int = 2048
    ):
        """
        Args:
            api_key: Gemini API 키
            model_name: 모델 이름
            temperature: 생성 온도
            max_output_tokens: 최대 출력 토큰 수
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
            
        genai.configure(api_key=self.api_key)
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
                "response_mime_type": "application/json"
            }
        )
        
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        텍스트 생성
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트
            retry_count: 재시도 횟수
            
        Returns:
            생성된 응답 (JSON)
        """
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
        for attempt in range(retry_count):
            try:
                response = self.model.generate_content(full_prompt)
                
                # JSON 파싱
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    # JSON이 아닌 경우 텍스트 그대로 반환
                    return {"text": response.text}
                    
            except ResourceExhausted as e:
                # 할당량 초과 에러를 명확하게 처리
                error_msg = f"API quota exceeded: {str(e)}"
                print(f"Generation attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < retry_count - 1:
                    # 할당량 초과시 더 긴 대기 시간
                    wait_time = 60 * (attempt + 1)  # 1분, 2분, 3분...
                    print(f"Waiting {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                else:
                    raise QuotaExceededException(
                        "Gemini API daily quota exceeded. Please try again tomorrow or upgrade your API plan."
                    )
                    
            except Exception as e:
                print(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    raise
                    
    def generate_batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        배치 생성
        
        Args:
            prompts: 프롬프트 리스트
            system_prompt: 공통 시스템 프롬프트
            
        Returns:
            생성된 응답 리스트
        """
        results = []
        for prompt in prompts:
            try:
                result = self.generate(prompt, system_prompt)
                results.append(result)
            except Exception as e:
                print(f"Failed to generate for prompt: {e}")
                results.append({"error": str(e)})
                
        return results