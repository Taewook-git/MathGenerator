import google.generativeai as genai
from typing import Dict, List, Optional
import json
import random
import sys
import os
# Add parent directory to path for imports
if __name__ == "__main__" or "core" in __name__:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import GEMINI_API_KEY, PROBLEM_TYPES, MATH_TOPICS, SPECIALIZED_PROBLEM_TYPES
from generators.graph_generator import MathGraphGenerator
from validators.error_fixes import error_fixer, problem_validator
from generators.ultra_hard_problems import UltraHardProblemGenerator, ULTRA_HARD_CATEGORIES
import re
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)

class KSATMathGenerator:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.fallback_model = genai.GenerativeModel('gemini-2.5-flash')  # 더 관대한 제한의 백업 모델
        self.graph_generator = MathGraphGenerator()
        self.last_request_time = 0
        self.min_request_interval = 30  # 30초 간격으로 요청 (free tier 제한 고려)
        self.use_fallback = False
        
        # 초고난도 문제 생성기
        self.ultra_hard_generator = UltraHardProblemGenerator()
        logger.info("초고난도 문제 생성기 활성화됨")
        
    def generate_problem(self, 
                        problem_type: str = "선택형",
                        topic: str = None,
                        difficulty: str = "중",
                        points: int = 3) -> Dict:
        
        if topic is None:
            topic = random.choice(MATH_TOPICS)
        
        # 특별 주제에 대해서는 세부 유형 선택
        specialized_subtopic = self._select_specialized_subtopic(topic)
        
        prompt = self._create_prompt(problem_type, topic, difficulty, points, specialized_subtopic)
        
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
                            print("gemini-2.5-pro 할당량 초과. gemini-2.5-flash로 전환...")
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
                "problem_type": problem_type,
                "topic": topic,
                "difficulty": difficulty,
                "points": points,
                "suggestion": "API 할당량이 초과되었습니다. 몇 분 후 다시 시도하거나 유료 플랜을 고려해보세요."
            }
    
    def _parse_curriculum_topic(self, topic: str) -> tuple:
        """2015 개정 교육과정 형식의 주제 파싱
        예: "[수학1] 지수함수와 로그함수" -> ("수학1", "지수함수와 로그함수")
        """
        if topic.startswith("[") and "]" in topic:
            parts = topic.split("] ")
            if len(parts) == 2:
                subject = parts[0][1:]  # "[" 제거
                chapter = parts[1]
                return subject, chapter
        return None, topic
    
    def _select_specialized_subtopic(self, topic: str) -> Optional[Dict]:
        """특별 주제에 대해 세부 유형 선택"""
        # 새 교육과정 형식에서 주제 추출
        _, chapter = self._parse_curriculum_topic(topic)
        
        # 특별 주제 매핑
        topic_mapping = {
            "[미적분] 미분법": "[미적분] 미분법",  # e^x, ln x는 미적분에서만
            "[수학1] 삼각함수": "[수학1] 삼각함수"  # 사인법칙, 코사인법칙
        }
        
        # 매핑된 주제 찾기
        mapped_topic = topic_mapping.get(topic) or topic_mapping.get(chapter)
        
        if mapped_topic and mapped_topic in SPECIALIZED_PROBLEM_TYPES:
            subtopic_categories = SPECIALIZED_PROBLEM_TYPES[mapped_topic]
            
            # 가중치 기반 선택 (특정 유형이 더 자주 나오도록)
            if mapped_topic == "[미적분] 미분법":
                # e^x, ln x 문제가 더 자주 나오도록 가중치 설정
                weighted_categories = {
                    "e^x 활용 문제": 0.4,
                    "ln x 활용 문제": 0.4, 
                    "지수로그 미분 복합문제": 0.2
                }
                
                category = random.choices(
                    list(weighted_categories.keys()),
                    weights=list(weighted_categories.values())
                )[0]
                
            elif mapped_topic == "[수학1] 삼각함수":
                # 사인법칙, 코사인법칙이 더 자주 나오도록
                weighted_categories = {
                    "사인 법칙 활용": 0.4,
                    "코사인 법칙 활용": 0.4,
                    "복합 도형문제": 0.2
                }
                
                category = random.choices(
                    list(weighted_categories.keys()),
                    weights=list(weighted_categories.values())
                )[0]
            else:
                # 기타 주제는 균등 선택
                category = random.choice(list(subtopic_categories.keys()))
            
            specific_type = random.choice(subtopic_categories[category])
            
            return {
                "category": category,
                "specific_type": specific_type,
                "all_types": subtopic_categories[category]
            }
        
        return None
    
    def _create_prompt(self, problem_type: str, 
                      topic: str, difficulty: str, points: int, 
                      specialized_subtopic: Optional[Dict] = None) -> str:
        
        # 2015 개정 교육과정 주제 파싱
        subject, chapter = self._parse_curriculum_topic(topic)
        
        # 교육과정 기반 상세 주제 안내
        curriculum_guidance = ""
        if subject and chapter:
            curriculum_guidance = f"""
교육과정 정보:
- 과목: {subject}
- 단원: {chapter}"""
            
            # CURRICULUM_2015에서 세부 항목 가져오기
            from core.config import CURRICULUM_2015
            if subject in CURRICULUM_2015 and chapter in CURRICULUM_2015[subject]:
                subtopics = CURRICULUM_2015[subject][chapter]
                if subtopics:
                    curriculum_guidance += f"\n- 세부 주제: {', '.join(subtopics[:3])}"
        
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
- 한국 교육과정 내에서 최고 난이도"""
        }
        
        # 특별 주제 지침 추가
        specialized_guidance = ""
        if specialized_subtopic:
            specialized_guidance = f"""

