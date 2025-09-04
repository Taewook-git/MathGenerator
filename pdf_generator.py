from typing import List, Dict
import os
import subprocess
import tempfile
import re
from datetime import datetime
from pylatex import Document, Package, Command, NewPage, Section, Subsection
from pylatex.utils import NoEscape, bold
from pylatex.base_classes import Environment
from pylatex.package import Package as PyLatexPackage

class KSATPDFGenerator:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def create_exam_pdf(self, problems: List[Dict], exam_info: Dict = None) -> bytes:
        """
        문제 리스트를 받아 수능 형식의 PDF를 생성합니다.
        """
        if exam_info is None:
            exam_info = {
                "title": "대학수학능력시험 모의고사",
                "subject": "수학 영역",
                "exam_type": "가형",
                "date": datetime.now().strftime("%Y년 %m월 %d일"),
                "time": "100분",
                "total_questions": len(problems)
            }
        
        tex_content = self._generate_latex(problems, exam_info)
        pdf_bytes = self._compile_latex(tex_content)
        
        return pdf_bytes
    
    def _generate_latex(self, problems: List[Dict], exam_info: Dict) -> str:
        """
        LaTeX 소스 코드를 생성합니다.
        """
        latex_template = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{kotex}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsthm}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage{tikz}
\usepackage{pgfplots}
\usepackage{multicol}
\usepackage{setspace}
\usepackage{newtxtext,newtxmath}  % 수능 스타일 폰트

% 한글 폰트 설정 (나눔명조)
\setmainfont{NanumMyeongjo}
\setsansfont{NanumGothic}
\setmonofont{NanumGothicCoding}

\geometry{
    a4paper,
    left=20mm,
    right=20mm,
    top=25mm,
    bottom=25mm
}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{""" + exam_info['date'] + r"""}
\fancyhead[C]{\textbf{""" + exam_info['title'] + r"""}}
\fancyhead[R]{""" + exam_info['exam_type'] + r"""}
\fancyfoot[C]{\thepage}

\setlength{\parindent}{0pt}
\setstretch{1.2}  % 수능 스타일 줄 간격

% 수능 스타일 수식 설정
\everymath{\displaystyle}

\newcounter{problemnum}
\setcounter{problemnum}{0}

\newcommand{\problem}[1]{%
    \stepcounter{problemnum}%
    \vspace{10pt}%
    \noindent\textbf{\theproblemnum.} #1%
}

\newcommand{\choices}[5]{%
    \begin{enumerate}[label=\protect\circled{\arabic*}, itemsep=3pt]
        \item #1
        \item #2
        \item #3
        \item #4
        \item #5
    \end{enumerate}
}

