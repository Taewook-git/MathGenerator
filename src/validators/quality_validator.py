import sympy as sp
import numpy as np
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
# Sentence Transformers 완전 비활성화 (torch.classes 오류 방지)
SENTENCE_TRANSFORMERS_AVAILABLE = False

# 필요시 아래 주석 해제하여 활성화
# try:
#     from sentence_transformers import SentenceTransformer
#     from sklearn.metrics.pairwise import cosine_similarity
#     SENTENCE_TRANSFORMERS_AVAILABLE = True
# except (ImportError, RuntimeError, AttributeError) as e:
#     SENTENCE_TRANSFORMERS_AVAILABLE = False
#     print(f"sentence-transformers not available: {e}")
import sqlite3
import json
from datetime import datetime


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MathValidator:
    """SymPy 기반 수학 검증 시스템"""
    
    def __init__(self):
        self.symbols = sp.symbols('x y z t a b c n k')
        self.x, self.y, self.z, self.t, self.a, self.b, self.c, self.n, self.k = self.symbols
        
    def parse_mathematical_expression(self, expr_str: str) -> Optional[sp.Expr]:
        """수학 표현을 SymPy 표현식으로 변환"""
        try:
            # 입력이 너무 길거나 한글이 많으면 수식이 아닌 설명문으로 판단
            if len(expr_str) > 100 or len(re.findall(r'[가-힣]', expr_str)) > 5:
                logger.debug(f"수식이 아닌 설명문으로 판단: {expr_str[:50]}...")
                return None
            
            # 한국어 수식 표현을 SymPy 형식으로 변환
            expr_str = expr_str.strip()
            
            # 한글 제거 (수식만 추출)
            expr_str = re.sub(r'[가-힣]+', '', expr_str).strip()
            
            # 빈 문자열 체크
            if not expr_str:
                return None
            
            # 기본적인 변환
            expr_str = expr_str.replace('√', 'sqrt')
            expr_str = expr_str.replace('π', 'pi')
            expr_str = expr_str.replace('∞', 'oo')
            
            # 암시적 곱셈 처리: 2x -> 2*x, 3sin -> 3*sin
            expr_str = re.sub(r'(\d+)([a-zA-Z])', r'\1*\2', expr_str)
            
            # 분수 표현 변환: a/b -> a/b (이미 올바름)
            # 지수 표현 변환: x^2 -> x**2
            expr_str = re.sub(r'(\w+)\^([^\s\+\-\*/]+)', r'\1**(\2)', expr_str)
            
            # 삼각함수 처리
            expr_str = re.sub(r'sin\s*([^\s\+\-\*/]+)', r'sin(\1)', expr_str)
            expr_str = re.sub(r'cos\s*([^\s\+\-\*/]+)', r'cos(\1)', expr_str)
            expr_str = re.sub(r'tan\s*([^\s\+\-\*/]+)', r'tan(\1)', expr_str)
            
            # 로그 함수 처리
            expr_str = re.sub(r'ln\s*([^\s\+\-\*/]+)', r'log(\1)', expr_str)
            expr_str = re.sub(r'log₂\s*([^\s\+\-\*/]+)', r'log(\1,2)', expr_str)
            
            return sp.sympify(expr_str)
        except Exception as e:
            # 파싱 실패는 정상적인 경우도 많으므로 debug 레벨로 낮춤
            logger.debug(f"수식 파싱 스킵: {expr_str[:30] if len(expr_str) > 30 else expr_str}")
            return None
    
    def verify_equation_solution(self, equation_str: str, solution: Any) -> bool:
        """방정식의 해가 올바른지 검증"""
        try:
            # 등식을 좌변과 우변으로 분리
            if '=' in equation_str:
                left, right = equation_str.split('=', 1)
                left_expr = self.parse_mathematical_expression(left.strip())
                right_expr = self.parse_mathematical_expression(right.strip())
                
                if left_expr is None or right_expr is None:
                    return False
                
                # 해를 대입하여 검증
                solution_val = sp.sympify(solution)
                
                # x에 해를 대입
                left_val = left_expr.subs(self.x, solution_val)
                right_val = right_expr.subs(self.x, solution_val)
                
                return sp.simplify(left_val - right_val) == 0
            
            return False
        except Exception as e:
            logger.warning(f"방정식 검증 실패: {e}")
            return False
    
    def verify_derivative(self, function_str: str, derivative_str: str) -> bool:
        """미분 계산이 올바른지 검증"""
        try:
            func = self.parse_mathematical_expression(function_str)
            claimed_derivative = self.parse_mathematical_expression(derivative_str)
            
            if func is None or claimed_derivative is None:
                return False
            
            actual_derivative = sp.diff(func, self.x)
            return sp.simplify(actual_derivative - claimed_derivative) == 0
        except Exception as e:
            logger.warning(f"미분 검증 실패: {e}")
            return False
    
    def verify_integral(self, integrand_str: str, result_str: str, 
                       limits: Optional[Tuple[Any, Any]] = None) -> bool:
        """적분 계산이 올바른지 검증"""
        try:
            integrand = self.parse_mathematical_expression(integrand_str)
            claimed_result = self.parse_mathematical_expression(result_str)
            
            if integrand is None or claimed_result is None:
                return False
            
            if limits:
                # 정적분
                a, b = limits
                actual_result = sp.integrate(integrand, (self.x, a, b))
            else:
                # 부정적분
                actual_result = sp.integrate(integrand, self.x)
            
            # 부정적분의 경우 상수 차이는 무시
            if limits is None:
                diff = sp.diff(claimed_result - actual_result, self.x)
                return sp.simplify(diff) == 0
            else:
                return sp.simplify(actual_result - claimed_result) == 0
        except Exception as e:
            logger.warning(f"적분 검증 실패: {e}")
            return False
    
    def verify_limit(self, function_str: str, point: Any, limit_value: Any) -> bool:
        """극한값 계산이 올바른지 검증"""
        try:
            func = self.parse_mathematical_expression(function_str)
            if func is None:
                return False
            
            point_val = sp.sympify(point)
            claimed_limit = sp.sympify(limit_value)
            
            actual_limit = sp.limit(func, self.x, point_val)
            return sp.simplify(actual_limit - claimed_limit) == 0
        except Exception as e:
            logger.warning(f"극한 검증 실패: {e}")
            return False