🔍 특별 주제 세부 지침:
- 카테고리: {specialized_subtopic['category']}
- 구체적 유형: {specialized_subtopic['specific_type']}
- 이 유형의 문제를 중심으로 출제하되, 아래 관련 유형들도 참고하세요:
"""
            for related_type in specialized_subtopic['all_types'][:3]:
                specialized_guidance += f"  • {related_type}\n"
        
        base_prompt = f"""
한국 대학수학능력시험 수학 문제를 생성해주세요. 실제 평가원이 출제하는 수준의 고품질 문제를 작성하세요.

문제 조건:
- 유형: {problem_type}
- 주제: {topic}
- 난이도: {difficulty}
- 배점: {points}점{curriculum_guidance}{specialized_guidance}

난이도 세부 지침:{difficulty_guide.get(difficulty, '')}

【고품질 문제 작성 기준】
1. **평가 타당성**: 해당 단원의 핵심 개념과 원리를 정확히 평가할 수 있는 문제
2. **문제 완성도**: 
   - 모든 조건이 명확하고 모호함이 없어야 함
   - 불필요한 정보는 배제하고 필요충분한 조건만 제시
   - 수학적 엄밀성과 논리적 일관성 확보
3. **변별력**: 
   - 학생의 수학적 사고력과 문제해결 능력을 측정
   - 단순 계산이 아닌 개념 이해와 적용 능력 평가
   - 난이도에 따른 적절한 사고 단계 요구
4. **오답 설계** (선택형):
   - 전형적인 실수 유형을 반영한 오답
   - 개념 오해에서 비롯된 오답
   - 계산 실수로 인한 오답
   - 부분적 해결에서 멈춘 오답
5. **실제 수능 유형 준수**:
   - 최근 5년간 수능/평가원 기출 문제 스타일 반영
   - 교육과정 성취기준에 부합
   - 실생활 맥락이나 수학 내적 맥락 활용

요구사항:
1. 실제 수능 문제와 동일한 형식과 품질로 작성
2. 문제 조건이 명확하고 답이 유일하게 결정됨
3. 수학적으로 완벽히 정확해야 함
4. 표준 한국어 수학 용어 사용
5. 2015 개정 교육과정 준수
6. 평가 목표가 명확한 문제
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
    "choices": ["정답값", "오답1", "오답2", "오답3", "오답4"],  // 선택형: 정확히 5개의 수치/수식
    "answer": "정답값",  // choices 배열에 있는 정답을 그대로 복사
    "solution": "자세한 풀이 과정 (단계별로 명확하게)",
    "key_concepts": ["핵심 개념1", "핵심 개념2"],
    "difficulty_rationale": "난이도 설정 근거 (왜 이 난이도인지)",
    "common_mistakes": ["흔한 실수1", "흔한 실수2"],  // 학생들이 자주 하는 실수
    "requires_graph": false,  // 대부분 false - 반드시 필요한 경우에만 true
    "graph_type": "trigonometric/geometry/function/vector",  // 그래프 유형 (requires_graph가 true인 경우만)
    "graph_params": {{}}  // 그래프 생성에 필요한 파라미터 (requires_graph가 true인 경우만)
}}

