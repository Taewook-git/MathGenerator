import google.generativeai as genai
from typing import Dict, List, Optional
import json
import random
from config import GEMINI_API_KEY, PROBLEM_TYPES, MATH_TOPICS
from graph_generator import MathGraphGenerator
import re

genai.configure(api_key=GEMINI_API_KEY)

class KSATMathGenerator:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.graph_generator = MathGraphGenerator()
        
    def generate_problem(self, 
                        exam_type: str = "가형",
                        problem_type: str = "선택형",
                        topic: str = None,
                        difficulty: str = "중",
                        points: int = 3) -> Dict:
        
        if topic is None:
            topic = random.choice(MATH_TOPICS[exam_type])
        
        prompt = self._create_prompt(exam_type, problem_type, topic, difficulty, points)
        
        try:
            response = self.model.generate_content(prompt)
            problem_data = self._parse_response(response.text)
            problem_data.update({
                "exam_type": exam_type,
                "problem_type": problem_type,
                "topic": topic,
                "difficulty": difficulty,
                "points": points
            })
            
            # 그래프가 필요한 문제인지 확인하고 생성
            graph_image = self._generate_graph_if_needed(problem_data, topic)
            if graph_image:
                problem_data["graph"] = graph_image
            
            return problem_data
        except Exception as e:
            return {
                "error": f"문제 생성 중 오류 발생: {str(e)}",
                "exam_type": exam_type,
                "problem_type": problem_type,
                "topic": topic,
                "difficulty": difficulty,
                "points": points
            }
    
    def _create_prompt(self, exam_type: str, problem_type: str, 
                      topic: str, difficulty: str, points: int) -> str:
        
        # 난이도에 따른 추가 지침
        difficulty_guide = {
            "하": """
- 기본 개념을 활용한 직접적인 계산 문제
- 1~2단계의 사고 과정
- 단순한 공식 적용""",
            "중": """
- 여러 개념을 융합한 문제
- 3~4단계의 사고 과정 필요
- 변형된 형태의 공식 활용
- 논리적 추론 포함""",
            "상": """
- 다양한 수학적 개념을 통합한 심화 문제
- 5단계 이상의 복잡한 사고 과정
- 여러 공식의 창의적 조합
- 조건의 변화에 따른 결과 분석
- 최소값, 최댓값, 존재성 등 심화 주제
- 역사고력 필요 (결과로부터 조건 추론)
- 한국 고등학교 교육과정 내에서 최고 난이도"""
        }
        
        base_prompt = f"""
한국 대학수학능력시험 {exam_type} 수학 문제를 생성해주세요.

문제 조건:
- 유형: {problem_type}
- 주제: {topic}
- 난이도: {difficulty}
- 배점: {points}점

난이도 세부 지침:{difficulty_guide.get(difficulty, '')}

요구사항:
1. 실제 수능 문제와 유사한 형식과 난이도로 작성
2. 문제 상황이 명확하고 논리적이어야 함
3. 수학적으로 정확해야 함
4. 한국어로 작성
5. 한국 고등학교 교육과정을 준수 (미적분, 확률과 통계, 기하와 벡터, 함수, 삼각함수 등)
5. 수식 표현 규칙:
   - LaTeX 명령어를 직접 사용하지 말고 자연스러운 수식 표현 사용
   - 분수는 a/b 또는 \\frac{{a}}{{b}} 형식
   - 지수는 x^2, x^n 형식 
   - 제곱근은 √x 또는 \\sqrt{{x}} 형식
   - 적분은 ∫ 기호 사용
   - 극한은 lim 사용
   - 삼각함수는 sin x, cos x, tan x 형식
   - 로그는 log_a(x) 형식
   - 벡터는 →a, →b 또는 \\vec{{a}} 형식
   - 집합은 {{x | 조건}} 형식
   - 예시: "함수 f(x) = x² + 2x + 1에서..." (O)
   - 예시: "함수 $f(x) = x^2 + 2x + 1$에서..." (X, LaTeX 기호 사용 금지)

응답 형식(JSON):
{{
    "question": "문제 내용",
    "choices": ["선택지1", "선택지2", "선택지3", "선택지4", "선택지5"],  // 선택형인 경우
    "answer": "정답",
    "solution": "자세한 풀이 과정",
    "key_concepts": ["핵심 개념1", "핵심 개념2"],
    "requires_graph": true/false,  // 그래프나 도형이 필요한지 여부
    "graph_type": "trigonometric/geometry/function/vector",  // 그래프 유형 (requires_graph가 true인 경우)
    "graph_params": {{}}  // 그래프 생성에 필요한 파라미터
}}
"""
        
        # 난이도에 따른 추가 지침
        if difficulty == "상":
            base_prompt += """\n
심화 문제 생성 방향:
- 주요 고난도 주제 예시 
미적분:
미분계수의 부호를 이용한 그래프 개형 추론 및 함수식 구하기.
기하:
공간도형의 성질을 이해하고 점, 선, 면의 관계를 파악하는 문제.
수열:
점화식이나 수열의 규칙성을 파악하고 일반항을 유도하여 값을 구하는 문제.
- 여러 개념을 통합한 복합 문제
- 조건부 확률, 함수의 극댓값/극소값
- 역함수, 합성함수, 매개변수 함수
- 벡터의 내적, 외적 활용
- 정적분과 미분의 고급 활용
- 한국 고등학교 교육과정 내에서 가장 어려운 수준
"""
        elif difficulty == "중" and points >= 4:
            base_prompt += """\n
중상급 문제 생성 방향:
- 함수와 도형의 성질을 활용한 문제
- 삼각함수와 벡터의 조합
- 확률 분포와 통계적 추정
"""
        
        if problem_type == "선택형":
            base_prompt += "\n선택지는 반드시 5개(①~⑤)를 제공하세요."
            if difficulty == "상":
                base_prompt += "\n선택지는 서로 유사하면서도 세밀하게 구분되어야 합니다."
        else:
            base_prompt += "\n단답형 문제이므로 답은 자연수 또는 유리수로 제공하세요."
            if difficulty == "상":
                base_prompt += "\n계산 과정이 복잡하고 실수 가능성이 높은 문제로 만드세요."
            
        return base_prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("JSON 형식을 찾을 수 없습니다.")
            
            json_str = response_text[json_start:json_end]
            return json.loads(json_str)
        except json.JSONDecodeError:
            lines = response_text.strip().split('\n')
            return {
                "question": response_text,
                "choices": [],
                "answer": "파싱 오류",
                "solution": "응답을 파싱할 수 없습니다.",
                "key_concepts": []
            }
    
    def generate_exam_set(self, exam_type: str = "가형", num_problems: int = 30) -> List[Dict]:
        problems = []
        config = PROBLEM_TYPES[exam_type]
        
        selective_count = min(num_problems * 7 // 10, config["선택형"]["문항수"])
        short_answer_count = min(num_problems - selective_count, config["단답형"]["문항수"])
        
        for i in range(selective_count):
            difficulty = random.choice(config["선택형"]["난이도"])
            points = random.choice(config["선택형"]["배점"])
            topic = random.choice(MATH_TOPICS[exam_type])
            
            problem = self.generate_problem(
                exam_type=exam_type,
                problem_type="선택형",
                topic=topic,
                difficulty=difficulty,
                points=points
            )
            problem["number"] = i + 1
            problems.append(problem)
        
        for i in range(short_answer_count):
            difficulty = random.choice(config["단답형"]["난이도"])
            points = random.choice(config["단답형"]["배점"])
            topic = random.choice(MATH_TOPICS[exam_type])
            
            problem = self.generate_problem(
                exam_type=exam_type,
                problem_type="단답형",
                topic=topic,
                difficulty=difficulty,
                points=points
            )
            problem["number"] = selective_count + i + 1
            problems.append(problem)
        
        return problems
    
    def _generate_graph_if_needed(self, problem_data: Dict, topic: str) -> Optional[str]:
        """
        문제에 그래프가 필요한지 확인하고 생성
        """
        # AI가 그래프가 필요하다고 명시한 경우
        if problem_data.get('requires_graph'):
            graph_type = problem_data.get('graph_type', 'function')
            graph_params = problem_data.get('graph_params', {})
            
            if graph_type == 'trigonometric':
                functions = graph_params.get('functions', ['sin', 'cos'])
                x_range = graph_params.get('x_range', (-2*3.14159, 2*3.14159))
                return self.graph_generator.generate_trigonometric_graph(
                    functions=functions,
                    x_range=tuple(x_range) if isinstance(x_range, list) else x_range,
                    title=graph_params.get('title', '삼각함수 그래프')
                )
            elif graph_type == 'geometry':
                figure_type = graph_params.get('figure_type', 'triangle')
                return self.graph_generator.generate_geometry_figure(
                    figure_type=figure_type,
                    params=graph_params
                )
            elif graph_type == 'function':
                function_str = graph_params.get('function', 'x**2')
                x_range = graph_params.get('x_range', (-10, 10))
                return self.graph_generator.generate_function_graph(
                    function_str=function_str,
                    x_range=tuple(x_range) if isinstance(x_range, list) else x_range,
                    title=graph_params.get('title', '함수 그래프')
                )
            elif graph_type == 'vector':
                vectors = graph_params.get('vectors', [(1, 2, 'a'), (2, 1, 'b')])
                return self.graph_generator.generate_vector_diagram(
                    vectors=vectors,
                    title=graph_params.get('title', '벡터 다이어그램')
                )
        
        # 주제에 따라 자동으로 그래프 생성
        question_text = problem_data.get('question', '').lower()
        
        # 삼각함수 관련 키워드 확인
        if topic == "삼각함수" or any(word in question_text for word in ['sin', 'cos', 'tan', '사인', '코사인', '탄젠트']):
            # 문제에서 언급된 삼각함수 찾기
            functions = []
            if 'sin' in question_text or '사인' in question_text:
                functions.append('sin')
            if 'cos' in question_text or '코사인' in question_text:
                functions.append('cos')
            if 'tan' in question_text or '탄젠트' in question_text:
                functions.append('tan')
            
            if functions:
                return self.graph_generator.generate_trigonometric_graph(
                    functions=functions if functions else ['sin', 'cos'],
                    title='삼각함수 그래프'
                )
        
        # 기하 관련 키워드 확인
        if topic == "기하와 벡터" or any(word in question_text for word in ['삼각형', '원', '직사각형', '정사각형', '벡터']):
            if '삼각형' in question_text:
                return self.graph_generator.generate_geometry_figure(
                    figure_type='triangle',
                    params={'title': '삼각형', 'show_sides': True}
                )
            elif '원' in question_text:
                return self.graph_generator.generate_geometry_figure(
                    figure_type='circle',
                    params={'title': '원', 'show_radius': True, 'radius': 2}
                )
            elif '직사각형' in question_text or '정사각형' in question_text:
                return self.graph_generator.generate_geometry_figure(
                    figure_type='rectangle',
                    params={'title': '사각형'}
                )
            elif '벡터' in question_text:
                return self.graph_generator.generate_vector_diagram(
                    vectors=[(2, 3, 'a'), (3, 1, 'b'), (-1, 2, 'c')],
                    title='벡터 다이어그램'
                )
        
        # 좌표평면 관련 키워드 확인
        if any(word in question_text for word in ['좌표', '점', '좌표평면']):
            return self.graph_generator.generate_geometry_figure(
                figure_type='coordinate_system',
                params={'title': '좌표평면', 'points': [(1, 2), (3, 1), (2, 4)]}
            )
        
        # 일반 함수 그래프 (2차함수, 지수함수 등)
        if any(word in question_text for word in ['함수', '그래프', '곡선']):
            if '2차' in question_text or '포물선' in question_text:
                return self.graph_generator.generate_function_graph(
                    function_str='x**2 - 2*x + 1',
                    title='2차 함수 그래프'
                )
            elif '지수' in question_text:
                return self.graph_generator.generate_function_graph(
                    function_str='2**x',
                    title='지수함수 그래프'
                )
            elif '로그' in question_text:
                return self.graph_generator.generate_function_graph(
                    function_str='np.log(x)',
                    x_range=(0.1, 10),
                    title='로그함수 그래프'
                )
        
        return None
    
    def save_problems_to_file(self, problems: List[Dict], filename: str = "exam_problems.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(problems, f, ensure_ascii=False, indent=2)
        return filename