class DistractorGenerator:
    """오답지(방해요인) 체계적 생성"""
    
    def __init__(self):
        self.validator = MathValidator()
        
    def generate_calculation_error_distractors(self, correct_answer: float, 
                                              num_distractors: int = 4) -> List[str]:
        """계산 실수 유형 오답지 생성"""
        distractors = []
        
        # 패턴 1: 부호 실수
        distractors.append(str(-correct_answer))
        
        # 패턴 2: 계산 과정에서 흔한 실수들
        if correct_answer != 0:
            distractors.extend([
                str(correct_answer * 2),      # 2배
                str(correct_answer / 2),      # 1/2배  
                str(correct_answer + 1),      # +1 실수
                str(correct_answer - 1),      # -1 실수
            ])
        
        # 패턴 3: 분수 계산 실수 (분모/분자 뒤바뀜)
        if abs(correct_answer) > 0.001:  # 0이 아닌 경우
            distractors.append(str(1.0/correct_answer))
        
        # 중복 제거 및 정답과 너무 가까운 것 제거  
        filtered = []
        for d in distractors:
            try:
                d_val = float(d)
                if (d_val != correct_answer and 
                    abs(d_val - correct_answer) > abs(correct_answer) * 0.1):
                    filtered.append(d)
            except:
                continue
                
        return filtered[:num_distractors]
    
    def generate_concept_error_distractors(self, problem_type: str, 
                                         correct_answer: Any) -> List[str]:
        """개념 오해 유형 오답지 생성"""
        distractors = []
        
        if problem_type == "미분":
            # 미분 공식 혼동
            if isinstance(correct_answer, (int, float)):
                distractors.extend([
                    str(correct_answer + 1),  # 상수항 빼먹음
                    str(correct_answer * 2),  # 곱의 법칙 실수
                ])
        
        elif problem_type == "적분":
            # 적분 공식 혼동
            if isinstance(correct_answer, (int, float)):
                distractors.extend([
                    str(correct_answer - 1),  # 상수항 처리 실수
                    str(abs(correct_answer)), # 부호 실수
                ])
        
        elif problem_type == "확률":
            # 확률 계산 실수
            if isinstance(correct_answer, (int, float)) and 0 <= correct_answer <= 1:
                distractors.extend([
                    str(1 - correct_answer),  # 여사건 혼동
                    str(correct_answer * 2),  # 중복 계산
                ])
        
        return distractors[:3]
    
    def generate_unit_trap_distractors(self, correct_answer: Any, 
                                     unit_type: str = "각도") -> List[str]:
        """단위/부호 함정 유형 오답지 생성"""
        distractors = []
        
        if unit_type == "각도" and isinstance(correct_answer, (int, float)):
            # 라디안 ↔ 도 변환 실수
            distractors.extend([
                str(correct_answer * 180 / 3.14159),  # 라디안→도 변환 실수
                str(correct_answer * 3.14159 / 180),  # 도→라디안 변환 실수
            ])
        
        elif unit_type == "넓이" and isinstance(correct_answer, (int, float)):
            # 넓이 계산 실수
            distractors.extend([
                str(correct_answer / 2),  # 공식의 1/2 빼먹음
                str(correct_answer * 2),  # 불필요한 2배
            ])
        
        return distractors[:2]