【선택형 문제 필수 규칙】
1. **정답 유일성 보장** (최우선 규칙):
   - 문제의 조건을 정밀하게 설계하여 반드시 단 하나의 정답만 존재하도록 함
   - 모호한 표현이나 다중 해석 가능한 조건 절대 금지
   - 필요시 "단," "여기서," "이때," 등의 제한 조건 명시적 추가
   - 변수의 범위, 정의역, 조건을 명확히 제시
2. **choices 배열**: 반드시 5개의 구체적인 수치나 수식
   - 예시: ["12", "-3", "2√5", "7/3", "0"]
   - 모든 선택지는 계산 가능한 값이어야 함
   - "없음", "모두", "알 수 없음" 같은 추상적 답변 금지
3. **오답 설계 전략**:
   - 오답1: 가장 흔한 계산 실수 결과
   - 오답2: 개념을 잘못 이해했을 때의 결과
   - 오답3: 문제를 부분적으로만 해결했을 때의 결과
   - 오답4: 공식을 잘못 적용했을 때의 결과
4. **정답**: choices 배열의 요소 중 하나를 정확히 복사
5. **변별력**: 각 선택지가 서로 충분히 구별되는 값
"""
        
        # 난이도에 따른 추가 지침
        # 특별 주제별 상세 지침 추가
        if specialized_subtopic:
            if "e^x" in specialized_subtopic['specific_type']:
                base_prompt += f"""\n
🧮 e^x 활용 문제 상세 지침:
- 자연지수함수 e^x의 특별한 성질 활용 (도함수가 자기 자신)
- 미분: (e^x)' = e^x, (e^(f(x)))' = f'(x)·e^(f(x))
- 적분: ∫e^x dx = e^x + C, ∫e^(f(x))·f'(x) dx = e^(f(x)) + C
- 극한: lim(x→∞) e^x = ∞, lim(x→-∞) e^x = 0
- 방정식: e^x = a ⇔ x = ln a (a > 0)
- 실제 수능에서 자주 나오는 유형으로 출제하세요.
"""
            elif "ln x" in specialized_subtopic['specific_type']:
                base_prompt += f"""\n
🧮 ln x 활용 문제 상세 지침:
- 자연로그함수 ln x의 특별한 성질 활용
- 미분: (ln x)' = 1/x, (ln(f(x)))' = f'(x)/f(x)
- 적분: ∫(1/x) dx = ln|x| + C, ∫f'(x)/f(x) dx = ln|f(x)| + C
- 극한: lim(x→0+) ln x = -∞, lim(x→∞) ln x = ∞
- 방정식: ln x = a ⇔ x = e^a
- 로피탈 정리 활용: lim(x→0+) x ln x = 0 등
- 실제 수능에서 자주 나오는 유형으로 출제하세요.
"""
            elif "사인 법칙" in specialized_subtopic['specific_type']:
                base_prompt += f"""\n
📐 사인 법칙 활용 문제 상세 지침:
- 사인 법칙: a/sin A = b/sin B = c/sin C = 2R (R: 외접원의 반지름)
- 삼각형에서 변과 각의 관계를 이용한 문제
- 삼각형의 넓이: S = (1/2)ab sin C
- 실제 수능에서 자주 나오는 유형으로 출제하세요.
"""
            elif "코사인 법칙" in specialized_subtopic['specific_type']:
                base_prompt += f"""\n
