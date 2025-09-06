"""
OpenAI API 클라이언트 (Fallback용)
"""
from openai import OpenAI
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
import json
import time

load_dotenv()


class OpenAIClient:
    """OpenAI API 래퍼"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Args:
            api_key: OpenAI API 키
            model_name: 모델 이름 (gpt-4o-mini, gpt-4o, gpt-3.5-turbo 등)
            temperature: 생성 온도
            max_tokens: 최대 출력 토큰 수
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")
            
        self.client = OpenAI(api_key=self.api_key)
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
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
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(retry_count):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
                
                # JSON 파싱
                try:
                    return json.loads(response.choices[0].message.content)
                except json.JSONDecodeError:
                    # JSON이 아닌 경우 텍스트 그대로 반환
                    return {"text": response.choices[0].message.content}
                    
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