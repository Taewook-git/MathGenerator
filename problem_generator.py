import google.generativeai as genai
from typing import Dict, List, Optional
import json
import random
from config import GEMINI_API_KEY, PROBLEM_TYPES, MATH_TOPICS
from graph_generator import MathGraphGenerator
import re
import time

genai.configure(api_key=GEMINI_API_KEY)

class KSATMathGenerator:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.fallback_model = genai.GenerativeModel('gemini-1.5-flash')  # 더 관대한 제한의 백업 모델
        self.graph_generator = MathGraphGenerator()
        self.last_request_time = 0
        self.min_request_interval = 30  # 30초 간격으로 요청 (free tier 제한 고려)
        self.use_fallback = False
        
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
            # Rate limiting - 최소 간격 대기
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                wait_time = self.min_request_interval - time_since_last
                print(f"Rate limiting: {wait_time:.1f}초 대기 중...")
                time.sleep(wait_time)
            
            # API 호출 시도 (재시도 로직 포함)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.last_request_time = time.time()
                    # 사용할 모델 선택 (fallback 모드인지 확인)
                    current_model = self.fallback_model if self.use_fallback else self.model
                    response = current_model.generate_content(prompt)
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
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    if "429" in error_str or "quota" in error_str.lower():
                        # quota 초과 에러인 경우
                        if not self.use_fallback and attempt == 0:
                            # 첫 번째 시도에서 실패하면 fallback 모델로 전환
                            print("gemini-2.5-pro 할당량 초과. gemini-1.5-flash로 전환...")
                            self.use_fallback = True
                            self.min_request_interval = 5  # flash는 더 관대함
                            continue
                        elif attempt < max_retries - 1:
                            # retry_delay 파싱 시도
                            import re
                            delay_match = re.search(r'retry_delay.*?seconds:\s*(\d+)', error_str)
                            wait_time = int(delay_match.group(1)) + 5 if delay_match else 35
                            print(f"API 할당량 초과. {wait_time}초 후 재시도... ({attempt + 1}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                    raise api_error
            
        except Exception as e:
            return {
                "error": f"문제 생성 중 오류 발생: {str(e)}",
                "exam_type": exam_type,
                "problem_type": problem_type,
                "topic": topic,
                "difficulty": difficulty,
                "points": points,
                "suggestion": "API 할당량이 초과되었습니다. 몇 분 후 다시 시도하거나 유료 플랜을 고려해보세요."
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
6. **중요: 답은 반드시 하나만 존재해야 함** - 문제 조건을 명확히 하여 답이 유일하게 결정되도록 함
7. 수식 표현 규칙:
   - LaTeX 명령어를 직접 사용하지 말고 자연스러운 수식 표현 사용
   - 분수는 a/b 또는 (a)/(b) 형식 (복잡한 분수의 경우)
   - 지수는 x^2, x^n 형식 
   - 제곱근은 √x 또는 √(복잡한식) 형식
   - 적분은 ∫ 기호 사용: ∫f(x)dx 또는 ∫[a부터b까지]f(x)dx
   - 극한 표현:
     * lim(x→a) f(x) 또는 lim[x→a] f(x)
     * lim(x→∞) f(x) 또는 lim[x→∞] f(x)  
     * lim(x→0⁺) f(x) (우극한), lim(x→0⁻) f(x) (좌극한)
     * 예시: "lim(x→2) (x²-4)/(x-2)의 값은?"
   - 삼각함수는 sin x, cos x, tan x 형식
   - 로그는 log x, ln x, log₂ x 형식
   - 벡터는 →a, →b 형식 (화살표 사용)
   - 집합은 {{x | 조건}} 형식
   - 절댓값은 |x| 형식
   - 예시: "함수 f(x) = x² + 2x + 1에서..." (O)
   - 예시: "lim(x→1) (x²-1)/(x-1) = 2" (O)
   - 예시: "함수 $f(x) = x^2 + 2x + 1$에서..." (X, LaTeX 기호 사용 금지)

그래프 생성 지침:
- requires_graph는 문제 해결을 위해 시각적 그래프가 반드시 필요한 경우에만 true로 설정
- 다음 경우에만 그래프 생성 요청:
  * 함수의 개형을 분석해야 하는 문제
  * 도형의 성질을 시각적으로 확인해야 하는 기하 문제
  * 삼각함수의 주기나 진폭을 분석하는 문제
- 단순 계산 문제, 공식 적용 문제, 논리 추론 문제는 requires_graph: false

응답 형식(JSON):
{{
    "question": "문제 내용",
    "choices": ["선택지1", "선택지2", "선택지3", "선택지4", "선택지5"],  // 선택형인 경우
    "answer": "정답",
    "solution": "자세한 풀이 과정",
    "key_concepts": ["핵심 개념1", "핵심 개념2"],
    "requires_graph": false,  // 대부분 false - 반드시 필요한 경우에만 true
    "graph_type": "trigonometric/geometry/function/vector",  // 그래프 유형 (requires_graph가 true인 경우만)
    "graph_params": {{}}  // 그래프 생성에 필요한 파라미터 (requires_graph가 true인 경우만)
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
            parsed_data = json.loads(json_str)
            
            # 답 유일성 검증
            validated_data = self._validate_answer_uniqueness(parsed_data)
            return validated_data
            
        except json.JSONDecodeError:
            lines = response_text.strip().split('\n')
            return {
                "question": response_text,
                "choices": [],
                "answer": "파싱 오류",
                "solution": "응답을 파싱할 수 없습니다.",
                "key_concepts": []
            }
    
    def _validate_answer_uniqueness(self, problem_data: Dict) -> Dict:
        """
        답이 유일한지 검증하고 필요시 수정
        """
        choices = problem_data.get('choices', [])
        answer = problem_data.get('answer', '')
        
        # 선택형 문제의 경우
        if choices:
            # 정답이 선택지에 있는지 확인
            if answer not in choices:
                # 정답이 선택지에 없으면 첫 번째 선택지를 정답으로 설정
                if choices:
                    problem_data['answer'] = choices[0]
                    problem_data['validation_warning'] = "정답이 선택지에 없어 첫 번째 선택지로 수정됨"
            
            # 중복 선택지 제거
            unique_choices = []
            seen = set()
            for choice in choices:
                if choice not in seen:
                    unique_choices.append(choice)
                    seen.add(choice)
            
            if len(unique_choices) != len(choices):
                problem_data['choices'] = unique_choices
                problem_data['validation_warning'] = problem_data.get('validation_warning', '') + " 중복 선택지 제거됨"
            
            # 선택지가 5개가 아닌 경우 경고
            if len(unique_choices) != 5:
                problem_data['validation_warning'] = problem_data.get('validation_warning', '') + f" 선택지 개수: {len(unique_choices)}개"
        
        # 단답형 문제의 경우 답이 숫자인지 확인
        else:
            try:
                # 답이 숫자인지 확인
                float(answer)
            except (ValueError, TypeError):
                # 숫자가 아닌 경우 경고 추가
                if answer not in ["파싱 오류"]:
                    problem_data['validation_warning'] = problem_data.get('validation_warning', '') + " 단답형 답이 숫자가 아님"
        
        return problem_data
    
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
        문제에 그래프가 필요한지 확인하고 생성 - 매우 보수적으로, AI가 명시적으로 요청한 경우에만
        """
        # AI가 명시적으로 그래프가 필요하다고 표시한 경우에만 생성
        if not problem_data.get('requires_graph', False):
            return None
            
        graph_type = problem_data.get('graph_type', 'function')
        graph_params = problem_data.get('graph_params', {})
        
        try:
            if graph_type == 'trigonometric':
                functions = graph_params.get('functions', ['sin', 'cos'])
                x_range = graph_params.get('x_range', (-2*3.14159, 2*3.14159))
                return self.graph_generator.generate_trigonometric_graph(
                    functions=functions,
                    x_range=tuple(x_range) if isinstance(x_range, list) else x_range,
                    title=graph_params.get('title', '')
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
                    title=graph_params.get('title', '')
                )
            elif graph_type == 'vector':
                vectors = graph_params.get('vectors', [(1, 2, 'a'), (2, 1, 'b')])
                return self.graph_generator.generate_vector_diagram(
                    vectors=vectors,
                    title=graph_params.get('title', '')
                )
        except Exception as e:
            # 그래프 생성 실패 시 None 반환 (문제 생성은 계속)
            print(f"그래프 생성 실패: {str(e)}")
            return None
        
        return None
    
    def save_problems_to_file(self, problems: List[Dict], filename: str = "exam_problems.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(problems, f, ensure_ascii=False, indent=2)
        return filename