📐 코사인 법칙 활용 문제 상세 지침:
- 코사인 법칙: c² = a² + b² - 2ab cos C
- 변의 길이로부터 각 구하기: cos C = (a² + b² - c²)/(2ab)
- 두 변과 그 사잇각으로부터 나머지 변 구하기
- 사각형의 대각선 길이, 입체도형에서의 거리
- 예시: "삼각형 ABC에서 a=5, b=7, ∠C=60°일 때..."
- 실제 수능에서 자주 나오는 유형으로 출제하세요.
"""
        
        # 초고난도 처리 - 명시적으로 요청된 경우에만
        # 난이도 "킬러" 또는 명시적 초고난도 요청 시에만 활성화
        if difficulty == "킬러" or difficulty == "ultra":
            # 초고난도 프롬프트 추가
            fusion_level = random.choice([2, 3, 4])  # 2-4개 단원 융합
            ultra_prompt = self.ultra_hard_generator.create_ultra_hard_prompt(
                topic, 
                fusion_level=fusion_level,
                use_identity=True,
                use_inequality=True
            )
            base_prompt += "\n\n" + ultra_prompt
            base_prompt += "\n\n🔴 초고난도 킬러 문항 생성 모드 활성화됨"
            
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
- 한국 교육과정 내에서 가장 어려운 수준
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
            
        # 오류 방지를 위한 프롬프트 개선
        enhanced_prompt = error_fixer.improve_problem_generation_prompt(base_prompt)
        return enhanced_prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        try:
            # 향상된 JSON 파싱 및 오류 수정
            fixed_json = error_fixer.fix_json_response(response_text)
            parsed_data = json.loads(fixed_json)
            
            # 문제 검증 및 자동 수정
            validated_data = problem_validator.validate_and_fix_problem(parsed_data)
            
            # 기존 답 유일성 검증도 적용
            final_data = self._validate_answer_uniqueness(validated_data)
            return final_data
            
        except Exception as e:
            logger.error(f"응답 파싱 실패: {e}")
            # 폴백 응답 - 더 나은 기본 선택지 제공
            return {
                "question": "문제 생성 중 오류가 발생했습니다. 다시 시도해주세요.",
                "choices": ["1", "2", "3", "4", "5"],  # 선택형의 기본 선택지
                "answer": "1",
                "solution": "응답을 파싱할 수 없습니다.",
                "key_concepts": ["파싱 오류"],
                "parsing_error": str(e)
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
            
            # 선택지가 5개가 아닌 경우 보충
            if len(unique_choices) < 5:
                # 부족한 선택지를 자동 생성
                while len(unique_choices) < 5:
                    # 기존 선택지를 기반으로 변형된 오답 생성
                    if unique_choices and unique_choices[0]:
                        try:
                            # 숫자인 경우 ±1, ±2 등으로 변형
                            base_val = float(unique_choices[0])
                            new_val = str(base_val + len(unique_choices))
                            if new_val not in seen:
                                unique_choices.append(new_val)
                                seen.add(new_val)
                            else:
                                unique_choices.append(f"선택지{len(unique_choices)+1}")
                        except:
                            unique_choices.append(f"선택지{len(unique_choices)+1}")
                    else:
                        unique_choices.append(f"선택지{len(unique_choices)+1}")
                
                problem_data['choices'] = unique_choices
                problem_data['validation_warning'] = problem_data.get('validation_warning', '') + f" 선택지 자동 보충됨"
            elif len(unique_choices) > 5:
                # 초과된 선택지는 제거
                problem_data['choices'] = unique_choices[:5]
                problem_data['validation_warning'] = problem_data.get('validation_warning', '') + f" 선택지 5개로 조정됨"
        
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
    
    def generate_exam_set(self, num_problems: int = 30, include_killer: bool = False) -> List[Dict]:
        problems = []
        config = PROBLEM_TYPES
        
        selective_count = min(num_problems * 7 // 10, config["선택형"]["문항수"])
        short_answer_count = min(num_problems - selective_count, config["단답형"]["문항수"])
        
        # 킬러 문제 포함 시 1-2개 배정
        killer_count = 0
        if include_killer:
            killer_count = min(2, num_problems // 10)  # 전체의 10% 이하, 최대 2개
        
        for i in range(selective_count):
            # 마지막 1-2문제를 킬러로 할당
            if include_killer and i >= selective_count - killer_count:
                difficulty = "킬러"
                points = 4  # 킬러 문제는 최고 배점
            else:
                difficulty = random.choice(config["선택형"]["난이도"])
                points = random.choice(config["선택형"]["배점"])
            
            topic = random.choice(MATH_TOPICS)
            
            problem = self.generate_problem(
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
            topic = random.choice(MATH_TOPICS)
            
            problem = self.generate_problem(
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
    
    def get_quality_statistics(self) -> Dict:
        """품질 통계 조회"""
        return {"error": "품질 강화 시스템이 비활성화되어 있습니다."}
    
    def search_similar_problems(self, question: str, limit: int = 5) -> List[Dict]:
        """유사 문제 검색"""
        return []
    
    def regenerate_with_quality_check(self,
                                    problem_type: str = "선택형",
                                    topic: str = None, difficulty: str = "중",
                                    points: int = 3, max_attempts: int = 3,
                                    min_quality_score: float = 70.0) -> Dict:
        """품질 기준을 만족할 때까지 문제 재생성"""
        
        for attempt in range(max_attempts):
            logger.info(f"문제 생성 시도 {attempt + 1}/{max_attempts}")
            
            problem = self.generate_problem(problem_type, topic, difficulty, points)
            
            # 품질 점수 확인
            quality_score = problem.get('quality_score', 0)
            is_duplicate = problem.get('is_duplicate', False)
            
            if quality_score >= min_quality_score and not is_duplicate:
                logger.info(f"품질 기준 만족 (점수: {quality_score})")
                return problem
            else:
                logger.info(f"품질 기준 미달 (점수: {quality_score}, 중복: {is_duplicate})")
                if attempt < max_attempts - 1:
                    # 잠시 대기 후 재시도
                    time.sleep(5)
        
        logger.warning(f"최대 시도 횟수 초과. 마지막 생성된 문제 반환")
        return problem
    
    def generate_exponential_log_problem(self, 
                                       problem_type: str = "선택형",
                                       difficulty: str = "중", points: int = 3,
                                       focus: str = "both") -> Dict:
        """e^x, ln x 활용 문제 전용 생성 메서드"""
        if focus == "e^x":
            topic = "지수함수와 로그함수"
            # e^x 문제 강제 생성
            specialized_subtopic = {
                "category": "e^x 활용 문제",
                "specific_type": random.choice([
                    "자연지수함수의 미분과 적분",
                    "e^x = a 형태의 지수방정식", 
                    "복합함수 f(e^x)의 미분",
                    "e^x를 포함한 극한값 계산"
                ]),
                "all_types": [
                    "자연지수함수의 미분과 적분",
                    "e^x = a 형태의 지수방정식",
                    "복합함수 f(e^x)의 미분"
                ]
            }
        elif focus == "ln":
            topic = "지수함수와 로그함수"
            # ln x 문제 강제 생성
            specialized_subtopic = {
                "category": "ln x 활용 문제", 
                "specific_type": random.choice([
                    "자연로그함수의 미분과 적분",
                    "ln x = a 형태의 로그방정식",
                    "복합함수 f(ln x)의 미분",
                    "ln x를 포함한 극한값 (로피탈 정리)"
                ]),
                "all_types": [
                    "자연로그함수의 미분과 적분",
                    "ln x = a 형태의 로그방정식",
                    "복합함수 f(ln x)의 미분"
                ]
            }
        else:
            # both - 지수로그 복합 문제
            topic = "지수함수와 로그함수"
            specialized_subtopic = {
                "category": "지수로그 복합문제",
                "specific_type": random.choice([
                    "e^x + ln x 형태의 복합함수",
                    "지수로그함수의 최댓값/최솟값",
                    "지수로그 연립방정식"
                ]),
                "all_types": [
                    "e^x + ln x 형태의 복합함수",
                    "지수로그함수의 최댓값/최솟값",
                    "지수로그 연립방정식"
                ]
            }
        
        prompt = self._create_prompt(problem_type, topic, difficulty, points, specialized_subtopic)
        
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                wait_time = self.min_request_interval - time_since_last
                logger.info(f"Rate limiting: {wait_time:.1f}초 대기 중...")
                time.sleep(wait_time)
            
            self.last_request_time = time.time()
            current_model = self.fallback_model if self.use_fallback else self.model
            response = current_model.generate_content(prompt)
            problem_data = self._parse_response(response.text)
            
            problem_data.update({
                "problem_type": problem_type,
                "topic": topic,
                "difficulty": difficulty,
                "points": points,
                "specialized_focus": focus,
                "specialized_subtopic": specialized_subtopic
            })
            
            
            return problem_data
            
        except Exception as e:
            return {
                "error": f"e^x/ln x 문제 생성 중 오류 발생: {str(e)}",
                "problem_type": problem_type, 
                "topic": topic,
                "difficulty": difficulty,
                "points": points,
                "specialized_focus": focus
            }
    
    def generate_trigonometric_law_problem(self,
                                         problem_type: str = "선택형", 
                                         difficulty: str = "중", points: int = 3,
                                         law_type: str = "both") -> Dict:
        """사인법칙, 코사인법칙 활용 도형문제 전용 생성 메서드"""
        topic = "삼각법칙 도형문제"
        
        if law_type == "sine":
            # 사인법칙 문제 강제 생성
            specialized_subtopic = {
                "category": "사인 법칙 활용",
                "specific_type": random.choice([
                    "삼각형의 변의 길이 구하기",
                    "삼각형의 각의 크기 구하기",
                    "외접원의 반지름 구하기", 
                    "높이를 이용한 거리 측정"
                ]),
                "all_types": [
                    "삼각형의 변의 길이 구하기",
                    "삼각형의 각의 크기 구하기",
                    "외접원의 반지름 구하기"
                ]
            }
        elif law_type == "cosine":
            # 코사인법칙 문제 강제 생성
            specialized_subtopic = {
                "category": "코사인 법칙 활용",
                "specific_type": random.choice([
                    "삼각형의 변의 길이 구하기",
                    "삼각형의 각의 크기 구하기",
                    "사각형의 대각선 길이",
                    "입체도형에서의 거리 계산"
                ]),
                "all_types": [
                    "삼각형의 변의 길이 구하기",
                    "삼각형의 각의 크기 구하기", 
                    "사각형의 대각선 길이"
                ]
            }
        else:
            # both - 복합 도형문제
            specialized_subtopic = {
                "category": "복합 도형문제",
                "specific_type": random.choice([
                    "사인법칙과 코사인법칙 동시 사용",
                    "삼각형과 원의 복합문제",
                    "입체도형에서의 각도와 거리",
                    "삼각측량을 이용한 실생활 문제"
                ]),
                "all_types": [
                    "사인법칙과 코사인법칙 동시 사용",
                    "삼각형과 원의 복합문제",
                    "입체도형에서의 각도와 거리"
                ]
            }
        
        prompt = self._create_prompt(problem_type, topic, difficulty, points, specialized_subtopic)
        
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                wait_time = self.min_request_interval - time_since_last
                logger.info(f"Rate limiting: {wait_time:.1f}초 대기 중...")
                time.sleep(wait_time)
            
            self.last_request_time = time.time()
            current_model = self.fallback_model if self.use_fallback else self.model
            response = current_model.generate_content(prompt)
            problem_data = self._parse_response(response.text)
            
            problem_data.update({
                "problem_type": problem_type,
                "topic": topic,
                "difficulty": difficulty,
                "points": points,
                "law_type_focus": law_type,
                "specialized_subtopic": specialized_subtopic
            })
            
            
            return problem_data
            
        except Exception as e:
            return {
                "error": f"삼각법칙 도형 문제 생성 중 오류 발생: {str(e)}",
                "problem_type": problem_type,
                "topic": topic, 
                "difficulty": difficulty,
                "points": points,
                "law_type_focus": law_type
            }
    
    def generate_ultra_hard_problem(self,
                                   problem_type: str = "선택형",
                                   base_topic: str = None,
                                   fusion_level: int = 3,
                                   category: str = None) -> Dict:
        """초고난도 킬러 문제 전용 생성 메서드
        
        Args:
            problem_type: 문제 유형 (선택형/단답형)
            base_topic: 기본 주제
            fusion_level: 융합 단원 수 (2-4)
            category: 초고난도 카테고리 (항등식_마스터, 융합_마스터, 부등식_마스터, 극한_마스터)
        """
        
        # 기본 주제 선택
        if base_topic is None:
            base_topic = random.choice(MATH_TOPICS)
        
        # 카테고리 선택
        if category is None:
            category = random.choice(list(ULTRA_HARD_CATEGORIES.keys()))
        
        category_info = ULTRA_HARD_CATEGORIES[category]
        
        # 초고난도 프롬프트 생성
        ultra_prompt = self.ultra_hard_generator.create_ultra_hard_prompt(
            base_topic,
            fusion_level=fusion_level,
            use_identity=(category == "항등식_마스터"),
            use_inequality=(category == "부등식_마스터")
        )
        
        # 기본 프롬프트에 초고난도 지침 추가
        prompt = f"""
