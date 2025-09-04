import re
from typing import Union, List

class LaTeXRenderer:
    """LaTeX 수식을 Streamlit에서 렌더링 가능한 형식으로 변환"""
    
    def __init__(self):
        # 자주 사용되는 LaTeX 명령어 매핑
        self.latex_replacements = {
            r'\times': '×',
            r'\div': '÷',
            r'\pm': '±',
            r'\mp': '∓',
            r'\cdot': '·',
            r'\leq': '≤',
            r'\geq': '≥',
            r'\neq': '≠',
            r'\approx': '≈',
            r'\equiv': '≡',
            r'\infty': '∞',
            r'\alpha': 'α',
            r'\beta': 'β',
            r'\gamma': 'γ',
            r'\delta': 'δ',
            r'\theta': 'θ',
            r'\pi': 'π',
            r'\sigma': 'σ',
            r'\mu': 'μ',
            r'\lambda': 'λ',
            r'\omega': 'ω',
            r'\Delta': 'Δ',
            r'\Sigma': 'Σ',
            r'\Pi': 'Π',
            r'\Omega': 'Ω',
            r'\rightarrow': '→',
            r'\leftarrow': '←',
            r'\Rightarrow': '⇒',
            r'\Leftarrow': '⇐',
            r'\leftrightarrow': '↔',
            r'\Leftrightarrow': '⇔',
            r'\subset': '⊂',
            r'\supset': '⊃',
            r'\subseteq': '⊆',
            r'\supseteq': '⊇',
            r'\in': '∈',
            r'\notin': '∉',
            r'\cup': '∪',
            r'\cap': '∩',
            r'\emptyset': '∅',
            r'\forall': '∀',
            r'\exists': '∃',
            r'\partial': '∂',
            r'\nabla': '∇',
            r'\triangle': '△',
        }
    
    def render_for_streamlit(self, text: str) -> str:
        """
        LaTeX 수식이 포함된 텍스트를 Streamlit에서 렌더링 가능한 형식으로 변환
        
        Args:
            text: LaTeX 수식이 포함된 텍스트
            
        Returns:
            Streamlit에서 렌더링 가능한 텍스트
        """
        # 타입 체크 - 문자열이 아닌 경우 문자열로 변환
        if not isinstance(text, str):
            text = str(text) if text is not None else ''
        
        if not text:
            return text
        
        # Streamlit은 $$...$$ 형식의 display math와 $...$ 형식의 inline math를 지원
        # 그러나 backslash가 제대로 처리되지 않는 경우가 있으므로 보정
        
        # Display math 처리: \[...\] → $$...$$
        text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
        
        # Inline math 처리: \(...\) → $...$
        text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text)
        
        # 이미 $...$ 형식인 경우 유지
        # 단, Streamlit이 LaTeX를 제대로 렌더링하지 못하는 경우를 위한 폴백
        
        # 한국어 환경에서의 일반적인 수식 패턴 처리
        text = self._fix_korean_math_patterns(text)
        
        return text
    
    def _fix_korean_math_patterns(self, text: str) -> str:
        """한국어 환경에서 자주 사용되는 수학 패턴 수정"""
        
        # 이미 $ 기호로 감싸진 수식은 건너뛰기
        parts = text.split('$')
        for i in range(0, len(parts), 2):  # $ 밖의 텍스트만 처리
            part = parts[i]
            
            # 더 자연스러운 수식 패턴 처리
            
            # 함수 표현: f(x), g(x), h(t) 등을 LaTeX로 변환
            part = re.sub(r'\b([a-zA-Z])\(([a-zA-Z])\)', r'$\1(\2)$', part)
            
            # 제곱 표현: x², x³ 등을 그대로 유지하거나 LaTeX로 변환
            part = re.sub(r'([a-zA-Z])²', r'$\1^2$', part)
            part = re.sub(r'([a-zA-Z])³', r'$\1^3$', part)
            
            # 지수 표현: x^2, x^n → $x^2$, $x^n$
            part = re.sub(r'([a-zA-Z])\^([\d\+\-]+|[a-zA-Z]+|\{[^}]+\})', r'$\1^{\2}$', part)
            
            # 아래첨자: x_1, a_n → $x_1$, $a_n$
            part = re.sub(r'([a-zA-Z])_([\d\+\-]+|[a-zA-Z]+|\{[^}]+\})', r'$\1_{\2}$', part)
            
            # 분수 표현 개선: 숫자/숫자, 변수/변수, 복잡한 표현식
            # 단순 분수: 3/4, a/b
            part = re.sub(r'(?<![$/])(\d+|[a-zA-Z])\s*/\s*(\d+|[a-zA-Z])(?![$/])', r'$\\frac{\1}{\2}$', part)
            
            # 제곱근: √x, sqrt(x) → $\sqrt{x}$
            part = re.sub(r'√(\w+)', r'$\\sqrt{\1}$', part)
            part = re.sub(r'sqrt\((.*?)\)', r'$\\sqrt{\1}$', part)
            
            # 로그: log_a(x), log a(x) → $\log_a x$
            part = re.sub(r'log[_ ]?(\w+)\s*\((.*?)\)', r'$\\log_{\1} \2$', part)
            part = re.sub(r'log\s*\((.*?)\)', r'$\\log(\1)$', part)
            part = re.sub(r'\bln\s*\((.*?)\)', r'$\\ln(\1)$', part)
            
            # 삼각함수 개선
            trig_funcs = ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'arcsin', 'arccos', 'arctan']
            for func in trig_funcs:
                # sin x, sin(x), sin²x 등 다양한 형태 처리
                part = re.sub(f'\\b{func}\\s+([a-zA-Z0-9]+)', f'$\\\\{func} \\1$', part)
                part = re.sub(f'{func}\\((.*?)\\)', f'$\\\\{func}(\\1)$', part)
                part = re.sub(f'{func}²\\s*([a-zA-Z0-9]+)', f'$\\\\{func}^2 \\1$', part)
            
            # 벡터 표현: →a, vec{a} → $\vec{a}$
            part = re.sub(r'→([a-zA-Z])', r'$\\vec{\1}$', part)
            
            # 적분 기호 개선: ∫ → $\int$
            part = re.sub(r'∫', r'$\\int$', part)
            
            # 극한 표현 개선: lim_{x→a} → $\lim_{x \to a}$
            part = re.sub(r'lim_?\{?([^}→]+)→([^}]+)\}?', r'$\\lim_{\1 \\to \2}$', part)
            part = re.sub(r'\blim\b', r'$\\lim$', part)
            
            # 합/곱 기호: ∑, ∏ → $\sum$, $\prod$
            part = re.sub(r'∑', r'$\\sum$', part)
            part = re.sub(r'∏', r'$\\prod$', part)
            
            # 집합 기호
            part = re.sub(r'∈', r'$\\in$', part)
            part = re.sub(r'∉', r'$\\notin$', part)
            part = re.sub(r'⊂', r'$\\subset$', part)
            part = re.sub(r'⊃', r'$\\supset$', part)
            part = re.sub(r'∪', r'$\\cup$', part)
            part = re.sub(r'∩', r'$\\cap$', part)
            part = re.sub(r'∅', r'$\\emptyset$', part)
            
            # 부등호
            part = re.sub(r'≤', r'$\\leq$', part)
            part = re.sub(r'≥', r'$\\geq$', part)
            part = re.sub(r'≠', r'$\\neq$', part)
            part = re.sub(r'≈', r'$\\approx$', part)
            
            # 그리스 문자
            greek_letters = {
                'α': '\\alpha', 'β': '\\beta', 'γ': '\\gamma', 'δ': '\\delta',
                'θ': '\\theta', 'λ': '\\lambda', 'μ': '\\mu', 'π': '\\pi',
                'σ': '\\sigma', 'φ': '\\phi', 'ω': '\\omega',
                'Δ': '\\Delta', 'Σ': '\\Sigma', 'Π': '\\Pi', 'Ω': '\\Omega'
            }
            for symbol, latex in greek_letters.items():
                part = part.replace(symbol, f'${latex}$')
            
            # 무한대 기호
            part = re.sub(r'∞', r'$\\infty$', part)
            
            # 미분 표현: f'(x), f''(x)
            part = re.sub(r"([a-zA-Z])'''\s*\((.*?)\)", r"$\1'''(\2)$", part)
            part = re.sub(r"([a-zA-Z])''\s*\((.*?)\)", r"$\1''(\2)$", part)
            part = re.sub(r"([a-zA-Z])'\s*\((.*?)\)", r"$\1'(\2)$", part)
            
            # 편미분: ∂f/∂x
            part = re.sub(r'∂([a-zA-Z])/∂([a-zA-Z])', r'$\\frac{\\partial \1}{\\partial \2}$', part)
            
            parts[i] = part
        
        # 다시 합치기
        text = '$'.join(parts)
        
        # 연속된 $ 기호 정리
        text = re.sub(r'\$\s*\$', ' ', text)
        
        return text
    
    def process_problem_text(self, problem_data: dict) -> dict:
        """
        문제 데이터의 모든 텍스트 필드에서 LaTeX 수식 처리
        
        Args:
            problem_data: 문제 데이터 딕셔너리
            
        Returns:
            처리된 문제 데이터
        """
        # 처리할 필드들
        fields_to_process = ['question', 'solution', 'answer']
        
        for field in fields_to_process:
            if field in problem_data and problem_data[field] is not None:
                problem_data[field] = self.render_for_streamlit(str(problem_data[field]))
        
        # 선택지 처리
        if 'choices' in problem_data and problem_data['choices']:
            problem_data['choices'] = [
                self.render_for_streamlit(str(choice)) if choice is not None else choice
                for choice in problem_data['choices']
            ]
        
        # 핵심 개념 처리
        if 'key_concepts' in problem_data and problem_data['key_concepts']:
            problem_data['key_concepts'] = [
                self.render_for_streamlit(str(concept)) if concept is not None else concept
                for concept in problem_data['key_concepts']
            ]
        
        return problem_data
    
    def inject_mathjax(self) -> str:
        """
        MathJax를 로드하기 위한 HTML 코드 생성 (수능 스타일)
        Streamlit의 components.html()과 함께 사용
        """
        return """
        <style>
        /* 수능 스타일 수식 폰트 설정 */
        .MathJax {
            font-size: 1.1em !important;
        }
        
        .MathJax_Display {
            margin: 0.7em 0 !important;
        }
        
        mjx-container {
            font-family: 'STIX Two Math', 'Times New Roman', serif !important;
        }
        
        /* 인라인 수식 스타일 */
        mjx-container[jax="CHTML"][display="false"] {
            display: inline-block !important;
            margin: 0 0.15em !important;
        }
        
        /* 블록 수식 스타일 */
        mjx-container[jax="CHTML"][display="true"] {
            display: block !important;
            text-align: center !important;
            margin: 1em 0 !important;
        }
        </style>
        <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
                processEnvironments: true,
                // 수능 스타일 수식 설정
                macros: {
                    RR: "\\mathbb{R}",
                    NN: "\\mathbb{N}",
                    ZZ: "\\mathbb{Z}",
                    QQ: "\\mathbb{Q}",
                    CC: "\\mathbb{C}"
                }
            },
            chtml: {
                scale: 1.0,  // 수식 크기
                minScale: 0.5,
                matchFontHeight: true,
                mtextInheritFont: false,
                merrorInheritFont: false,
                mtextFont: '',
                merrorFont: 'serif',
                unknownFamily: 'serif',
                fontURL: 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/output/chtml/fonts/woff-v2'
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
            }
        };
        </script>
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        """