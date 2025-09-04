"""
선택지 수식 파싱 개선 모듈
Mathematical expression parsing for answer choices
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ChoiceParser:
    """선택지 수식 파싱 전문 클래스"""
    
    def __init__(self):
        # 수식 보호 패턴 (파싱 전에 보호할 수식들)
        self.math_patterns = [
            # 분수 표현
            (r'\\frac\{[^}]+\}\{[^}]+\}', 'FRAC'),
            (r'\d+/\d+', 'FRAC'),
            
            # 제곱근
            (r'\\sqrt\{[^}]+\}', 'SQRT'),
            (r'√\([^)]+\)', 'SQRT'),
            (r'√\d+', 'SQRT'),
            
            # 지수/로그
            (r'e\^[^\s,\]]+', 'EXP'),
            (r'ln\s*\([^)]+\)', 'LOG'),
            (r'log_?\d*\s*\([^)]+\)', 'LOG'),
            
            # 삼각함수
            (r'(sin|cos|tan|sec|csc|cot)\s*\([^)]+\)', 'TRIG'),
            (r'(sin|cos|tan)\^\d+\s*[^,\s\]]+', 'TRIG'),
            
            # 적분/미분
            (r'\\int[^}]*\}', 'INT'),
            (r'∫[^d]+d[a-z]', 'INT'),
            (r'd/d[a-z]\s*\([^)]+\)', 'DERIV'),
            
            # 극한
            (r'lim_\{[^}]+\}', 'LIM'),
            (r'\\lim[^}]+\}', 'LIM'),
            
            # 파이, 무한대
            (r'π', 'PI'),
            (r'\\pi', 'PI'),
            (r'∞', 'INF'),
            (r'\\infty', 'INF'),
            
            # 벡터/행렬 (LaTeX)
            (r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}', 'MATRIX'),
            (r'\\vec\{[^}]+\}', 'VECTOR'),
        ]
    
    def parse_choices(self, choices_data: Any) -> List[str]:
        """
        다양한 형식의 선택지를 파싱하여 표준 리스트로 변환
        
        Args:
            choices_data: 선택지 데이터 (리스트, 문자열, dict 등)
            
        Returns:
            파싱된 선택지 리스트
        """
        if isinstance(choices_data, list):
            return self._parse_list_choices(choices_data)
        elif isinstance(choices_data, str):
            return self._parse_string_choices(choices_data)
        elif isinstance(choices_data, dict):
            return self._parse_dict_choices(choices_data)
        else:
            logger.warning(f"Unsupported choices format: {type(choices_data)}")
            return self._create_default_choices()
    
    def _parse_list_choices(self, choices: List) -> List[str]:
        """리스트 형태의 선택지 파싱"""
        parsed = []
        
        for choice in choices:
            if isinstance(choice, str):
                # 선택지 번호 제거 및 정리
                cleaned = self._clean_choice_text(choice)
                parsed.append(cleaned)
            elif isinstance(choice, (int, float)):
                # 숫자는 문자열로 변환
                parsed.append(str(choice))
            elif isinstance(choice, dict):
                # dict인 경우 value 추출
                if 'value' in choice:
                    parsed.append(str(choice['value']))
                elif 'text' in choice:
                    parsed.append(str(choice['text']))
                else:
                    parsed.append(str(choice))
            else:
                parsed.append(str(choice))
        
        # 정확히 5개로 맞춤
        while len(parsed) < 5:
            parsed.append(f"{len(parsed) + 1}")
        while len(parsed) > 5:
            parsed.pop()
            
        return parsed
    
    def _parse_string_choices(self, choices_str: str) -> List[str]:
        """문자열 형태의 선택지 파싱"""
        # 수식 보호
        protected_str, replacements = self._protect_math_expressions(choices_str)
        
        # JSON 문자열인 경우
        if protected_str.strip().startswith('['):
            try:
                choices_list = json.loads(protected_str)
                # 보호된 수식 복원
                restored_list = []
                for choice in choices_list:
                    restored = self._restore_math_expressions(str(choice), replacements)
                    restored_list.append(restored)
                return self._parse_list_choices(restored_list)
            except:
                pass
        
        # 선택지 구분자로 분할
        # ①②③④⑤ 형태
        if any(num in protected_str for num in ['①', '②', '③', '④', '⑤']):
            pattern = r'[①②③④⑤]\s*([^①②③④⑤]+)'
            matches = re.findall(pattern, protected_str)
            if matches:
                restored = [self._restore_math_expressions(m.strip(), replacements) for m in matches]
                return self._parse_list_choices(restored)
        
        # 1) 2) 3) 형태
        pattern = r'\d+\)\s*([^,\n]+)'
        matches = re.findall(pattern, protected_str)
        if matches:
            restored = [self._restore_math_expressions(m.strip(), replacements) for m in matches]
            return self._parse_list_choices(restored)
        
        # 쉼표 구분
        if ',' in protected_str:
            choices = protected_str.split(',')
            restored = [self._restore_math_expressions(c.strip(), replacements) for c in choices]
            return self._parse_list_choices(restored)
        
        # 줄바꿈 구분
        if '\n' in protected_str:
            choices = protected_str.split('\n')
            restored = [self._restore_math_expressions(c.strip(), replacements) for c in choices if c.strip()]
            return self._parse_list_choices(restored)
        
        # 단일 값인 경우
        restored = self._restore_math_expressions(protected_str.strip(), replacements)
        return [restored, "2", "3", "4", "5"]
    
    def _parse_dict_choices(self, choices_dict: Dict) -> List[str]:
        """딕셔너리 형태의 선택지 파싱"""
        parsed = []
        
        # 번호 키로 접근
        for i in range(1, 6):
            key = str(i)
            if key in choices_dict:
                parsed.append(str(choices_dict[key]))
            elif f"choice{i}" in choices_dict:
                parsed.append(str(choices_dict[f"choice{i}"]))
            elif f"option{i}" in choices_dict:
                parsed.append(str(choices_dict[f"option{i}"]))
        
        # 부족하면 기본값 추가
        while len(parsed) < 5:
            parsed.append(f"{len(parsed) + 1}")
            
        return parsed
    
    def _clean_choice_text(self, text: str) -> str:
        """선택지 텍스트 정리"""
        # 선택지 번호 제거
        text = re.sub(r'^[①②③④⑤]\s*', '', text)
        text = re.sub(r'^\d+\)\s*', '', text)
        text = re.sub(r'^\d+\.\s*', '', text)
        text = re.sub(r'^[()\[\]]\s*', '', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        # 빈 문자열이면 기본값
        if not text:
            return "답"
            
        return text
    
    def _protect_math_expressions(self, text: str) -> tuple:
        """수식을 임시 토큰으로 치환하여 보호"""
        replacements = {}
        protected = text
        
        for pattern, token in self.math_patterns:
            matches = re.findall(pattern, protected)
            for i, match in enumerate(matches):
                placeholder = f"__{token}_{i}__"
                replacements[placeholder] = match
                protected = protected.replace(match, placeholder, 1)
        
        return protected, replacements
    
    def _restore_math_expressions(self, text: str, replacements: dict) -> str:
        """보호된 수식을 원래대로 복원"""
        restored = text
        for placeholder, original in replacements.items():
            restored = restored.replace(placeholder, original)
        return restored
    
    def _create_default_choices(self) -> List[str]:
        """기본 선택지 생성"""
        return ["1", "2", "3", "4", "5"]
    
    def validate_choices(self, choices: List[str], answer: str) -> Dict[str, Any]:
        """
        선택지 유효성 검증
        
        Returns:
            검증 결과 딕셔너리
        """
        result = {
            'is_valid': True,
            'issues': [],
            'fixed_choices': choices.copy(),
            'fixed_answer': answer
        }
        
        # 1. 선택지 개수 확인
        if len(choices) != 5:
            result['issues'].append(f"선택지 개수가 5개가 아님: {len(choices)}개")
            while len(result['fixed_choices']) < 5:
                result['fixed_choices'].append(f"{len(result['fixed_choices']) + 1}")
            while len(result['fixed_choices']) > 5:
                result['fixed_choices'].pop()
        
        # 2. 중복 선택지 확인
        seen = set()
        unique_choices = []
        for choice in result['fixed_choices']:
            if choice not in seen:
                unique_choices.append(choice)
                seen.add(choice)
            else:
                # 중복된 경우 변형
                modified = f"{choice}'"
                while modified in seen:
                    modified += "'"
                unique_choices.append(modified)
                seen.add(modified)
                result['issues'].append(f"중복 선택지 발견 및 수정: {choice}")
        
        result['fixed_choices'] = unique_choices
        
        # 3. 빈 선택지 확인
        for i, choice in enumerate(result['fixed_choices']):
            if not choice or choice.isspace():
                result['fixed_choices'][i] = str(i + 1)
                result['issues'].append(f"빈 선택지 발견 및 수정: 위치 {i+1}")
        
        # 4. 정답이 선택지에 있는지 확인
        if answer not in result['fixed_choices']:
            result['issues'].append(f"정답 '{answer}'이 선택지에 없음")
            # 정답과 가장 유사한 선택지 찾기
            best_match = self._find_best_match(answer, result['fixed_choices'])
            if best_match:
                result['fixed_answer'] = best_match
            else:
                result['fixed_answer'] = result['fixed_choices'][0]
            result['issues'].append(f"정답을 '{result['fixed_answer']}'로 수정")
        
        # 5. 수식 파싱 가능성 확인
        for i, choice in enumerate(result['fixed_choices']):
            if self._contains_unparseable_math(choice):
                result['issues'].append(f"선택지 {i+1}에 파싱 불가능한 수식 포함")
        
        result['is_valid'] = len(result['issues']) == 0
        return result
    
    def _find_best_match(self, answer: str, choices: List[str]) -> Optional[str]:
        """정답과 가장 유사한 선택지 찾기"""
        # 숫자만 추출하여 비교
        answer_nums = re.findall(r'[\d.]+', answer)
        if answer_nums:
            answer_main = answer_nums[0]
            for choice in choices:
                choice_nums = re.findall(r'[\d.]+', choice)
                if choice_nums and choice_nums[0] == answer_main:
                    return choice
        
        # 부분 문자열 매칭
        for choice in choices:
            if answer in choice or choice in answer:
                return choice
        
        return None
    
    def _contains_unparseable_math(self, text: str) -> bool:
        """파싱 불가능한 수식이 포함되어 있는지 확인"""
        # 균형 맞지 않는 괄호
        if text.count('(') != text.count(')'):
            return True
        if text.count('{') != text.count('}'):
            return True
        if text.count('[') != text.count(']'):
            return True
        
        # 연속된 연산자
        if re.search(r'[\+\-\*/]{2,}', text):
            return True
        
        return False


# 전역 인스턴스
choice_parser = ChoiceParser()


def enhance_choice_parsing(problem_data: Dict) -> Dict:
    """
    문제 데이터의 선택지 파싱 개선
    
    Args:
        problem_data: 원본 문제 데이터
        
    Returns:
        개선된 문제 데이터
    """
    if 'choices' not in problem_data:
        return problem_data
    
    # 선택지 파싱
    parsed_choices = choice_parser.parse_choices(problem_data['choices'])
    
    # 선택지 검증
    answer = problem_data.get('answer', '')
    validation = choice_parser.validate_choices(parsed_choices, answer)
    
    # 결과 업데이트
    problem_data['choices'] = validation['fixed_choices']
    problem_data['answer'] = validation['fixed_answer']
    
    # 검증 정보 추가
    if validation['issues']:
        if 'validation_issues' not in problem_data:
            problem_data['validation_issues'] = []
        problem_data['validation_issues'].extend(validation['issues'])
    
    return problem_data


if __name__ == "__main__":
    # 테스트
    parser = ChoiceParser()
    
    test_cases = [
        # 리스트 형태
        ["1", "2", "3", "4", "5"],
        ["e^2", "ln(2)", "√3", "π/2", "∞"],
        
        # 문자열 형태
        "① e^x + 1  ② ln(x-1)  ③ sin²x  ④ ∫xdx  ⑤ lim(x→0)",
        "1) 2π, 2) 3π, 3) 4π, 4) 5π, 5) 6π",
        
        # 수식이 포함된 경우
        ["\\frac{1}{2}", "\\sqrt{3}", "e^{\\pi}", "\\ln 2", "\\infty"],
    ]
    
    print("선택지 파싱 테스트:")
    print("=" * 50)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n테스트 {i}:")
        print(f"입력: {test}")
        parsed = parser.parse_choices(test)
        print(f"파싱 결과: {parsed}")
        
        # 검증
        validation = parser.validate_choices(parsed, parsed[0] if parsed else "")
        if validation['issues']:
            print(f"검증 이슈: {validation['issues']}")
        else:
            print("검증: ✓ 통과")