한국 대학수학능력시험 수학 킬러(Killer) 문항을 생성해주세요.

📌 문제 조건:
- 유형: {problem_type}
- 기본 주제: {base_topic}
- 카테고리: {category}
- 융합 레벨: {fusion_level}개 단원 융합
- 난이도: 킬러 (최상위 1%)
- 배점: 4점 (최고 배점)

📌 카테고리 특성:
- {category_info['description']}
- 필요 기술: {', '.join(category_info['required_skills'])}
- 최소 난이도 점수: {category_info['min_score']}/100

{ultra_prompt}

🔴 반드시 지켜야 할 사항:
1. 실제 수능 킬러 문항(21, 29, 30번) 수준 이상의 난이도
2. 여러 개념의 깊이 있는 융합
3. 표준적인 접근으로는 해결 불가능
4. 창의적 사고와 깊은 통찰 필요
5. 계산보다는 개념적 이해와 논리가 핵심

응답 형식(JSON):
{{
    "question": "문제 내용 (명확한 수학적 조건과 함께)",
    "choices": ["정답", "오답1", "오답2", "오답3", "오답4"],  // 선택형: 구체적 수치 5개
    "answer": "정답",  // choices 중 하나와 정확히 일치
    "solution": "자세한 풀이 과정 (단계별로 명확하게)",
    "key_concepts": ["핵심 개념1", "핵심 개념2", "핵심 개념3"],
    "difficulty_analysis": "난이도 분석 및 출제 의도",
    "common_mistakes": ["흔한 실수1", "흔한 실수2"],
    "ultra_difficulty_score": 95,  // 100점 만점 난이도 점수
    "requires_graph": false
}}

