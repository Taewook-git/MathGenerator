#!/usr/bin/env python3
"""
KSAT 수학 문제 생성기 주요 오류 개선 사항
"""

import re
import json
import logging
from typing import Dict, Any, List
from .choice_parser import choice_parser, enhance_choice_parsing
from .answer_mapper import answer_mapper, enhance_problem_data
from .json_fixer import json_fixer

logger = logging.getLogger(__name__)

class ErrorFixer:
    """주요 오류 패턴 수정"""
    
    def __init__(self):
        self.json_cleanup_patterns = [
            # JSON 응답에서 불필요한 마크다운 코드 블록 제거
            (r'```json\s*', ''),
            (r'\s*```', ''),
            # 불완전한 JSON 문자열 처리
            (r'",\s*$', '"'),
            (r',\s*}', '}'),
            (r',\s*]', ']'),
        ]
        
        self.math_expression_fixes = [
            # 한국어 수식 표현을 SymPy 호환 형태로 변환
            (r'∫\[([^\]]+)\]\s*([^d]+)d([a-z])', r'integrate(\2, (\3, \1))'),
            (r'∫\s*([^d]+)d([a-z])', r'integrate(\1, \2)'),
            (r'lim\s*\(([^→]+)→([^)]+)\)\s*([^=]+)', r'limit(\3, \1, \2)'),
            (r'([가-힣\s]+)', ''),  # 한글 제거
            (r'①|②|③|④|⑤', ''),  # 선택지 번호 제거
            (r'[^\w\s\+\-\*\/\^\(\)\.\,\=\<\>]', ''),  # 수학 기호가 아닌 특수문자 제거
        ]
    
    def fix_json_response(self, response_text: str) -> str:
        """AI 응답에서 JSON 추출 및 정리 (향상된 버전)"""
        # 새로운 JSON fixer 사용
        return json_fixer.fix_json(response_text)
    
    def _fix_common_json_errors(self, json_str: str) -> str:
        """일반적인 JSON 오류 수정"""
        # 1. 문자열 내 이스케이프되지 않은 따옴표 수정
        json_str = re.sub(r'(?<!\\)"(?=.*?")', '\\"', json_str)
        
        # 2. 여러 줄 문자열을 단일 줄로 변환
        json_str = re.sub(r'"\s*\n\s*', '"', json_str)
        json_str = re.sub(r'\n\s*"', '"', json_str)
        
        # 3. 끝나지 않은 문자열 처리
        lines = json_str.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 홀수 개의 따옴표가 있는 줄 찾기
            quote_count = line.count('"') - line.count('\\"')
            if quote_count % 2 == 1:
                line += '"'
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _create_fallback_json(self, response_text: str) -> str:
        """JSON 파싱 실패 시 대체 JSON 생성"""
        # 간단한 패턴 매칭으로 정보 추출
        question = self._extract_pattern(response_text, r'question["\']?\s*:\s*["\']([^"\']*)["\']')
        answer = self._extract_pattern(response_text, r'answer["\']?\s*:\s*["\']([^"\']*)["\']')
        
        fallback = {
            "question": question or "문제 생성 중 오류가 발생했습니다.",
            "choices": ["①", "②", "③", "④", "⑤"],
            "answer": answer or "①",
            "solution": "해설을 생성할 수 없습니다.",
            "key_concepts": ["파싱 오류"],
            "requires_graph": False
        }
        
        return json.dumps(fallback, ensure_ascii=False, indent=2)
    
    def _extract_pattern(self, text: str, pattern: str) -> str:
        """정규표현식으로 패턴 추출"""
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1) if match else ""
    
    def fix_math_expression_for_sympy(self, expr: str) -> str:
        """수학 표현식을 SymPy 파싱 가능하도록 수정"""
        if not expr or len(expr.strip()) == 0:
            return ""
        
        fixed = expr
        
        # 수학 표현식 수정 규칙 적용
        for pattern, replacement in self.math_expression_fixes:
            fixed = re.sub(pattern, replacement, fixed)
        
        # 추가적인 정리
        fixed = fixed.strip()
        
        # 너무 복잡하거나 한글이 많이 포함된 경우 빈 문자열 반환
        if len([c for c in fixed if ord(c) > 127]) > len(fixed) * 0.3:
            return ""
        
        # 의미있는 수학식인지 확인
        if not re.search(r'[a-zA-Z0-9\+\-\*/\^\(\)=<>]', fixed):
            return ""
        
        return fixed
    
    def improve_problem_generation_prompt(self, base_prompt: str) -> str:
        """문제 생성 프롬프트 개선"""
        improvements = [
            "\n\n중요한 응답 규칙:",
            "1. 반드시 올바른 JSON 형식으로만 응답하세요.",
            "2. 문자열 내의 따옴표는 반드시 이스케이프(\\)하세요.",
            "3. 여러 줄 문자열은 \\n으로 표현하세요.",
            "4. 수학 기호는 LaTeX가 아닌 유니코드나 텍스트로 표현하세요.",
            "5. 해설은 명확하고 단계별로 작성하세요.",
            "6. 선택지는 반드시 5개를 제공하세요.",
            "7. JSON 외부에 다른 텍스트를 포함하지 마세요.",
        ]
        
        return base_prompt + "\n".join(improvements)