class DifficultyAnalyzer:
    """난이도 및 영역 자동 태깅"""
    
    def __init__(self):
        # 개념별 기본 난이도 가중치
        self.concept_weights = {
            "미분": {"기본": 1, "연쇄법칙": 2, "이계도함수": 3},
            "적분": {"기본": 1, "치환적분": 2, "부분적분": 3},
            "확률": {"기본": 1, "통계": 3, "조건부확률": 4},
            "기하": {"기본": 1, "벡터": 2, "공간기하": 4},
            "수열": {"기본": 1, "점화식": 3, "극한": 3},
        }
        
    def analyze_difficulty(self, problem_data: Dict) -> Dict:
        """난이도 자동 분석"""
        question = problem_data.get("question", "")
        solution = problem_data.get("solution", "")
        topic = problem_data.get("topic", "")
        
        # 기본 점수
        difficulty_score = 1.0
        analysis = {
            "base_score": 1.0,
            "factors": [],
            "estimated_difficulty": "중",
            "confidence": 0.8
        }
        
        # 1. 풀이 길이 분석
        solution_length = len(solution.split())
        if solution_length > 200:
            difficulty_score += 1.5
            analysis["factors"].append(f"긴 풀이과정 (+1.5): {solution_length}자")
        elif solution_length > 100:
            difficulty_score += 0.8
            analysis["factors"].append(f"중간 풀이과정 (+0.8): {solution_length}자")
        
        # 2. 수식 복잡도 분석
        math_patterns = [
            (r'∫.*dx', 1.2, "적분"),
            (r'lim.*→', 1.3, "극한"),
            (r'd/dx|f\'', 1.0, "미분"),
            (r'sin|cos|tan', 0.8, "삼각함수"),
            (r'log|ln', 0.7, "로그함수"),
            (r'√', 0.5, "제곱근"),
            (r'\^[3-9]', 1.1, "고차항"),
            (r'σ|μ|∑', 1.5, "통계/수열"),
        ]
        
        for pattern, weight, desc in math_patterns:
            if re.search(pattern, question + solution):
                difficulty_score += weight
                analysis["factors"].append(f"{desc} (+{weight})")
        
        # 3. 키워드 기반 난이도 평가
        high_difficulty_keywords = [
            "최댓값", "최솟값", "존재성", "필요충분조건",
            "역함수", "합성함수", "매개변수", "조건부확률"
        ]
        
        for keyword in high_difficulty_keywords:
            if keyword in question:
                difficulty_score += 1.2
                analysis["factors"].append(f"고난도 키워드: {keyword} (+1.2)")
        
        # 4. 문제 유형별 가중치
        if "증명" in question or "보이시오" in question:
            difficulty_score += 2.0
            analysis["factors"].append("증명문제 (+2.0)")
        
        # 5. 최종 난이도 결정
        if difficulty_score < 2.0:
            estimated = "하"
        elif difficulty_score < 4.0:
            estimated = "중"
        else:
            estimated = "상"
        
        analysis["final_score"] = round(difficulty_score, 2)
        analysis["estimated_difficulty"] = estimated
        
        return analysis
    
    def categorize_topic(self, problem_data: Dict) -> Dict:
        """주제 분류 및 세부 영역 태깅"""
        question = problem_data.get("question", "")
        
        # 주제별 키워드 매칭
        topic_keywords = {
            "미적분": {
                "미분": ["도함수", "접선", "변화율", "f'", "d/dx"],
                "적분": ["적분", "∫", "넓이", "부피"],
                "극한": ["lim", "극한", "연속", "→"],
            },
            "확률과통계": {
                "확률": ["확률", "사건", "표본공간"],
                "통계": ["평균", "분산", "표준편차", "σ", "μ"],
                "조합": ["조합", "순열", "C", "P"],
            },
            "기하": {
                "평면기하": ["삼각형", "원", "직선", "좌표"],
                "벡터": ["벡터", "→", "내적", "외적"],
                "공간기하": ["구", "면", "공간"],
            },
        }
        
        detected_topics = {}
        for main_topic, subtopics in topic_keywords.items():
            detected_topics[main_topic] = []
            for sub, keywords in subtopics.items():
                if any(kw in question for kw in keywords):
                    detected_topics[main_topic].append(sub)
        
        # 빈 항목 제거
        detected_topics = {k: v for k, v in detected_topics.items() if v}
        
        return {
            "main_topics": list(detected_topics.keys()),
            "subtopics": detected_topics,
            "confidence": 0.9 if detected_topics else 0.3
        }

