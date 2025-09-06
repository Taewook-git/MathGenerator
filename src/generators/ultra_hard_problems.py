"""
초고난도 문제 생성 시스템
2015 개정 교육과정 기반 (수학1, 수학2, 미적분)
항등식, 다단원 융합, 부등식 조건 활용
"""

from typing import Dict, List, Optional
import random

class UltraHardProblemGenerator:
    """초고난도 문제 생성 전문 클래스 (2015 개정 교육과정)"""
    
    def __init__(self):
        # 항등식 문제 템플릿
        self.identity_templates = {
            "삼각항등식": {
                "patterns": [
                    "sin²x + cos²x = 1",
                    "1 + tan²x = sec²x", 
                    "1 + cot²x = csc²x",
                    "sin(2x) = 2sin(x)cos(x)",
                    "cos(2x) = cos²x - sin²x = 2cos²x - 1 = 1 - 2sin²x",
                    "tan(2x) = 2tan(x)/(1 - tan²x)"
                ],
                "problem_types": [
                    "항등식을 만족하는 함수 f(x) 결정",
                    "항등식 조건 하에서 극값 구하기",
                    "항등식을 이용한 적분 계산",
                    "항등식과 미분방정식 연결"
                ]
            },
            "지수로그항등식": {
                "patterns": [
                    "e^(ln x) = x (x > 0)",
                    "ln(e^x) = x",
                    "a^(log_a x) = x (a > 0, a ≠ 1, x > 0)",
                    "log_a(a^x) = x",
                    "e^x · e^y = e^(x+y)",
                    "ln(xy) = ln x + ln y"
                ],
                "problem_types": [
                    "항등식을 이용한 방정식 풀이",
                    "복합함수에서 항등식 적용",
                    "극한값 계산에 항등식 활용",
                    "미분과 항등식 결합"
                ]
            },
            "대수항등식": {
                "patterns": [
                    "(a + b)³ = a³ + 3a²b + 3ab² + b³",
                    "(a - b)³ = a³ - 3a²b + 3ab² - b³",
                    "a³ + b³ = (a + b)(a² - ab + b²)",
                    "a³ - b³ = (a - b)(a² + ab + b²)",
                    "a⁴ - b⁴ = (a² - b²)(a² + b²)"
                ],
                "problem_types": [
                    "항등식을 이용한 인수분해",
                    "항등식 조건에서 최댓값/최솟값",
                    "수열의 일반항 유도",
                    "정적분 계산에 활용"
                ]
            }
        }
        
        # 다단원 융합 문제 패턴 (2015 개정 교육과정)
        self.fusion_patterns = {
            "[수학1+수학2] 삼각함수와 미분": {
                "concepts": ["삼각함수", "도함수", "극값", "사인법칙", "코사인법칙"],
                "problem_types": [
                    "삼각함수의 도함수와 극값 구하기",
                    "삼각함수 그래프의 접선 방정식",
                    "사인/코사인 법칙과 최적화 문제",
                    "삼각함수의 최댓값/최솟값",
                    "주기함수의 평균변화율"
                ]
            },
            "[수학1+미적분] 지수로그와 미적분": {
                "concepts": ["지수함수", "로그함수", "e^x", "ln x", "미분법", "적분법"],
                "problem_types": [
                    "e^x와 ln x의 미분과 적분",
                    "지수로그 합성함수의 미분",
                    "로그미분법 활용",
                    "지수적 증가/감소 모델",
                    "자연로그를 포함한 적분"
                ]
            },
            "[수학1+수학2] 수열과 적분": {
                "concepts": ["등차수열", "등비수열", "수열의 합", "정적분"],
                "problem_types": [
                    "수열의 합과 정적분의 관계",
                    "리만 합으로 정의된 수열",
                    "수열로 표현된 함수의 적분",
                    "수학적 귀납법과 적분",
                    "계단함수의 정적분"
                ]
            },
            "[수학2+미적분] 극한과 미적분": {
                "concepts": ["함수의 극한", "연속성", "미분가능성", "적분"],
                "problem_types": [
                    "미적분학의 기본정리 응용",
                    "연속이지만 미분불가능한 점",
                    "극한과 도함수의 관계",
                    "평균값 정리와 롤의 정리",
                    "정적분으로 정의된 함수"
                ]
            },
            "[미적분] 고급 미적분 기법": {
                "concepts": ["부분적분", "치환적분", "이상적분", "매개변수 미분", "음함수 미분"],
                "problem_types": [
                    "복잡한 부분적분 문제",
                    "삼각치환을 이용한 적분",
                    "이상적분의 수렴성 판정",
                    "매개변수로 나타낸 함수의 미적분",
                    "음함수 미분법과 관련 방정식"
                ]
            }
        }
        
        # 부등식 조건 문제 패턴
        self.inequality_patterns = {
            "최적화문제": {
                "constraints": [
                    "f(x) ≥ 0 조건에서 g(x) 최대화",
                    "|f(x) - a| < ε 조건에서 해의 범위",
                    "f(x) ≤ g(x) ≤ h(x) 조건 만족",
                    "∫f(x)dx ≥ k 조건에서 f(x) 결정"
                ],
                "techniques": [
                    "라그랑주 승수법",
                    "KKT 조건",
                    "젠센 부등식",
                    "코시-슈바르츠 부등식",
                    "산술-기하 평균 부등식"
                ]
            },
            "존재성문제": {
                "constraints": [
                    "f(x) > 0인 x가 존재할 조건",
                    "f(x) = g(x)가 해를 가질 조건",
                    "수열이 수렴할 필요충분조건",
                    "적분이 수렴할 조건"
                ],
                "techniques": [
                    "중간값 정리",
                    "롤의 정리",
                    "평균값 정리",
                    "단조수렴정리",
                    "볼차노-바이어슈트라스 정리"
                ]
            },
            "범위제한문제": {
                "constraints": [
                    "0 < x < 1에서 f(x) 성질",
                    "sin x > 0인 구간에서 적분",
                    "log x가 정의되는 범위에서 최댓값",
                    "√(f(x))가 실수인 x의 범위"
                ],
                "techniques": [
                    "구간 분할",
                    "경계값 분석",
                    "연속성 활용",
                    "미분가능성 조건",
                    "적분가능성 조건"
                ]
            }
        }
        
    def create_ultra_hard_prompt(self, 
                                base_topic: str,
                                fusion_level: int = 2,
                                use_identity: bool = True,
                                use_inequality: bool = True) -> str:
        """초고난도 문제 생성을 위한 프롬프트 생성"""
        
        prompt = f"""
🔥 초고난도 KSAT 수학 문제 생성 (최상위 1% 수준)

기본 주제: {base_topic}
융합 레벨: {fusion_level}단원 융합
난이도: 최상 (killer 문항)

핵심 요구사항:
1. 실제 수능 최고난도 문항(21, 29, 30번)보다 어려운 수준
2. 최소 {fusion_level}개 이상의 단원 개념 융합
3. 5단계 이상의 복잡한 사고과정 필요
4. 역사고력과 창의적 접근 필수
"""
        
        # 항등식 활용 지시
        if use_identity:
            identity_type = random.choice(list(self.identity_templates.keys()))
            identity_info = self.identity_templates[identity_type]
            pattern = random.choice(identity_info["patterns"])
            problem_type = random.choice(identity_info["problem_types"])
            
            prompt += f"""

📐 항등식 활용 지침:
- 핵심 항등식: {pattern}
- 문제 유형: {problem_type}
- 항등식을 직접적으로 제시하지 말고, 문제 해결 과정에서 발견하도록 유도
- 항등식의 변형이나 일반화를 요구하는 문제 출제
"""
        
        # 다단원 융합 지시
        fusion_keys = list(self.fusion_patterns.keys())
        selected_fusions = random.sample(fusion_keys, min(fusion_level, len(fusion_keys)))
        
        prompt += "\n🔗 다단원 융합 요소:"
        for fusion_key in selected_fusions:
            fusion_info = self.fusion_patterns[fusion_key]
            problem_type = random.choice(fusion_info["problem_types"])
            prompt += f"""
- {fusion_key}: {problem_type}
  관련 개념: {', '.join(fusion_info["concepts"])}"""
        
        # 부등식 조건 활용 지시
        if use_inequality:
            inequality_type = random.choice(list(self.inequality_patterns.keys()))
            inequality_info = self.inequality_patterns[inequality_type]
            constraint = random.choice(inequality_info["constraints"])
            technique = random.choice(inequality_info["techniques"])
            
            prompt += f"""

⚖️ 부등식 조건 활용:
- 제약 조건: {constraint}
- 활용 기법: {technique}
- 부등식을 통해 해의 존재성, 유일성, 범위를 결정하는 문제
- 등호 조건이 성립하는 경우를 찾는 것이 핵심이 되도록 설계
"""
        
        prompt += """

🎯 문제 설계 원칙:
1. **다층적 사고**: 표면적 접근으로는 해결 불가능, 깊은 통찰 필요
2. **함정 설치**: 일반적인 접근법이 막다른 길로 이어지도록
3. **우아한 해법**: 복잡해 보이지만 핵심 아이디어를 찾으면 간결하게 해결
4. **계산 복잡도**: 단순 계산이 아닌 개념적 이해와 논리적 추론 중심
5. **시간 압박**: 실전에서 15분 이상 소요될 정도의 난이도

예시 문제 구조:
- 도입부: 겉보기엔 단순한 설정
- 전개부: 여러 조건이 얽히며 복잡도 증가
- 핵심부: 숨겨진 패턴이나 항등식 발견 필요
- 해결부: 다단계 추론과 정교한 계산
- 검증부: 답의 타당성 확인 과정도 비자명

🚫 피해야 할 것:
- 단순 계산 위주 문제
- 공식 대입으로 해결되는 문제
- 한 가지 개념만 사용하는 문제
- 표준적인 풀이법이 바로 적용되는 문제
"""
        
        return prompt
    
    def generate_problem_examples(self) -> List[Dict]:
        """초고난도 문제 예시 생성"""
        
        examples = [
            {
                "type": "항등식+미적분",
                "problem": """
                함수 f(x)가 모든 실수 x에 대하여 다음 조건을 만족한다:
                
                (가) f(x + π) = -f(x)
                (나) ∫[0→π/2] f(x)sin(x)dx = 1
                (다) f'(x) + f(x) = e^x·cos(x)
                
                이때, f(0) + f(π/4) + f(π/2)의 값을 구하시오.
                """,
                "key_concepts": ["주기함수", "미분방정식", "삼각항등식", "적분"],
                "difficulty_score": 95
            },
            {
                "type": "부등식+수열+극한",
                "problem": """
                수열 {a_n}이 다음 조건을 만족한다:
                
                (가) a₁ = 1
                (나) a_{n+1} = a_n + 1/(n·a_n) (n ≥ 1)
                (다) 모든 n에 대해 √(2n) ≤ a_n ≤ √(2n+1)
                
                lim(n→∞) (a_n - √(2n))·√n 의 값을 구하시오.
                """,
                "key_concepts": ["점화식", "부등식", "극한", "근사"],
                "difficulty_score": 98
            },
            {
                "type": "삼각함수+미적분+기하",
                "problem": """
                평면 위의 점 P에서 출발한 곡선이 매개변수 방정식
                x(t) = ∫[0→t] cos(s²)ds, y(t) = ∫[0→t] sin(s²)ds로 주어진다.
                
                이 곡선 위의 점에서 곡률반지름이 √2일 때,
                그 점에서의 접선과 x축이 이루는 예각의 크기를 θ라 하자.
                
                sin(4θ)의 값을 구하시오.
                """,
                "key_concepts": ["매개변수 미분", "곡률", "삼각함수", "적분"],
                "difficulty_score": 97
            },
            {
                "type": "지수로그+적분+급수",
                "problem": """
                함수 f(x) = ln(1 + e^x) - x/2에 대하여,
                
                급수 Σ[n=1→∞] f(n)/n² 이 수렴할 때,
                
                lim[x→∞] [∫[0→x] f(t)dt / (x·ln x)]의 값을 구하시오.
                
                (단, e는 자연로그의 밑)
                """,
                "key_concepts": ["지수로그함수", "적분", "급수", "극한"],
                "difficulty_score": 96
            }
        ]
        
        return examples
    
    def analyze_ultra_difficulty(self, problem_data: Dict) -> Dict:
        """초고난도 문제 난이도 분석"""
        
        analysis = {
            "base_score": 80,  # 초고난도 기본 점수
            "factors": [],
            "fusion_count": 0,
            "identity_used": False,
            "inequality_used": False,
            "expected_time": 15,  # 예상 소요 시간(분)
        }
        
        question = problem_data.get("question", "")
        solution = problem_data.get("solution", "")
        
        # 융합 단원 수 계산
        fusion_keywords = {
            "미분": ["미분", "도함수", "f'", "d/dx"],
            "적분": ["적분", "∫", "넓이", "부피"],
            "지수로그": ["e^", "ln", "log", "지수", "로그"],
            "수열": ["수열", "a_n", "점화식", "급수", "수렴"],
            "극한": ["lim", "극한", "→∞", "수렴", "발산"],
            "삼각": ["sin", "cos", "tan", "삼각", "주기"],
        }
        
        detected_units = set()
        for unit, keywords in fusion_keywords.items():
            if any(kw in question + solution for kw in keywords):
                detected_units.add(unit)
        
        analysis["fusion_count"] = len(detected_units)
        analysis["base_score"] += len(detected_units) * 5
        analysis["factors"].append(f"융합 단원 수: {len(detected_units)}개 (+{len(detected_units)*5})")
        
        # 항등식 사용 여부
        identity_keywords = ["항등식", "모든 x", "임의의", "항상 성립"]
        if any(kw in question for kw in identity_keywords):
            analysis["identity_used"] = True
            analysis["base_score"] += 10
            analysis["factors"].append("항등식 활용 (+10)")
            analysis["expected_time"] += 3
        
        # 부등식 조건 사용 여부
        inequality_keywords = ["≤", "≥", "<", ">", "최대", "최소", "범위"]
        if any(kw in question for kw in inequality_keywords):
            analysis["inequality_used"] = True
            analysis["base_score"] += 8
            analysis["factors"].append("부등식 조건 (+8)")
            analysis["expected_time"] += 2
        
        # 고급 수학 개념
        advanced_concepts = {
            "테일러": 12,
            "라그랑주": 10,
            "코시": 10,
            "롤의 정리": 8,
            "중간값": 7,
            "곡률": 9,
            "발산": 8,
        }
        
        for concept, score in advanced_concepts.items():
            if concept in question + solution:
                analysis["base_score"] += score
                analysis["factors"].append(f"{concept} (+{score})")
                analysis["expected_time"] += 1
        
        # 최종 난이도 등급
        if analysis["base_score"] >= 100:
            analysis["grade"] = "울트라하드(Ultra Hard)"
        elif analysis["base_score"] >= 90:
            analysis["grade"] = "준-울트라하드(Semi-Ultra Hard)"
        else:
            analysis["grade"] = "최상"
        
        analysis["final_score"] = min(analysis["base_score"], 100)
        
        return analysis


