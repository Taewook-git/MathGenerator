"""
향상된 JSON 파싱 및 수정 모듈
Enhanced JSON parsing and fixing module
"""

import re
import json
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class JSONFixer:
    """향상된 JSON 수정 클래스"""
    
    def __init__(self):
        # 마크다운 및 불필요한 텍스트 제거 패턴
        self.cleanup_patterns = [
            (r'```json\s*', ''),
            (r'```\s*', ''),
            (r'^\s*JSON[:\s]*', ''),
            (r'^\s*json[:\s]*', ''),
        ]
        
        # JSON 속성 이름 패턴
        self.property_patterns = [
            'question', 'choices', 'answer', 'solution',
            'key_concepts', 'difficulty_rationale', 'common_mistakes',
            'requires_graph', 'graph_type', 'graph_params',
            'difficulty_analysis', 'ultra_difficulty_score'
        ]
    
    def fix_json(self, response_text: str) -> str:
        """
        AI 응답에서 JSON 추출 및 수정
        
        Args:
            response_text: AI 응답 텍스트
            
        Returns:
            수정된 JSON 문자열
        """
        try:
            # 1단계: 마크다운 제거 및 정리
            cleaned = self._clean_response(response_text)
            
            # 2단계: JSON 블록 추출
            json_str = self._extract_json_block(cleaned)
            
            if not json_str:
                logger.warning("JSON 블록을 찾을 수 없음")
                return self._create_fallback_json(response_text)
            
            # 3단계: JSON 구문 오류 수정 시도
            fixed_json = self._fix_json_syntax(json_str)
            
            # 4단계: 파싱 테스트
            try:
                parsed = json.loads(fixed_json)
                # 필수 필드 확인
                self._ensure_required_fields(parsed)
                return json.dumps(parsed, ensure_ascii=False, indent=2)
            except json.JSONDecodeError as e:
                # 5단계: 고급 수정 시도
                advanced_fixed = self._advanced_fix(fixed_json, e)
                if advanced_fixed:
                    return advanced_fixed
                
                # 6단계: 패턴 기반 재구성
                reconstructed = self._reconstruct_from_patterns(response_text)
                if reconstructed:
                    return reconstructed
                
                # 마지막 수단: 폴백
                return self._create_fallback_json(response_text)
                
        except Exception as e:
            logger.error(f"JSON 수정 중 예외: {e}")
            return self._create_fallback_json(response_text)
    
    def _clean_response(self, text: str) -> str:
        """응답 텍스트 정리"""
        cleaned = text
        
        # 마크다운 코드 블록 제거
        for pattern, replacement in self.cleanup_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.MULTILINE)
        
        # 주석 제거 (// 스타일)
        cleaned = re.sub(r'//[^\n]*', '', cleaned)
        
        return cleaned.strip()
    
    def _extract_json_block(self, text: str) -> Optional[str]:
        """JSON 블록 추출"""
        # 방법 1: 중괄호 기반 추출
        stack = []
        start_idx = -1
        in_string = False
        escape_next = False
        
        for i, char in enumerate(text):
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '{':
                    if start_idx == -1:
                        start_idx = i
                    stack.append('{')
                elif char == '}':
                    if stack:
                        stack.pop()
                        if not stack and start_idx != -1:
                            return text[start_idx:i+1]
        
        # 방법 2: 정규표현식 기반 추출
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        
        return None
    
    def _fix_json_syntax(self, json_str: str) -> str:
        """JSON 구문 오류 수정"""
        fixed = json_str
        
        # 1. 후행 쉼표 제거
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        
        # 2. 속성 이름 따옴표 수정
        for prop in self.property_patterns:
            # 따옴표 없는 속성명에 따옴표 추가
            fixed = re.sub(f'(?<!")\\b{prop}\\b(?!")', f'"{prop}"', fixed)
            # 작은따옴표를 큰따옴표로 변경
            fixed = re.sub(f"'{prop}'", f'"{prop}"', fixed)
        
        # 3. 작은따옴표를 큰따옴표로 (값에서)
        # 속성명이 아닌 곳에서만
        fixed = self._fix_quotes_in_values(fixed)
        
        # 4. 이스케이프 문자 수정
        fixed = self._fix_escape_sequences(fixed)
        
        # 5. 숫자 값 정리 (NaN, Infinity 등)
        fixed = re.sub(r'\bNaN\b', 'null', fixed)
        fixed = re.sub(r'\bInfinity\b', '9999999', fixed)
        fixed = re.sub(r'\bundefined\b', 'null', fixed)
        
        return fixed
    
    def _fix_quotes_in_values(self, json_str: str) -> str:
        """값 부분의 따옴표 수정"""
        # 매우 조심스럽게 처리
        result = []
        in_key = False
        in_value = False
        i = 0
        
        while i < len(json_str):
            char = json_str[i]
            
            if char == '"':
                # 속성명 시작/끝 판단
                if i > 0 and json_str[i-1] in ':{,\n\t ':
                    in_key = True
                elif in_key and i < len(json_str) - 1 and json_str[i+1] == ':':
                    in_key = False
                
                result.append(char)
            elif char == "'" and not in_key:
                # 값 부분의 작은따옴표를 큰따옴표로
                result.append('"')
            else:
                result.append(char)
            
            i += 1
        
        return ''.join(result)
    
    def _fix_escape_sequences(self, json_str: str) -> str:
        """이스케이프 시퀀스 수정"""
        # 잘못된 이스케이프 수정
        fixed = json_str
        
        # \' -> '
        fixed = fixed.replace("\\'", "'")
        
        # 줄바꿈 처리
        fixed = fixed.replace('\r\n', '\\n')
        fixed = fixed.replace('\n', '\\n')
        fixed = fixed.replace('\r', '\\n')
        
        # 탭 처리
        fixed = fixed.replace('\t', '\\t')
        
        return fixed
    
    def _advanced_fix(self, json_str: str, error: json.JSONDecodeError) -> Optional[str]:
        """고급 JSON 수정"""
        try:
            # 에러 위치 기반 수정
            error_line = error.lineno - 1 if error.lineno else 0
            error_col = error.colno - 1 if error.colno else 0
            
            lines = json_str.split('\n')
            
            if error_line < len(lines):
                problem_line = lines[error_line]
                
                # 속성명 문제인지 확인
                if "Expecting property name" in str(error):
                    # 해당 라인에서 따옴표 없는 속성명 찾기
                    for prop in self.property_patterns:
                        if prop in problem_line and f'"{prop}"' not in problem_line:
                            problem_line = problem_line.replace(prop, f'"{prop}"')
                    
                    lines[error_line] = problem_line
                    fixed = '\n'.join(lines)
                    
                    # 다시 파싱 시도
                    parsed = json.loads(fixed)
                    return json.dumps(parsed, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.debug(f"고급 수정 실패: {e}")
        
        return None
    
    def _reconstruct_from_patterns(self, text: str) -> Optional[str]:
        """패턴 기반 재구성"""
        try:
            result = {}
            
            # question 추출
            question_match = re.search(r'question["\']?\s*:\s*["\']([^"\']+)["\']', text, re.IGNORECASE)
            if question_match:
                result['question'] = question_match.group(1)
            
            # choices 추출
            choices_match = re.search(r'choices["\']?\s*:\s*\[([^\]]+)\]', text, re.IGNORECASE)
            if choices_match:
                choices_text = choices_match.group(1)
                # 선택지 파싱
                choices = re.findall(r'["\']([^"\']+)["\']', choices_text)
                if len(choices) >= 5:
                    result['choices'] = choices[:5]
                else:
                    # 부족하면 채우기
                    result['choices'] = choices + [f"{i+1}" for i in range(len(choices), 5)]
            
            # answer 추출
            answer_match = re.search(r'answer["\']?\s*:\s*["\']([^"\']+)["\']', text, re.IGNORECASE)
            if answer_match:
                result['answer'] = answer_match.group(1)
            
            # solution 추출
            solution_match = re.search(r'solution["\']?\s*:\s*["\']([^"\']+)["\']', text, re.IGNORECASE | re.DOTALL)
            if solution_match:
                result['solution'] = solution_match.group(1)
            
            # key_concepts 추출
            concepts_match = re.search(r'key_concepts["\']?\s*:\s*\[([^\]]+)\]', text, re.IGNORECASE)
            if concepts_match:
                concepts_text = concepts_match.group(1)
                concepts = re.findall(r'["\']([^"\']+)["\']', concepts_text)
                result['key_concepts'] = concepts if concepts else ["수학"]
            
            # 필수 필드 확인
            if 'question' in result:
                self._ensure_required_fields(result)
                return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.debug(f"패턴 재구성 실패: {e}")
        
        return None
    
    def _ensure_required_fields(self, data: Dict) -> Dict:
        """필수 필드 확인 및 기본값 설정"""
        if 'question' not in data:
            data['question'] = "문제를 생성할 수 없습니다."
        
        if 'choices' not in data:
            data['choices'] = ["1", "2", "3", "4", "5"]
        elif len(data['choices']) < 5:
            while len(data['choices']) < 5:
                data['choices'].append(str(len(data['choices']) + 1))
        
        if 'answer' not in data:
            data['answer'] = data['choices'][0] if data['choices'] else "1"
        
        if 'solution' not in data:
            data['solution'] = "해설이 제공되지 않았습니다."
        
        if 'key_concepts' not in data:
            data['key_concepts'] = ["수학"]
        
        return data
    
    def _create_fallback_json(self, text: str) -> str:
        """폴백 JSON 생성"""
        fallback = {
            "question": "문제 생성 중 오류가 발생했습니다. 다시 시도해주세요.",
            "choices": ["1", "2", "3", "4", "5"],
            "answer": "1",
            "solution": "JSON 파싱 오류로 인해 해설을 표시할 수 없습니다.",
            "key_concepts": ["파싱 오류"],
            "requires_graph": False,
            "parsing_error": True
        }
        
        # 가능하면 일부 정보라도 추출
        question_match = re.search(r'문제[:\s]*([^"\n]+)', text)
        if question_match:
            fallback['question'] = question_match.group(1).strip()
        
        return json.dumps(fallback, ensure_ascii=False, indent=2)


# 전역 인스턴스
json_fixer = JSONFixer()


if __name__ == "__main__":
    # 테스트
    fixer = JSONFixer()
    
    test_cases = [
        # 속성명에 따옴표 없음
        """{
            question: "문제입니다",
            answer: "1"
        }""",
        
        # 작은따옴표 사용
        """{
            'question': '문제입니다',
            'answer': '1'
        }""",
        
        # 후행 쉼표
        """{
            "question": "문제",
            "answer": "1",
        }""",
        
        # 혼합 문제
        """{
            question: "다음 중 옳은 것은?",
            'choices': ["1", "2", "3", "4", "5"],
            answer: 1,
            "solution": "해설입니다",
        }""",
    ]
    
    print("=" * 60)
    print("JSON 수정 테스트")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n테스트 {i}:")
        print("원본:")
        print(test)
        
        fixed = fixer.fix_json(test)
        print("\n수정:")
        print(fixed)
        
        try:
            parsed = json.loads(fixed)
            print("✓ 파싱 성공")
        except Exception as e:
            print(f"✗ 파싱 실패: {e}")