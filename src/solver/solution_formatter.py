"""
풀이 결과 포맷팅 모듈
"""
from typing import Dict, Any, List, Optional
import re


class SolutionFormatter:
    """풀이 결과를 다양한 형식으로 포맷팅"""
    
    @staticmethod
    def format_solution(
        solution_data: Dict[str, Any],
        format_type: str = "markdown"
    ) -> str:
        """
        풀이 결과 포맷팅
        
        Args:
            solution_data: 풀이 결과 데이터
            format_type: 출력 형식 (markdown, latex, html, plain)
            
        Returns:
            포맷된 문자열
        """
        if format_type == "markdown":
            return SolutionFormatter._format_markdown(solution_data)
        elif format_type == "latex":
            return SolutionFormatter._format_latex(solution_data)
        elif format_type == "html":
            return SolutionFormatter._format_html(solution_data)
        else:  # plain
            return SolutionFormatter._format_plain(solution_data)
            
    @staticmethod
    def _format_markdown(data: Dict[str, Any]) -> str:
        """Markdown 형식으로 포맷팅"""
        lines = []
        
        # 문제
        problem = data.get("problem", {})
        lines.append(f"## 문제 {problem.get('number', '')}")
        lines.append("")
        lines.append(problem.get("question", problem.get("text", "")))
        lines.append("")
        
        # 선택지
        if problem.get("options"):
            lines.append("**보기:**")
            for option in problem["options"]:
                lines.append(f"- {option}")
            lines.append("")
            
        # 문제 정보
        if problem.get("topic"):
            lines.append(f"- **주제:** {problem['topic']}")
        if problem.get("difficulty"):
            lines.append(f"- **난이도:** {problem['difficulty']}")
        if problem.get("points"):
            lines.append(f"- **배점:** {problem['points']}점")
        lines.append("")
        
        # 풀이
        lines.append("## 풀이")
        lines.append("")
        solution = data.get("solution", "")
        
        # 수식 처리 (LaTeX 스타일로 변환)
        solution = re.sub(r'(\d+)\^(\d+)', r'$\1^{\2}$', solution)
        solution = re.sub(r'sqrt\(([^)]+)\)', r'$\\sqrt{\1}$', solution)
        solution = re.sub(r'∫', r'$\\int$', solution)
        solution = re.sub(r'∑', r'$\\sum$', solution)
        
        lines.append(solution)
        lines.append("")
        
        # 답
        lines.append("## 정답")
        lines.append("")
        lines.append(f"**{data.get('answer', '답 없음')}**")
        
        # 검증 결과
        if "is_correct" in data:
            lines.append("")
            if data["is_correct"]:
                lines.append("✅ 정답입니다!")
            else:
                lines.append(f"❌ 오답입니다. (정답: {problem.get('answer', '?')})")
                
        # 신뢰도
        if "confidence" in data:
            lines.append("")
            confidence = data["confidence"]
            lines.append(f"신뢰도: {'⭐' * int(confidence * 5)}/5")
            
        return "\n".join(lines)
    
    @staticmethod
    def _format_latex(data: Dict[str, Any]) -> str:
        """LaTeX 형식으로 포맷팅"""
        lines = []
        
        problem = data.get("problem", {})
        
        # 문서 시작
        lines.append("\\begin{problem}")
        lines.append(f"\\item[{problem.get('number', '')}.]")
        
        # 문제 텍스트
        question = problem.get("question", "")
        question = SolutionFormatter._escape_latex(question)
        lines.append(question)
        
        # 선택지
        if problem.get("options"):
            lines.append("\\begin{enumerate}")
            for option in problem["options"]:
                option_text = SolutionFormatter._escape_latex(option)
                lines.append(f"\\item {option_text}")
            lines.append("\\end{enumerate}")
            
        lines.append("\\end{problem}")
        lines.append("")
        
        # 풀이
        lines.append("\\begin{solution}")
        solution = data.get("solution", "")
        solution = SolutionFormatter._escape_latex(solution)
        lines.append(solution)
        lines.append("\\end{solution}")
        lines.append("")
        
        # 답
        lines.append("\\begin{answer}")
        answer = SolutionFormatter._escape_latex(data.get("answer", ""))
        lines.append(f"\\boxed{{{answer}}}")
        lines.append("\\end{answer}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_html(data: Dict[str, Any]) -> str:
        """HTML 형식으로 포맷팅"""
        lines = []
        
        problem = data.get("problem", {})
        
        lines.append('<div class="problem-container">')
        
        # 문제
        lines.append(f'<h3>문제 {problem.get("number", "")}</h3>')
        lines.append(f'<div class="question">{problem.get("question", "")}</div>')
        
        # 선택지
        if problem.get("options"):
            lines.append('<div class="options">')
            lines.append('<ol>')
            for option in problem["options"]:
                lines.append(f'<li>{option}</li>')
            lines.append('</ol>')
            lines.append('</div>')
            
        # 메타데이터
        lines.append('<div class="metadata">')
        if problem.get("topic"):
            lines.append(f'<span class="topic">주제: {problem["topic"]}</span>')
        if problem.get("difficulty"):
            lines.append(f'<span class="difficulty">난이도: {problem["difficulty"]}</span>')
        if problem.get("points"):
            lines.append(f'<span class="points">배점: {problem["points"]}점</span>')
        lines.append('</div>')
        
        # 풀이
        lines.append('<div class="solution">')
        lines.append('<h4>풀이</h4>')
        solution = data.get("solution", "").replace('\n', '<br>')
        lines.append(f'<p>{solution}</p>')
        lines.append('</div>')
        
        # 답
        lines.append('<div class="answer">')
        lines.append('<h4>정답</h4>')
        lines.append(f'<strong>{data.get("answer", "")}</strong>')
        
        if "is_correct" in data:
            if data["is_correct"]:
                lines.append('<span class="correct">✓</span>')
            else:
                lines.append(f'<span class="incorrect">✗ (정답: {problem.get("answer", "")})</span>')
                
        lines.append('</div>')
        lines.append('</div>')
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_plain(data: Dict[str, Any]) -> str:
        """일반 텍스트 형식으로 포맷팅"""
        lines = []
        
        problem = data.get("problem", {})
        
        # 문제
        lines.append(f"문제 {problem.get('number', '')}")
        lines.append("-" * 50)
        lines.append(problem.get("question", ""))
        lines.append("")
        
        # 선택지
        if problem.get("options"):
            lines.append("보기:")
            for i, option in enumerate(problem["options"], 1):
                lines.append(f"  {option}")
            lines.append("")
            
        # 정보
        if problem.get("topic"):
            lines.append(f"주제: {problem['topic']}")
        if problem.get("difficulty"):
            lines.append(f"난이도: {problem['difficulty']}")
        if problem.get("points"):
            lines.append(f"배점: {problem['points']}점")
        lines.append("")
        
        # 풀이
        lines.append("풀이")
        lines.append("-" * 50)
        lines.append(data.get("solution", ""))
        lines.append("")
        
        # 답
        lines.append("정답")
        lines.append("-" * 50)
        lines.append(data.get("answer", ""))
        
        if "is_correct" in data:
            if data["is_correct"]:
                lines.append("(정답)")
            else:
                lines.append(f"(오답 - 정답: {problem.get('answer', '')})")
                
        return "\n".join(lines)
    
    @staticmethod
    def _escape_latex(text: str) -> str:
        """LaTeX 특수문자 이스케이프"""
        replacements = {
            '\\': '\\textbackslash{}',
            '{': '\\{',
            '}': '\\}',
            '$': '\\$',
            '&': '\\&',
            '#': '\\#',
            '%': '\\%',
            '_': '\\_',
            '^': '\\^{}',
            '~': '\\~{}',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        return text
    
    @staticmethod
    def format_batch_solutions(
        solutions: List[Dict[str, Any]],
        format_type: str = "markdown"
    ) -> str:
        """여러 풀이 결과를 하나로 포맷팅"""
        formatted_parts = []
        
        for i, solution in enumerate(solutions, 1):
            if format_type == "markdown":
                formatted_parts.append(f"---\n# 문항 {i}\n")
            elif format_type == "latex":
                formatted_parts.append(f"% 문항 {i}\n")
            elif format_type == "html":
                formatted_parts.append(f'<div class="problem-{i}">')
                
            formatted = SolutionFormatter.format_solution(solution, format_type)
            formatted_parts.append(formatted)
            
            if format_type == "html":
                formatted_parts.append('</div>')
                
        return "\n\n".join(formatted_parts)