class ProblemValidator:
    """문제 검증 및 품질 확인"""
    
    def __init__(self):
        self.error_fixer = ErrorFixer()
    
    def validate_and_fix_problem(self, problem_data: Dict) -> Dict:
        """문제 검증 및 자동 수정 (개선된 버전)"""
        # 전체 문제 데이터 개선 (정답 매핑, 해설/개념 파싱)
        fixed_problem = enhance_problem_data(problem_data.copy())
        issues = []
        
        # 1. 필수 필드 확인
        required_fields = ['question', 'answer', 'solution']
        for field in required_fields:
            if field not in fixed_problem or not fixed_problem[field]:
                fixed_problem[field] = f"{field} 정보가 누락되었습니다."
                issues.append(f"필수 필드 누락: {field}")
        
        # 2. 선택형 문제의 경우 choices 확인 (개선된 파싱 사용)
        if fixed_problem.get('choices'):
            # 개선된 선택지 파싱 적용
            original_choices = fixed_problem.get('choices', [])
            fixed_problem = enhance_choice_parsing(fixed_problem)
            
            # 파싱 전후 비교
            if fixed_problem.get('choices') != original_choices:
                issues.append("선택지 파싱 및 검증 완료")
        
        # 3. 정답 검증 (이미 enhance_problem_data에서 처리되지만 추가 확인)
        answer = fixed_problem.get('answer', '')
        choices = fixed_problem.get('choices', [])
        
        if choices and answer not in choices:
            # 정답이 선택지에 없으면 첫 번째 선택지로 설정
            if choices:
                fixed_problem['answer'] = choices[0]
                issues.append("정답이 선택지에 없어 첫 번째 선택지로 수정")
        
        # 4. 해설 품질 확인 (이미 파싱은 개선됨)
        solution = fixed_problem.get('solution', '')
        if len(solution) < 50:
            fixed_problem['solution'] += "\n\n추가 설명: 이 문제는 기본 개념을 활용한 표준 문제입니다."
            issues.append("해설이 너무 짧아 보충 설명 추가")
        
        # 5. 핵심 개념 확인 (이미 파싱은 개선됨)
        if 'key_concepts' not in fixed_problem or not fixed_problem['key_concepts']:
            fixed_problem['key_concepts'] = ["수학"]
            issues.append("핵심 개념 누락으로 기본값 설정")
        
        # 6. 검증 결과 추가
        if 'validation_issues' not in fixed_problem:
            fixed_problem['validation_issues'] = []
        fixed_problem['validation_issues'].extend(issues)
        fixed_problem['is_validated'] = len(fixed_problem['validation_issues']) == 0
        
        return fixed_problem

# 전역 인스턴스
error_fixer = ErrorFixer()
problem_validator = ProblemValidator()

def apply_error_fixes_to_generator():
    """기존 생성기에 오류 수정 적용"""
    try:
        from core.problem_generator import KSATMathGenerator
        
        # 원본 메서드 저장
        original_parse_response = KSATMathGenerator._parse_response
        original_create_prompt = KSATMathGenerator._create_prompt
        
        def enhanced_parse_response(self, response_text: str) -> Dict:
            """향상된 응답 파싱"""
            try:
                # 1. JSON 정리 및 수정
                fixed_json = error_fixer.fix_json_response(response_text)
                
                # 2. JSON 파싱
                problem_data = json.loads(fixed_json)
                
                # 3. 문제 검증 및 수정
                validated_problem = problem_validator.validate_and_fix_problem(problem_data)
                
                return validated_problem
                
            except Exception as e:
                logger.error(f"향상된 파싱 실패: {e}")
                # 원본 메서드로 폴백
                return original_parse_response(self, response_text)
        
        def enhanced_create_prompt(self, exam_type: str, problem_type: str, 
                                 topic: str, difficulty: str, points: int) -> str:
            """향상된 프롬프트 생성"""
            base_prompt = original_create_prompt(self, exam_type, problem_type, topic, difficulty, points)
            return error_fixer.improve_problem_generation_prompt(base_prompt)
        
        # 메서드 교체
        KSATMathGenerator._parse_response = enhanced_parse_response
        KSATMathGenerator._create_prompt = enhanced_create_prompt
        
        logger.info("문제 생성기 오류 수정 패치 적용 완료")
        return True
        
    except Exception as e:
        logger.error(f"오류 수정 패치 적용 실패: {e}")
        return False

if __name__ == "__main__":
    # 오류 수정 테스트
    print("오류 수정 시스템 테스트")
    print("=" * 40)
    
    # 1. JSON 수정 테스트
    broken_json = '''```json
    {
        "question": "문제입니다",
        "choices": ["①", "②", "③", "④", "⑤"],
        "answer": "①",
        "solution": "해설입니다.
        계속됩니다.",
    }
    ```'''
    
    fixed = error_fixer.fix_json_response(broken_json)
    print("JSON 수정 테스트:")
    print("수정 전:", broken_json[:50] + "...")
    print("수정 후:", fixed[:50] + "...")
    print()
    
    # 2. 수학식 수정 테스트
    math_expressions = [
        "∫[0부터 pi까지] sin(x)dx",
        "lim(x→0) sin(x)/x", 
        "① 답은 2π입니다",
        "함수 f(x) = x^2에서"
    ]
    
    print("수학식 수정 테스트:")
    for expr in math_expressions:
        fixed = error_fixer.fix_math_expression_for_sympy(expr)
        print(f"  원본: {expr}")
        print(f"  수정: '{fixed}'")
        print()
    
    print("오류 수정 시스템 준비 완료 ✓")