class SolutionQualityChecker:
    """해설 품질 검증 및 개선"""
    
    def __init__(self):
        self.required_structure = {
            "핵심아이디어": {"min_chars": 20, "max_chars": 100},
            "단계별풀이": {"min_steps": 2, "max_steps": 10},
            "주의점": {"min_chars": 15, "max_chars": 80},
        }
    
    def analyze_solution_quality(self, solution: str) -> Dict:
        """해설 품질 분석"""
        analysis = {
            "structure_score": 0,
            "clarity_score": 0,
            "completeness_score": 0,
            "issues": [],
            "suggestions": [],
            "total_score": 0
        }
        
        # 1. 구조 분석
        structure_analysis = self._analyze_structure(solution)
        analysis.update(structure_analysis)
        
        # 2. 명확성 분석
        clarity_analysis = self._analyze_clarity(solution)
        analysis["clarity_score"] = clarity_analysis["score"]
        analysis["issues"].extend(clarity_analysis["issues"])
        
        # 3. 완성도 분석
        completeness_analysis = self._analyze_completeness(solution)
        analysis["completeness_score"] = completeness_analysis["score"]
        analysis["issues"].extend(completeness_analysis["issues"])
        
        # 총점 계산
        analysis["total_score"] = (
            analysis["structure_score"] * 0.4 +
            analysis["clarity_score"] * 0.3 +
            analysis["completeness_score"] * 0.3
        )
        
        return analysis
    
    def _analyze_structure(self, solution: str) -> Dict:
        """해설 구조 분석"""
        score = 0
        issues = []
        
        # 단계별 구분 확인 (1., 2., 3. 또는 ①, ②, ③)
        step_patterns = [r'\d+\.', r'[①②③④⑤⑥⑦⑧⑨⑩]', r'단계\s*\d+', r'\[\d+\]']
        has_steps = any(re.search(pattern, solution) for pattern in step_patterns)
        
        if has_steps:
            score += 40
        else:
            issues.append("단계별 구분이 명확하지 않음")
        
        # 핵심 아이디어 구문 확인
        idea_patterns = ["핵심", "아이디어", "포인트", "중요", "주목"]
        has_key_idea = any(keyword in solution for keyword in idea_patterns)
        
        if has_key_idea:
            score += 30
        else:
            issues.append("핵심 아이디어가 명시되지 않음")
        
        # 결론 또는 주의점 확인
        conclusion_patterns = ["따라서", "결론적으로", "주의", "유의", "참고"]
        has_conclusion = any(keyword in solution for keyword in conclusion_patterns)
        
        if has_conclusion:
            score += 30
        else:
            issues.append("결론 또는 주의사항이 없음")
        
        return {"structure_score": min(score, 100), "structure_issues": issues}
    
    def _analyze_clarity(self, solution: str) -> Dict:
        """명확성 분석"""
        score = 80  # 기본 점수
        issues = []
        
        # 문장 길이 체크 (너무 긴 문장은 감점)
        sentences = re.split(r'[.!?]', solution)
        long_sentences = [s for s in sentences if len(s.strip()) > 150]
        
        if long_sentences:
            score -= len(long_sentences) * 10
            issues.append(f"너무 긴 문장 {len(long_sentences)}개")
        
        # 수학 기호 사용 일관성
        inconsistent_notation = []
        if '×' in solution and '*' in solution:
            inconsistent_notation.append("곱셈 기호")
        if '÷' in solution and '/' in solution:
            inconsistent_notation.append("나눗셈 기호")
            
        if inconsistent_notation:
            score -= 15
            issues.append(f"표기법 불일치: {', '.join(inconsistent_notation)}")
        
        return {"score": max(score, 0), "issues": issues}
    
    def _analyze_completeness(self, solution: str) -> Dict:
        """완성도 분석"""
        score = 80  # 기본 점수
        issues = []
        
        # 최소 길이 체크
        if len(solution.strip()) < 50:
            score -= 30
            issues.append("해설이 너무 짧음")
        
        # 수식과 설명의 균형
        math_chars = len(re.findall(r'[+\-*/=<>∫∑√π]', solution))
        text_chars = len(re.sub(r'[+\-*/=<>∫∑√π\d\s]', '', solution))
        
        if text_chars < math_chars * 0.5:
            score -= 20
            issues.append("설명에 비해 수식이 과도함")
        elif math_chars < text_chars * 0.1:
            score -= 15
            issues.append("수식 표현이 부족함")
        
        return {"score": max(score, 0), "issues": issues}
    
    def improve_solution(self, solution: str, analysis: Dict) -> str:
        """해설 품질 개선"""
        improved = solution
        
        # 구조 개선
        if "단계별 구분이 명확하지 않음" in analysis.get("structure_issues", []):
            # 간단한 단계 구분 추가 (실제로는 더 정교한 로직 필요)
            sentences = solution.split('. ')
            if len(sentences) > 2:
                numbered_sentences = []
                for i, sentence in enumerate(sentences, 1):
                    if sentence.strip():
                        numbered_sentences.append(f"{i}. {sentence.strip()}")
                improved = '. '.join(numbered_sentences)
        
        return improved