# 기존 문제 생성기와 통합
def enhance_problem_generator_with_ultra_hard():
    """기존 문제 생성기에 초고난도 기능 추가"""
    
    ultra_generator = UltraHardProblemGenerator()
    
    # 초고난도 프롬프트 생성 함수
    def create_ultra_hard_prompt(topic, fusion_level=2):
        return ultra_generator.create_ultra_hard_prompt(
            topic, 
            fusion_level=fusion_level,
            use_identity=True,
            use_inequality=True
        )
    
    # 난이도 분석 함수 향상
    def analyze_ultra_difficulty(problem_data):
        return ultra_generator.analyze_ultra_difficulty(problem_data)
    
    return {
        "create_prompt": create_ultra_hard_prompt,
        "analyze": analyze_ultra_difficulty,
        "examples": ultra_generator.generate_problem_examples()
    }

# 초고난도 문제 카테고리 정의
ULTRA_HARD_CATEGORIES = {
    "항등식_마스터": {
        "description": "항등식을 핵심으로 하는 초고난도 문제",
        "min_score": 90,
        "topics": ["삼각항등식", "지수로그항등식", "대수항등식"],
        "required_skills": ["패턴인식", "일반화", "귀납법"]
    },
    "융합_마스터": {
        "description": "3개 이상 단원을 융합한 복합 문제",
        "min_score": 92,
        "topics": ["수학1+수학2", "수학2+미적분", "수학1+미적분"],
        "required_skills": ["다각도접근", "개념통합", "전환사고"]
    },
    "부등식_마스터": {
        "description": "부등식 조건과 최적화를 활용한 문제",
        "min_score": 88,
        "topics": ["최적화", "존재성", "범위제한"],
        "required_skills": ["경계분석", "극값판정", "조건해석"]
    },
    "극한_마스터": {
        "description": "극한과 수렴성을 다루는 최고난도 문제",
        "min_score": 95,
        "topics": ["수열극한", "함수극한", "적분수렴"],
        "required_skills": ["근사이론", "수렴판정", "오차분석"]
    }
}

if __name__ == "__main__":
    # 테스트
    generator = UltraHardProblemGenerator()
    prompt = generator.create_ultra_hard_prompt("미분과 적분", fusion_level=3)
    print("초고난도 문제 생성 프롬프트:")
    print("=" * 50)
    print(prompt)
    print("\n" + "=" * 50)
    print("예시 문제들:")
    for example in generator.generate_problem_examples()[:2]:
        print(f"\n[{example['type']}] 난이도: {example['difficulty_score']}/100")
        print(example['problem'])
        print(f"핵심 개념: {', '.join(example['key_concepts'])}")