【중요】
- 문제문은 한글로 작성하되, 수식은 명확히 구분
- 조건 (가), (나), (다) 형식 사용 시 각 조건을 명확히 서술
- 선택지는 반드시 계산 가능한 구체적 수치나 수식
- 수식 표기: f(x), g(x), sin(x), e^x, ln(x) 등 표준 형식 사용
"""
        
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                wait_time = self.min_request_interval - time_since_last
                logger.info(f"Rate limiting: {wait_time:.1f}초 대기 중...")
                time.sleep(wait_time)
            
            self.last_request_time = time.time()
            
            # 초고난도 문제는 항상 고성능 모델 사용
            response = self.model.generate_content(prompt)
            problem_data = self._parse_response(response.text)
            
            # 초고난도 문제 메타데이터 추가
            problem_data.update({
                "problem_type": problem_type,
                "topic": base_topic,
                "difficulty": "킬러",
                "points": 4,
                "ultra_hard_category": category,
                "fusion_level": fusion_level
            })
            
            # 초고난도 난이도 분석
            ultra_analysis = self.ultra_hard_generator.analyze_ultra_difficulty(problem_data)
            problem_data["ultra_difficulty_analysis"] = ultra_analysis
            
            return problem_data
            
        except Exception as e:
            return {
                "error": f"초고난도 문제 생성 중 오류 발생: {str(e)}",
                "problem_type": problem_type,
                "topic": base_topic,
                "difficulty": "킬러",
                "ultra_hard_category": category
            }