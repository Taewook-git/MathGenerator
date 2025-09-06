#!/usr/bin/env python3
"""JSON 파싱 문제 디버깅"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.generator.gemini_client_v2 import GeminiClientV2
import json
import logging

# 디버그 로깅 설정
logging.basicConfig(level=logging.DEBUG)

# API 직접 테스트
from dotenv import load_dotenv
load_dotenv(override=True)

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-lite',
    generation_config={
        "temperature": 0.7,
        "max_output_tokens": 2048,
        "response_mime_type": "application/json"
    },
    safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
)

prompt = """다음 조건에 맞는 수학 문제를 생성해주세요:
- 과목: 수학1
- 주제: 지수함수와 로그함수
- 난이도: 중
- 유형: 선택형
- 배점: 3점
- 2015 개정 교육과정 준수: 필수

5개의 선택지를 제공해주세요. (①~⑤)"""

system_prompt = """【필수 응답 형식】
반드시 아래 JSON 형식으로만 응답하세요. 모든 필수 필드를 반드시 포함해야 합니다.

{
    "question": "문제 내용",
    "answer": "정답",
    "topic": "지수함수와 로그함수",
    "difficulty": "중",
    "type": "선택형",
    "options": ["①...", "②...", "③...", "④...", "⑤..."],
    "points": 3,
    "exam_type": "공통",
    "keywords": ["키워드1", "키워드2"],
    "hint": "풀이 힌트"
}"""

full_prompt = system_prompt + "\n\n" + prompt

print("=" * 50)
print("프롬프트 전송 중...")
print("=" * 50)

try:
    response = model.generate_content(full_prompt)
    raw_text = response.text
    
    print("\n원본 응답:")
    print(repr(raw_text))  # repr로 이스케이프 문자 확인
    print("\n" + "=" * 50)
    
    # 다양한 파싱 시도
    print("\n파싱 시도 1: 직접 파싱")
    try:
        result = json.loads(raw_text)
        print("✅ 성공!")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except json.JSONDecodeError as e:
        print(f"❌ 실패: {e}")
        
    print("\n파싱 시도 2: 백슬래시 처리")
    try:
        # 잘못된 이스케이프 수정
        fixed = raw_text.replace('\\', '\\\\')
        result = json.loads(fixed)
        print("✅ 성공!")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except json.JSONDecodeError as e:
        print(f"❌ 실패: {e}")
        
    print("\n파싱 시도 3: 유니코드 이스케이프 처리")
    try:
        # raw string으로 처리
        import codecs
        decoded = codecs.decode(raw_text, 'unicode_escape')
        result = json.loads(decoded)
        print("✅ 성공!")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"❌ 실패: {e}")

except Exception as e:
    print(f"\n생성 실패: {e}")