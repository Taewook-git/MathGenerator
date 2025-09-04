"""
정답 매핑 및 파싱 개선 모듈
Answer mapping and parsing enhancement module
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class AnswerMapper:
    """정답 매핑 전문 클래스"""
    
    def __init__(self):
        # 정답 형식 패턴
        self.answer_patterns = [
            # 번호 형식 (1, 2, 3 등)
            (r'^[1-5]$', 'number'),
            # 원 번호 형식 (①, ②, ③ 등)
            (r'^[①②③④⑤]$', 'circle'),
            # 괄호 번호 형식 (1), 2) 등)
            (r'^\(?[1-5]\)?$', 'parenthesis'),
            # 실제 값 (나머지는 실제 답안으로 간주)
            (r'.*', 'value')
        ]
        
        self.circle_to_index = {
            '①': 0, '②': 1, '③': 2, '④': 3, '⑤': 4,
            '1': 0, '2': 1, '3': 2, '4': 3, '5': 4,
            '(1)': 0, '(2)': 1, '(3)': 2, '(4)': 3, '(5)': 4,
            '1)': 0, '2)': 1, '3)': 2, '4)': 3, '5)': 4,
        }
    
    def map_answer(self, problem_data: Dict) -> Dict:
        """
        문제 데이터의 정답을 올바른 값으로 매핑
        
        Args:
            problem_data: 원본 문제 데이터
            
        Returns:
            수정된 문제 데이터
        """
        if 'answer' not in problem_data:
            return problem_data
        
        answer = str(problem_data['answer']).strip()
        choices = problem_data.get('choices', [])
        
        # 선택형 문제가 아니면 그대로 반환
        if not choices:
            return problem_data
        
        # 정답이 번호 형식인지 확인
        answer_type = self._identify_answer_type(answer)
        
        if answer_type in ['number', 'circle', 'parenthesis']:
            # 번호를 인덱스로 변환
            index = self._get_answer_index(answer)
            
            if index is not None and 0 <= index < len(choices):
                # 실제 답안 내용으로 변경
                actual_answer = choices[index]
                problem_data['answer'] = actual_answer
                problem_data['answer_index'] = index + 1  # 1부터 시작하는 번호
                
                if 'answer_mapping_info' not in problem_data:
                    problem_data['answer_mapping_info'] = {}
                
                problem_data['answer_mapping_info'].update({
                    'original_answer': answer,
                    'mapped_answer': actual_answer,
                    'answer_type': answer_type,
                    'index': index + 1
                })
                
                logger.debug(f"Answer mapped: {answer} → {actual_answer}")
            else:
                # 인덱스가 범위를 벗어나는 경우
                logger.warning(f"Answer index out of range: {answer} (choices: {len(choices)})")
                problem_data['validation_warning'] = f"정답 번호 {answer}가 선택지 범위를 벗어남"
        
        # 정답이 이미 실제 값인 경우 검증
        elif answer_type == 'value':
            if answer not in choices:
                # 정답이 선택지에 없는 경우 가장 유사한 것 찾기
                best_match = self._find_best_match(answer, choices)
                if best_match:
                    problem_data['answer'] = best_match
                    problem_data['validation_warning'] = f"정답 '{answer}'을(를) 선택지에서 '{best_match}'로 매칭"
                else:
                    # 매칭 실패 시 첫 번째 선택지로
                    problem_data['answer'] = choices[0]
                    problem_data['validation_warning'] = f"정답 '{answer}'을(를) 찾을 수 없어 첫 번째 선택지로 설정"
        
        return problem_data
    
    def _identify_answer_type(self, answer: str) -> str:
        """정답의 형식을 식별"""
        for pattern, answer_type in self.answer_patterns:
            if re.match(pattern, answer):
                if answer_type != 'value':
                    return answer_type
        return 'value'
    
    def _get_answer_index(self, answer: str) -> Optional[int]:
        """정답 번호를 인덱스로 변환"""
        # 직접 매핑
        if answer in self.circle_to_index:
            return self.circle_to_index[answer]
        
        # 숫자 추출
        numbers = re.findall(r'\d', answer)
        if numbers:
            num = int(numbers[0])
            if 1 <= num <= 5:
                return num - 1
        
        return None
    
    def _find_best_match(self, answer: str, choices: List[str]) -> Optional[str]:
        """정답과 가장 유사한 선택지 찾기"""
        answer_clean = self._clean_expression(answer)
        
        # 정확한 매칭
        for choice in choices:
            if self._clean_expression(choice) == answer_clean:
                return choice
        
        # 부분 매칭
        for choice in choices:
            choice_clean = self._clean_expression(choice)
            if answer_clean in choice_clean or choice_clean in answer_clean:
                return choice
        
        # 숫자 매칭
        answer_nums = self._extract_numbers(answer)
        if answer_nums:
            for choice in choices:
                choice_nums = self._extract_numbers(choice)
                if choice_nums and answer_nums[0] == choice_nums[0]:
                    return choice
        
        return None
    
    def _clean_expression(self, expr: str) -> str:
        """수식을 정규화하여 비교하기 쉽게 만듦"""
        # 공백 제거
        expr = re.sub(r'\s+', '', expr)
        # 괄호 정규화
        expr = expr.replace('（', '(').replace('）', ')')
        # × → *
        expr = expr.replace('×', '*').replace('·', '*')
        # ÷ → /
        expr = expr.replace('÷', '/')
        return expr.lower()
    
    def _extract_numbers(self, expr: str) -> List[float]:
        """수식에서 숫자 추출"""
        # 분수 형태 처리
        fraction_match = re.match(r'(\d+)\s*/\s*(\d+)', expr)
        if fraction_match:
            num, den = fraction_match.groups()
            return [float(num) / float(den)]
        
        # 일반 숫자
        numbers = re.findall(r'-?\d+\.?\d*', expr)
        return [float(n) for n in numbers]
    
    def fix_solution_parsing(self, solution: str) -> str:
        """
        해설 텍스트의 파싱 오류 수정
        """
        if not solution:
            return "해설이 제공되지 않았습니다."
        
        # 이스케이프 문자 처리
        solution = solution.replace('\\n', '\n')
        solution = solution.replace('\\t', '  ')
        solution = solution.replace('\\"', '"')
        solution = solution.replace("\\'", "'")
        
        # 수식 마크다운 정리
        # $$ ... $$ → 블록 수식
        solution = re.sub(r'\$\$(.+?)\$\$', r'\n\n$$\1$$\n\n', solution, flags=re.DOTALL)
        # $ ... $ → 인라인 수식
        solution = re.sub(r'(?<!\$)\$(?!\$)(.+?)\$(?!\$)', r'$\1$', solution)
        
        # 단계 구분 개선
        solution = re.sub(r'(?:단계|STEP|Step)\s*(\d+)', r'\n\n**단계 \1**', solution, flags=re.IGNORECASE)
        solution = re.sub(r'^(\d+)\.\s+', r'\n\1. ', solution, flags=re.MULTILINE)
        
        # 중복 줄바꿈 제거
        solution = re.sub(r'\n{3,}', '\n\n', solution)
        
        # 앞뒤 공백 정리
        solution = solution.strip()
        
        return solution
    
    def fix_key_concepts_parsing(self, concepts: Union[List, str, None]) -> List[str]:
        """
        핵심 개념 리스트의 파싱 오류 수정
        """
        if not concepts:
            return ["핵심 개념이 제공되지 않았습니다."]
        
        # 문자열인 경우 리스트로 변환
        if isinstance(concepts, str):
            # JSON 문자열인 경우
            if concepts.startswith('['):
                try:
                    concepts = json.loads(concepts)
                except:
                    pass
            
            # 여전히 문자열인 경우 분리
            if isinstance(concepts, str):
                # 쉼표, 세미콜론, 줄바꿈으로 분리
                concepts = re.split(r'[,;，；\n]', concepts)
        
        # 리스트 정리
        if isinstance(concepts, list):
            cleaned = []
            for concept in concepts:
                if concept:
                    # 문자열로 변환
                    concept_str = str(concept).strip()
                    # 번호 제거
                    concept_str = re.sub(r'^\d+\.\s*', '', concept_str)
                    concept_str = re.sub(r'^[-*•]\s*', '', concept_str)
                    # 빈 문자열이 아니면 추가
                    if concept_str:
                        cleaned.append(concept_str)
            
            return cleaned if cleaned else ["핵심 개념이 제공되지 않았습니다."]
        
        return ["핵심 개념이 제공되지 않았습니다."]


# 전역 인스턴스
answer_mapper = AnswerMapper()


def enhance_problem_data(problem_data: Dict) -> Dict:
    """
    문제 데이터 전체 개선
    
    Args:
        problem_data: 원본 문제 데이터
        
    Returns:
        개선된 문제 데이터
    """
    # 1. 정답 매핑
    enhanced = answer_mapper.map_answer(problem_data)
    
    # 2. 해설 파싱 수정
    if 'solution' in enhanced:
        enhanced['solution'] = answer_mapper.fix_solution_parsing(enhanced['solution'])
    
    # 3. 핵심 개념 파싱 수정
    if 'key_concepts' in enhanced:
        enhanced['key_concepts'] = answer_mapper.fix_key_concepts_parsing(enhanced['key_concepts'])
    
    # 4. 추가 필드 정리
    if 'difficulty_rationale' in enhanced and isinstance(enhanced['difficulty_rationale'], str):
        enhanced['difficulty_rationale'] = answer_mapper.fix_solution_parsing(enhanced['difficulty_rationale'])
    
    if 'common_mistakes' in enhanced:
        enhanced['common_mistakes'] = answer_mapper.fix_key_concepts_parsing(enhanced['common_mistakes'])
    
    return enhanced


if __name__ == "__main__":
    # 테스트
    mapper = AnswerMapper()
    
    print("=" * 60)
    print("정답 매핑 테스트")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "번호만 있는 경우",
            "data": {
                "choices": ["2π", "3π", "4π", "5π", "6π"],
                "answer": "3"
            }
        },
        {
            "name": "원 번호인 경우",
            "data": {
                "choices": ["e^x", "ln(x)", "sin(x)", "cos(x)", "tan(x)"],
                "answer": "②"
            }
        },
        {
            "name": "이미 값인 경우",
            "data": {
                "choices": ["1", "2", "3", "4", "5"],
                "answer": "3"
            }
        },
        {
            "name": "매칭 필요한 경우",
            "data": {
                "choices": ["2√3", "3√2", "√6", "6", "12"],
                "answer": "2*sqrt(3)"
            }
        }
    ]
    
    for test in test_cases:
        print(f"\n{test['name']}:")
        print(f"  원본: answer = {test['data']['answer']}")
        
        result = mapper.map_answer(test['data'].copy())
        print(f"  매핑: answer = {result['answer']}")
        
        if 'answer_mapping_info' in result:
            print(f"  정보: {result['answer_mapping_info']}")
    
    # 해설 파싱 테스트
    print("\n" + "=" * 60)
    print("해설 파싱 테스트")
    print("=" * 60)
    
    test_solution = "단계 1: 함수를 미분한다.\\n$f'(x) = 2x$\\n\\n단계 2: 극값을 구한다.\\n$f'(x) = 0$에서 $x = 0$"
    fixed_solution = mapper.fix_solution_parsing(test_solution)
    print("원본:")
    print(test_solution)
    print("\n수정:")
    print(fixed_solution)
    
    # 핵심 개념 파싱 테스트
    print("\n" + "=" * 60)
    print("핵심 개념 파싱 테스트")
    print("=" * 60)
    
    test_concepts = [
        "1. 미분",
        "2. 적분",
        "- 극값",
        None,
        '["도함수", "극값", "최댓값"]'
    ]
    
    for concepts in test_concepts:
        fixed = mapper.fix_key_concepts_parsing(concepts)
        print(f"원본: {concepts}")
        print(f"수정: {fixed}")
        print()