\newcommand{\circled}[1]{\tikz[baseline=(char.base)]{
    \node[shape=circle,draw,inner sep=1pt] (char) {#1};}}

\begin{document}

\begin{center}
    \Large\textbf{""" + exam_info['title'] + r"""}\\
    \vspace{5mm}
    \large\textbf{""" + exam_info['subject'] + r""" (""" + exam_info['exam_type'] + r""")}\\
    \vspace{3mm}
    \normalsize 시험 시간: """ + exam_info['time'] + r"""
\end{center}

\vspace{10mm}

\begin{center}
    \fbox{
        \begin{minipage}{0.9\textwidth}
            \centering
            \textbf{수험생 유의사항}\\
            \vspace{3mm}
            \begin{itemize}[leftmargin=15pt]
                \item 문제지와 답안지의 해당란에 성명과 수험번호를 정확히 기입하시오.
                \item 답안지에는 반드시 흑색 펜을 사용하여 기입하시오.
                \item 문항에 따라 배점이 다르니, 각 물음의 끝에 표시된 배점을 참고하시오.
                \item 계산은 문제지의 여백을 활용하시오.
            \end{itemize}
        \end{minipage}
    }
\end{center}

\vspace{15mm}

"""
        
        # 선택형 문제 섹션
        selective_problems = [p for p in problems if p.get('problem_type') == '선택형']
        if selective_problems:
            latex_template += r"""\section*{\Large 선택형}
\vspace{5mm}

"""
            for problem in selective_problems:
                latex_template += self._format_problem(problem)
        
        # 단답형 문제 섹션
        short_answer_problems = [p for p in problems if p.get('problem_type') == '단답형']
        if short_answer_problems:
            latex_template += r"""
\newpage
\section*{\Large 단답형}
\vspace{5mm}

"""
            for problem in short_answer_problems:
                latex_template += self._format_problem(problem)
        
        # 정답 페이지
        latex_template += r"""
\newpage
\section*{\Large 정답 및 풀이}
\vspace{5mm}

"""
        for i, problem in enumerate(problems, 1):
            latex_template += self._format_answer(i, problem)
        
        latex_template += r"""
\end{document}"""
        
        return latex_template
    
    def _format_problem(self, problem: Dict) -> str:
        """
        개별 문제를 LaTeX 형식으로 변환합니다.
        """
        latex_str = ""
        
        # 문제 번호와 내용
        question = self._escape_latex(problem.get('question', ''))
        question = self._convert_math_expressions(question)
        
        latex_str += r"\problem{" + question + r" \textbf{[" + str(problem.get('points', 3)) + r"점]}}" + "\n\n"
        
        # 선택지 (선택형인 경우)
        if problem.get('problem_type') == '선택형' and problem.get('choices'):
            choices = problem.get('choices', [''] * 5)
            # 선택지도 수식 처리
            formatted_choices = []
            for choice in choices[:5]:  # 최대 5개
                escaped_choice = self._escape_latex(choice)
                formatted_choice = self._convert_math_expressions(escaped_choice)
                formatted_choices.append(formatted_choice)
            
            # 부족한 선택지는 빈 문자열로 채우기
            while len(formatted_choices) < 5:
                formatted_choices.append('')
            
            latex_str += r"\choices"
            for choice in formatted_choices:
                latex_str += "{" + choice + "}"
            latex_str += "\n\n"
        
        latex_str += r"\vspace{10pt}" + "\n\n"
        
        return latex_str
    
    def _format_answer(self, num: int, problem: Dict) -> str:
        """
        정답과 풀이를 LaTeX 형식으로 변환합니다.
        """
        latex_str = r"\subsection*{문제 " + str(num) + "}"
        latex_str += "\n\n"
        
        # 정답
        answer = self._escape_latex(str(problem.get('answer', '')))
        answer = self._convert_math_expressions(answer)
        latex_str += r"\textbf{정답: }" + answer + "\n\n"
        
        # 풀이
        solution = self._escape_latex(problem.get('solution', ''))
        solution = self._convert_math_expressions(solution)
        latex_str += r"\textbf{풀이:}\\[5pt]" + "\n"
        latex_str += solution + "\n\n"
        
        # 핵심 개념
        if problem.get('key_concepts'):
            latex_str += r"\textbf{핵심 개념:} "
            concepts = [self._escape_latex(c) for c in problem.get('key_concepts', [])]
            latex_str += ", ".join(concepts) + "\n\n"
        
        latex_str += r"\vspace{10pt}" + "\n\n"
        
        return latex_str
    
    def _escape_latex(self, text: str) -> str:
        """
        LaTeX 특수 문자를 이스케이프합니다.
        """
        if not text:
            return ""
        
        # LaTeX 특수 문자 이스케이프
        special_chars = {
            '&': r'\&',
            '%': r'\%',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}',
        }
        
        for char, replacement in special_chars.items():
            text = text.replace(char, replacement)
        
        return text
    
    def _convert_math_expressions(self, text: str) -> str:
        """
        텍스트 내의 수학 표현을 LaTeX 수식으로 변환합니다.
        """
        # 인라인 수식 처리 (예: $x^2 + y^2 = z^2$)
        text = re.sub(r'\$([^\$]+)\$', r'$\1$', text)
        
        # 블록 수식 처리 (예: $$\int_0^1 x^2 dx$$)
        text = re.sub(r'\$\$([^\$]+)\$\$', r'\\[\1\\]', text)
        
        # 일반적인 수학 표현 변환
        # 분수: a/b -> \frac{a}{b}
        text = re.sub(r'(\d+)/(\d+)', r'$\\frac{\1}{\2}$', text)
        
        # 제곱: x^2 -> x^{2}
        text = re.sub(r'(\w)\^(\d+)', r'$\1^{\2}$', text)
        
        # 루트: sqrt(x) -> \sqrt{x}
        text = re.sub(r'sqrt\(([^)]+)\)', r'$\\sqrt{\1}$', text)
        
        # 적분: int -> \int
        text = re.sub(r'\bint\b', r'$\\int$', text)
        
        # 시그마: sum -> \sum
        text = re.sub(r'\bsum\b', r'$\\sum$', text)
        
        # 파이: pi -> \pi
        text = re.sub(r'\bpi\b', r'$\\pi$', text)
        
        # 무한대: infinity -> \infty
        text = re.sub(r'\binfinity\b', r'$\\infty$', text)
        
        return text
    
    def _compile_latex(self, latex_content: str) -> bytes:
        """
        LaTeX 소스를 컴파일하여 PDF를 생성합니다.
        """
        # 임시 파일 생성
        tex_file = os.path.join(self.temp_dir, "exam.tex")
        pdf_file = os.path.join(self.temp_dir, "exam.pdf")
        
        # LaTeX 파일 작성
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        try:
            # xelatex 컴파일 시도 (한글 처리가 더 좋음)
            subprocess.run([
                'xelatex',
                '-interaction=nonstopmode',
                '-output-directory', self.temp_dir,
                tex_file
            ], capture_output=True, text=True, timeout=30)
            
        except (FileNotFoundError, subprocess.TimeoutExpired):
            try:
                # pdflatex 컴파일 시도
                subprocess.run([
                    'pdflatex',
                    '-interaction=nonstopmode',
                    '-output-directory', self.temp_dir,
                    tex_file
                ], capture_output=True, text=True, timeout=30)
                
            except:
                # LaTeX가 설치되지 않은 경우 대체 방법 사용
                return self._create_simple_pdf(latex_content)
        
        # PDF 파일 읽기
        if os.path.exists(pdf_file):
            with open(pdf_file, 'rb') as f:
                pdf_bytes = f.read()
            return pdf_bytes
        else:
            # PDF 생성 실패 시 대체 방법
            return self._create_simple_pdf(latex_content)
    
    def _create_simple_pdf(self, content: str) -> bytes:
        """
        LaTeX 컴파일이 불가능한 경우 간단한 PDF를 생성합니다.
        """
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        # PDF 파일 생성
        pdf_file = os.path.join(self.temp_dir, "exam_simple.pdf")
        doc = SimpleDocTemplate(pdf_file, pagesize=A4)
        
        # 스타일 설정
        styles = getSampleStyleSheet()
        
        # 제목 스타일
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor='black',
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        # 부제목 스타일  
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # 본문 스타일
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_LEFT,
            spaceAfter=12
        )
        
        # 문서 요소 생성
        story = []
        
        # 제목
        story.append(Paragraph("대학수학능력시험 모의고사", title_style))
        story.append(Paragraph("수학 영역", subtitle_style))
        story.append(Spacer(1, 20*mm))
        
        # LaTeX 내용을 간단한 텍스트로 변환
        lines = content.split('\n')
        for line in lines:
            if line.strip():
                # LaTeX 명령어 제거
                clean_line = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', line)
                clean_line = re.sub(r'\\[a-zA-Z]+', '', clean_line)
                clean_line = clean_line.replace('$', '').replace('{', '').replace('}', '')
                
                if clean_line.strip():
                    story.append(Paragraph(clean_line, body_style))
        
        # PDF 생성
        doc.build(story)
        
        # PDF 파일 읽기
        with open(pdf_file, 'rb') as f:
            pdf_bytes = f.read()
        
        return pdf_bytes