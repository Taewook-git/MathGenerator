"""
Gemma-3를 사용한 수학 문제 풀이 모듈
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Dict, Any, Optional, List
import re


class GemmaSolver:
    """Gemma-3 기반 수학 문제 풀이기"""
    
    def __init__(
        self,
        model_name: str = "google/gemma-3-4b-it",  # Gemma-3가 출시되면 변경
        device: Optional[str] = None,
        max_length: int = 2048,
        temperature: float = 0.3
    ):
        """
        Args:
            model_name: HuggingFace 모델 이름
            device: 연산 디바이스
            max_length: 최대 생성 길이
            temperature: 생성 온도 (낮을수록 일관성 있음)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.max_length = max_length
        self.temperature = temperature
        
        print(f"Loading {model_name} on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
            device_map="auto" if self.device == 'cuda' else None
        )
        
        if self.device == 'cpu':
            self.model = self.model.to(self.device)
            
        self.model.eval()
        
    def solve(
        self,
        problem: Dict[str, Any],
        show_steps: bool = True
    ) -> Dict[str, Any]:
        """
        문제 풀이 및 해설 생성
        
        Args:
            problem: 문제 딕셔너리
            show_steps: 단계별 풀이 표시 여부
            
        Returns:
            풀이 결과 딕셔너리
        """
        # 프롬프트 생성
        prompt = self._create_solving_prompt(problem, show_steps)
        
        # 토크나이징
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length
        ).to(self.device)
        
        # 생성
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=self.temperature,
                do_sample=True,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
        # 디코딩
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 응답에서 풀이 부분만 추출
        solution = self._extract_solution(response, prompt)
        
        # 결과 구성
        result = {
            "problem": problem,
            "solution": solution,
            "answer": self._extract_answer(solution),
            "confidence": self._calculate_confidence(solution, problem)
        }
        
        # 검증
        if problem.get("answer"):
            result["is_correct"] = self._verify_answer(
                result["answer"],
                problem["answer"]
            )
            
        return result
    
    def solve_batch(
        self,
        problems: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        여러 문제 일괄 풀이
        
        Args:
            problems: 문제 리스트
            show_progress: 진행 상황 표시
            
        Returns:
            풀이 결과 리스트
        """
        results = []
        
        for i, problem in enumerate(problems):
            if show_progress:
                print(f"Solving problem {i+1}/{len(problems)}...")
                
            try:
                result = self.solve(problem)
                results.append(result)
            except Exception as e:
                print(f"Failed to solve problem {i+1}: {e}")
                results.append({
                    "problem": problem,
                    "error": str(e)
                })
                
        return results
    
    def _create_solving_prompt(
        self,
        problem: Dict[str, Any],
        show_steps: bool
    ) -> str:
        """풀이 프롬프트 생성"""
        prompt_parts = [
            "당신은 한국 수능 수학 문제를 풀이하는 전문가입니다.",
            "다음 문제를 단계별로 자세히 풀어주세요.",
            "",
            f"[문제]",
            problem.get("question", problem.get("text", "")),
            ""
        ]
        
        # 선택형인 경우 보기 추가
        if problem.get("type") == "선택형" and problem.get("options"):
            prompt_parts.append("[보기]")
            for option in problem["options"]:
                prompt_parts.append(option)
            prompt_parts.append("")
            
        if show_steps:
            prompt_parts.extend([
                "[풀이 요구사항]",
                "1. 문제 분석",
                "2. 사용할 개념/공식",
                "3. 단계별 풀이 과정",
                "4. 최종 답",
                "5. 검산 (가능한 경우)",
                "",
                "[풀이]"
            ])
        else:
            prompt_parts.extend([
                "정답만 간단히 제시해주세요.",
                "",
                "[정답]"
            ])
            
        return "\n".join(prompt_parts)
    
    def _extract_solution(self, response: str, prompt: str) -> str:
        """응답에서 풀이 부분 추출"""
        # 프롬프트 이후 부분만 추출
        if prompt in response:
            solution = response[len(prompt):].strip()
        else:
            # [풀이] 태그 이후 부분 찾기
            if "[풀이]" in response:
                solution = response.split("[풀이]")[-1].strip()
            elif "[정답]" in response:
                solution = response.split("[정답]")[-1].strip()
            else:
                solution = response.strip()
                
        return solution
    
    def _extract_answer(self, solution: str) -> str:
        """풀이에서 최종 답 추출"""
        # 다양한 패턴으로 답 찾기
        patterns = [
            r"최종\s*답\s*[:：]\s*([^\n]+)",
            r"정답\s*[:：]\s*([^\n]+)",
            r"답\s*[:：]\s*([^\n]+)",
            r"따라서\s*답은\s*([^\n]+)",
            r"∴\s*([^\n]+)",
            r"Answer\s*[:：]\s*([^\n]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, solution, re.IGNORECASE)
            if match:
                answer = match.group(1).strip()
                # 선택지 번호 추출
                if "①" in answer:
                    return "①"
                elif "②" in answer:
                    return "②"
                elif "③" in answer:
                    return "③"
                elif "④" in answer:
                    return "④"
                elif "⑤" in answer:
                    return "⑤"
                # 숫자 추출
                else:
                    numbers = re.findall(r'\d+', answer)
                    if numbers:
                        return numbers[0]
                        
        # 마지막 줄에서 답 찾기
        lines = solution.strip().split('\n')
        if lines:
            last_line = lines[-1].strip()
            # 선택지 찾기
            for opt in ["①", "②", "③", "④", "⑤"]:
                if opt in last_line:
                    return opt
            # 숫자 찾기
            numbers = re.findall(r'\d+', last_line)
            if numbers:
                return numbers[-1]
                
        return "답을 찾을 수 없음"
    
    def _calculate_confidence(
        self,
        solution: str,
        problem: Dict[str, Any]
    ) -> float:
        """풀이 신뢰도 계산"""
        confidence = 0.5  # 기본값
        
        # 풀이 길이 체크
        if len(solution) > 100:
            confidence += 0.1
            
        # 수식 포함 여부
        if any(op in solution for op in ['+', '-', '*', '/', '=', '∫', '∑']):
            confidence += 0.1
            
        # 단계별 풀이 여부
        if any(keyword in solution for keyword in ['단계', '따라서', '그러므로']):
            confidence += 0.1
            
        # 검산 포함 여부
        if '검산' in solution or '확인' in solution:
            confidence += 0.2
            
        return min(confidence, 1.0)
    
    def _verify_answer(
        self,
        predicted_answer: str,
        correct_answer: str
    ) -> bool:
        """답 검증"""
        # 정규화
        pred = predicted_answer.strip().replace(" ", "")
        correct = str(correct_answer).strip().replace(" ", "")
        
        # 직접 비교
        if pred == correct:
            return True
            
        # 숫자만 추출해서 비교
        pred_nums = re.findall(r'\d+', pred)
        correct_nums = re.findall(r'\d+', correct)
        
        if pred_nums and correct_nums:
            return pred_nums[0] == correct_nums[0]
            
        return False