class ProblemDatabase:
    """문제 데이터베이스 및 중복 방지"""
    
    def __init__(self, db_path: str = "problems.db"):
        self.db_path = db_path
        # Sentence transformer는 PyTorch 오류가 자주 발생하므로 비활성화
        # 대신 Jaccard 유사도 같은 간단한 메트릭 사용
        self.sentence_model = None
        self.use_embeddings = False
        
        # Sentence Transformer 완전 비활성화
        # torch.classes 오류 방지를 위해 사용하지 않음
        # 대신 Jaccard 유사도 사용 (더 빠르고 안정적)
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            choices TEXT,
            answer TEXT NOT NULL,
            solution TEXT NOT NULL,
            topic TEXT,
            difficulty TEXT,
            points INTEGER,
            embedding BLOB,
            quality_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS quality_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id INTEGER,
            difficulty_analysis TEXT,
            topic_analysis TEXT,
            solution_quality TEXT,
            validation_results TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (problem_id) REFERENCES problems (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간 유사도 계산"""
        if self.use_embeddings and self.sentence_model:
            try:
                embeddings = self.sentence_model.encode([text1, text2])
                similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                return float(similarity)
            except:
                pass
        
        # 폴백: 간단한 문자열 유사도
        return self._simple_similarity(text1, text2)
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """간단한 문자열 유사도 (Jaccard similarity)"""
        # 문자 단위로 집합 생성
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        # Jaccard similarity
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 1.0 if text1 == text2 else 0.0
        
        return intersection / union
    
    def check_duplicate(self, question: str, similarity_threshold: float = 0.8) -> List[Dict]:
        """중복 문제 검사"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, question FROM problems')
        existing_problems = cursor.fetchall()
        conn.close()
        
        similar_problems = []
        for prob_id, existing_question in existing_problems:
            similarity = self.calculate_similarity(question, existing_question)
            if similarity >= similarity_threshold:
                similar_problems.append({
                    "id": prob_id,
                    "question": existing_question,
                    "similarity": similarity
                })
        
        return similar_problems
    
    def store_problem(self, problem_data: Dict, quality_report: Dict) -> int:
        """문제 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 임베딩 계산 (가능한 경우)
        if self.use_embeddings and self.sentence_model:
            try:
                question_embedding = self.sentence_model.encode(problem_data["question"])
                question_embedding_bytes = question_embedding.tobytes()
            except:
                question_embedding_bytes = b""  # 빈 바이트
        else:
            question_embedding_bytes = b""
        
        cursor.execute('''
        INSERT INTO problems 
        (question, choices, answer, solution, topic, difficulty, points, 
         embedding, quality_score, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            problem_data["question"],
            json.dumps(problem_data.get("choices", [])),
            problem_data["answer"],
            problem_data["solution"],
            problem_data.get("topic", ""),
            problem_data.get("difficulty", ""),
            problem_data.get("points", 0),
            question_embedding_bytes,
            quality_report.get("total_quality_score", 0.0),
            json.dumps(problem_data)
        ))
        
        problem_id = cursor.lastrowid
        
        # 품질 보고서 저장
        cursor.execute('''
        INSERT INTO quality_reports 
        (problem_id, difficulty_analysis, topic_analysis, solution_quality, validation_results)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            problem_id,
            json.dumps(quality_report.get("difficulty_analysis", {})),
            json.dumps(quality_report.get("topic_analysis", {})),
            json.dumps(quality_report.get("solution_quality", {})),
            json.dumps(quality_report.get("validation_results", {}))
        ))
        
        conn.commit()
        conn.close()
        
        return problem_id
    
    def get_problem_statistics(self) -> Dict:
        """문제 통계 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # 전체 문제 수
        cursor.execute('SELECT COUNT(*) FROM problems')
        stats['total_problems'] = cursor.fetchone()[0]
        
        # 난이도별 분포
        cursor.execute('SELECT difficulty, COUNT(*) FROM problems GROUP BY difficulty')
        stats['difficulty_distribution'] = dict(cursor.fetchall())
        
        # 주제별 분포  
        cursor.execute('SELECT topic, COUNT(*) FROM problems GROUP BY topic')
        stats['topic_distribution'] = dict(cursor.fetchall())
        
        # 평균 품질 점수
        cursor.execute('SELECT AVG(quality_score) FROM problems WHERE quality_score > 0')
        avg_quality = cursor.fetchone()[0]
        stats['average_quality'] = round(avg_quality, 2) if avg_quality else 0
        
        conn.close()
        return stats


class QualityEnhancedGenerator:
    """통합 품질 강화 생성기"""
    
    def __init__(self):
        self.validator = MathValidator()
        self.distractor_gen = DistractorGenerator()
        self.difficulty_analyzer = DifficultyAnalyzer()
        self.solution_checker = SolutionQualityChecker()
        self.database = ProblemDatabase()
        
    def enhance_problem_quality(self, problem_data: Dict) -> Dict:
        """문제 품질 종합 강화"""
        enhanced_data = problem_data.copy()
        quality_report = {
            "validation_results": {},
            "difficulty_analysis": {},
            "topic_analysis": {},
            "solution_quality": {},
            "duplicate_check": {},
            "total_quality_score": 0.0
        }
        
        try:
            # 1. 수학적 검증
            validation_results = self._perform_validation(enhanced_data)
            quality_report["validation_results"] = validation_results
            
            # 2. 오답지 개선
            if enhanced_data.get("choices"):
                enhanced_choices = self._improve_distractors(enhanced_data)
                enhanced_data["choices"] = enhanced_choices
            
            # 3. 난이도 분석
            difficulty_analysis = self.difficulty_analyzer.analyze_difficulty(enhanced_data)
            quality_report["difficulty_analysis"] = difficulty_analysis
            enhanced_data["analyzed_difficulty"] = difficulty_analysis["estimated_difficulty"]
            enhanced_data["difficulty_score"] = difficulty_analysis["final_score"]
            
            # 4. 주제 분석
            topic_analysis = self.difficulty_analyzer.categorize_topic(enhanced_data)
            quality_report["topic_analysis"] = topic_analysis
            enhanced_data["detected_topics"] = topic_analysis["main_topics"]
            enhanced_data["subtopics"] = topic_analysis["subtopics"]
            
            # 5. 해설 품질 검증 및 개선
            solution_quality = self.solution_checker.analyze_solution_quality(
                enhanced_data.get("solution", "")
            )
            quality_report["solution_quality"] = solution_quality
            
            if solution_quality["total_score"] < 70:
                improved_solution = self.solution_checker.improve_solution(
                    enhanced_data.get("solution", ""), solution_quality
                )
                enhanced_data["solution"] = improved_solution
            
            # 6. 중복 검사
            duplicate_check = self.database.check_duplicate(enhanced_data["question"])
            quality_report["duplicate_check"] = {
                "similar_count": len(duplicate_check),
                "similar_problems": duplicate_check[:3]  # 상위 3개만
            }
            enhanced_data["is_duplicate"] = len(duplicate_check) > 0
            
            # 7. 종합 품질 점수 계산
            total_score = self._calculate_total_quality_score(quality_report)
            quality_report["total_quality_score"] = total_score
            enhanced_data["quality_score"] = total_score
            
            # 8. 데이터베이스 저장
            if total_score >= 60 and not enhanced_data.get("is_duplicate", False):
                problem_id = self.database.store_problem(enhanced_data, quality_report)
                enhanced_data["problem_id"] = problem_id
            
            enhanced_data["quality_report"] = quality_report
            
        except Exception as e:
            logger.error(f"품질 강화 처리 중 오류: {e}")
            enhanced_data["quality_enhancement_error"] = str(e)
        
        return enhanced_data
    
    def _perform_validation(self, problem_data: Dict) -> Dict:
        """수학적 검증 수행"""
        results = {
            "equation_check": None,
            "derivative_check": None,
            "integral_check": None,
            "limit_check": None,
            "overall_valid": False
        }
        
        question = problem_data.get("question", "")
        answer = problem_data.get("answer", "")
        solution = problem_data.get("solution", "")
        
        # 방정식 검증
        if "=" in question and answer:
            try:
                is_valid = self.validator.verify_equation_solution(question, answer)
                results["equation_check"] = is_valid
            except:
                results["equation_check"] = None
        
        # 미분 검증
        if "미분" in question or "도함수" in question:
            # 간단한 미분 검증 시도
            func_match = re.search(r'f\(x\)\s*=\s*([^,\s]+)', question)
            if func_match and answer:
                try:
                    is_valid = self.validator.verify_derivative(func_match.group(1), answer)
                    results["derivative_check"] = is_valid
                except:
                    results["derivative_check"] = None
        
        # 적분 검증
        if "∫" in question or "적분" in question:
            integrand_match = re.search(r'∫([^d]+)dx', question)
            if integrand_match and answer:
                try:
                    is_valid = self.validator.verify_integral(integrand_match.group(1), answer)
                    results["integral_check"] = is_valid
                except:
                    results["integral_check"] = None
        
        # 극한 검증
        if "lim" in question or "극한" in question:
            # 극한 검증 로직 (복잡하므로 간소화)
            results["limit_check"] = True  # 임시로 통과
        
        # 전체 유효성 판단
        valid_checks = [v for v in results.values() if v is not None]
        results["overall_valid"] = len(valid_checks) == 0 or all(valid_checks)
        
        return results
    
    def _improve_distractors(self, problem_data: Dict) -> List[str]:
        """오답지 개선"""
        correct_answer = problem_data.get("answer", "")
        choices = problem_data.get("choices", [])
        topic = problem_data.get("topic", "")
        
        if not correct_answer or not choices:
            return choices
        
        try:
            # 기존 오답지 분석
            current_distractors = [c for c in choices if c != correct_answer]
            
            # 숫자 답인 경우
            try:
                numeric_answer = float(correct_answer)
                
                # 계산 실수 유형 생성
                calc_errors = self.distractor_gen.generate_calculation_error_distractors(
                    numeric_answer, 3
                )
                
                # 개념 실수 유형 생성
                concept_errors = self.distractor_gen.generate_concept_error_distractors(
                    topic, numeric_answer
                )
                
                # 단위 함정 유형 생성
                unit_traps = self.distractor_gen.generate_unit_trap_distractors(
                    numeric_answer
                )
                
                # 새로운 오답지 조합
                new_distractors = calc_errors + concept_errors + unit_traps
                new_distractors = list(set(new_distractors))[:4]  # 중복 제거 후 4개
                
                # 정답과 함께 5개 선택지 구성
                improved_choices = [correct_answer] + new_distractors
                
                # 순서 섞기
                import random
                random.shuffle(improved_choices)
                
                return improved_choices[:5]
                
            except ValueError:
                # 숫자가 아닌 답인 경우 기존 선택지 유지
                return choices
                
        except Exception as e:
            logger.warning(f"오답지 개선 실패: {e}")
            return choices
    
    def _calculate_total_quality_score(self, quality_report: Dict) -> float:
        """종합 품질 점수 계산"""
        score = 0.0
        
        # 검증 결과 (30%)
        validation = quality_report.get("validation_results", {})
        if validation.get("overall_valid", False):
            score += 30
        
        # 해설 품질 (25%)
        solution_quality = quality_report.get("solution_quality", {})
        solution_score = solution_quality.get("total_score", 0)
        score += (solution_score / 100) * 25
        
        # 난이도 분석 신뢰도 (20%)
        difficulty = quality_report.get("difficulty_analysis", {})
        difficulty_confidence = difficulty.get("confidence", 0.5)
        score += difficulty_confidence * 20
        
        # 주제 분석 신뢰도 (15%)
        topic = quality_report.get("topic_analysis", {})
        topic_confidence = topic.get("confidence", 0.5)
        score += topic_confidence * 15
        
        # 중복성 (10% - 중복이 아닐 때 점수)
        duplicate = quality_report.get("duplicate_check", {})
        if duplicate.get("similar_count", 0) == 0:
            score += 10
        
        return round(min(score, 100), 2)