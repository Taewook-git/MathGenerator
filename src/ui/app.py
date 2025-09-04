import streamlit as st
import streamlit.components.v1 as components
import sys
import os
# 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.problem_generator import KSATMathGenerator
from generators.pdf_generator import KSATPDFGenerator
from generators.latex_renderer import LaTeXRenderer
from core.config import MATH_TOPICS, PROBLEM_TYPES
import json
import pandas as pd
from datetime import datetime
import base64

st.set_page_config(
    page_title="수능 수학 문제 생성기",
    page_icon="📚",
    layout="wide"
)

@st.cache_resource
def init_generator():
    return KSATMathGenerator()

@st.cache_resource
def init_pdf_generator():
    return KSATPDFGenerator()

@st.cache_resource
def init_latex_renderer():
    return LaTeXRenderer()

def main():
    st.title("🎓 대학수학능력시험 수학 문제 생성기")
    st.markdown("Gemini AI를 활용한 수능 수학 문제 자동 생성 시스템")
    
    # MathJax 스크립트 삽입 (수능 스타일)
    components.html("""
    <style>
    /* 수능 스타일 수식 설정 */
    .MathJax {
        font-size: 1.05em !important;
    }
    
    mjx-container {
        font-family: 'STIX Two Math', 'Times New Roman', 'Batang', serif !important;
    }
    
    /* 인라인 수식 */
    mjx-container[jax="CHTML"][display="false"] {
        display: inline-block !important;
        margin: 0 0.15em !important;
    }
    
    /* 블록 수식 */
    mjx-container[jax="CHTML"][display="true"] {
        display: block !important;
        text-align: center !important;
        margin: 0.8em 0 !important;
    }
    
    /* 문제 텍스트 스타일 */
    .stMarkdown {
        font-family: 'Batang', 'NanumMyeongjo', serif;
        line-height: 1.6;
    }
    </style>
    <script>
    window.MathJax = {
        tex: {
            inlineMath: [['$', '$'], ['\\(', '\\)']],
            displayMath: [['$$', '$$'], ['\\[', '\\]']],
            processEscapes: true,
            processEnvironments: true,
            macros: {
                RR: "\\mathbb{R}",
                NN: "\\mathbb{N}",
                ZZ: "\\mathbb{Z}",
                QQ: "\\mathbb{Q}",
                CC: "\\mathbb{C}"
            }
        },
        chtml: {
            scale: 1.0,
            minScale: 0.5,
            matchFontHeight: true,
            mtextInheritFont: false,
            merrorInheritFont: false,
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
    """, height=0)
    
    generator = init_generator()
    pdf_generator = init_pdf_generator()
    latex_renderer = init_latex_renderer()
    
    with st.sidebar:
        st.header("⚙️ 문제 설정")
        
        mode = st.radio("모드 선택", ["단일 문제 생성", "모의고사 생성"])
        
        if mode == "단일 문제 생성":
            problem_type = st.selectbox("문제 유형", ["선택형", "단답형"])
            
            topic = st.selectbox("주제", ["자동 선택"] + MATH_TOPICS)
            if topic == "자동 선택":
                topic = None
            
            difficulty = st.selectbox(
                "난이도", 
                ["하", "중", "상", "킬러"],
                help="킬러: 초고난도 문항 (항등식, 다단원 융합, 부등식 활용)"
            )
            
            points = st.selectbox("배점", 
                                [2, 3, 4] if problem_type == "선택형" else [3, 4])
            
            if st.button("🚀 문제 생성", type="primary"):
                with st.spinner("문제를 생성하는 중..."):
                    problem = generator.generate_problem(
                        problem_type=problem_type,
                        topic=topic,
                        difficulty=difficulty,
                        points=points
                    )
                    # LaTeX 렌더링 적용
                    problem = latex_renderer.process_problem_text(problem)
                    st.session_state['current_problem'] = problem
        
        else:  
            num_problems = st.slider("문제 수", 10, 30, 20)
            
            include_killer = st.checkbox(
                "킬러 문제 포함", 
                value=False,
                help="초고난도 킬러 문항 1-2개를 포함합니다"
            )
            
            if st.button("📝 모의고사 생성", type="primary"):
                with st.spinner(f"{num_problems}개의 문제를 생성하는 중..."):
                    problems = generator.generate_exam_set(
                        num_problems=num_problems,
                        include_killer=include_killer
                    )
                    # 모든 문제에 LaTeX 렌더링 적용
                    problems = [latex_renderer.process_problem_text(p) for p in problems]
                    st.session_state['exam_problems'] = problems
    
    if mode == "단일 문제 생성" and 'current_problem' in st.session_state:
        problem = st.session_state['current_problem']
        
        if 'error' in problem:
            st.error(problem['error'])
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📋 문제")
                
                st.info(f"**주제:** {problem.get('topic', 'N/A')} | "
                       f"**난이도:** {problem.get('difficulty', 'N/A')} | "
                       f"**배점:** {problem.get('points', 'N/A')}점")
                
                # LaTeX 수식이 포함된 문제 표시
                question_text = problem.get('question', '문제를 불러올 수 없습니다.')
                st.markdown(question_text)
                
                # 그래프가 있는 경우 표시
                if problem.get('graph'):
                    st.markdown("**그래프:**")
                    img_html = f'<img src="data:image/png;base64,{problem["graph"]}" style="max-width:100%; height:auto;">'
                    st.markdown(img_html, unsafe_allow_html=True)
                
                if problem.get('choices'):
                    st.markdown("**선택지:**")
                    # 선택지를 2열로 표시하여 가독성 향상
                    col1_choices, col2_choices = st.columns(2)
                    choices = problem.get('choices', [])
                    
                    for i, choice in enumerate(choices, 1):
                        # 선택지 번호와 값을 명확히 표시
                        circle_nums = ["①", "②", "③", "④", "⑤"]
                        choice_text = f"**{circle_nums[i-1]}** {choice}"
                        if i <= 3:
                            col1_choices.markdown(choice_text)
                        else:
                            col2_choices.markdown(choice_text)
            
            with col2:
                st.subheader("💡 정답 및 풀이")
                
                with st.expander("정답 보기"):
                    answer_text = problem.get('answer', 'N/A')
                    # 선택형인 경우 선택지 번호도 함께 표시
                    if problem.get('choices') and answer_text in problem['choices']:
                        circle_nums = ["①", "②", "③", "④", "⑤"]
                        idx = problem['choices'].index(answer_text)
                        st.success(f"**정답:** {circle_nums[idx]} {answer_text}")
                    else:
                        st.success(f"**정답:** {answer_text}")
                
                with st.expander("풀이 보기"):
                    solution_text = problem.get('solution', '풀이를 불러올 수 없습니다.')
                    st.markdown(solution_text)
                
                if problem.get('key_concepts'):
                    with st.expander("핵심 개념"):
                        for concept in problem.get('key_concepts', []):
                            st.markdown(f"- {concept}")
                
                # 추가 품질 정보 표시
                if problem.get('difficulty_rationale'):
                    with st.expander("난이도 설정 근거"):
                        st.markdown(problem['difficulty_rationale'])
                
                if problem.get('common_mistakes'):
                    with st.expander("자주 하는 실수"):
                        for mistake in problem.get('common_mistakes', []):
                            st.markdown(f"⚠️ {mistake}")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 문제 저장 (JSON)"):
                    filename = generator.save_problems_to_file([problem], "single_problem.json")
                    st.success(f"문제가 {filename}에 저장되었습니다!")
            
            with col2:
                json_str = json.dumps(problem, ensure_ascii=False, indent=2)
                st.download_button(
                    label="💾 JSON 다운로드",
                    data=json_str,
                    file_name="ksat_math_problem.json",
                    mime="application/json"
                )
    
    elif mode == "모의고사 생성" and 'exam_problems' in st.session_state:
        problems = st.session_state['exam_problems']
        
        st.subheader(f"📝 생성된 모의고사 ({len(problems)}문제)")
        
        tab1, tab2, tab3 = st.tabs(["문제 목록", "상세 보기", "통계"])
        
        with tab1:
            for i, problem in enumerate(problems, 1):
                with st.expander(f"문제 {i} - {problem.get('topic', 'N/A')} ({problem.get('points', 0)}점)"):
                    question_text = problem.get('question', '문제를 불러올 수 없습니다.')
                    st.markdown(question_text)
                    
                    # 그래프가 있는 경우 표시
                    if problem.get('graph'):
                        st.markdown("**그래프:**")
                        img_html = f'<img src="data:image/png;base64,{problem["graph"]}" style="max-width:100%; height:auto;">'
                        st.markdown(img_html, unsafe_allow_html=True)
                    
                    if problem.get('choices'):
                        st.markdown("**선택지:**")
                        circle_nums = ["①", "②", "③", "④", "⑤"]
                        choices_text = " ".join([f"{circle_nums[j]} {choice}" for j, choice in enumerate(problem.get('choices', []))])
                        st.markdown(choices_text)
                    
                    answer_text = problem.get('answer', 'N/A')
                    st.info(f"정답: {answer_text}")
        
        with tab2:
            problem_num = st.selectbox("문제 선택", 
                                      [f"문제 {i+1}" for i in range(len(problems))])
            idx = int(problem_num.split()[1]) - 1
            selected = problems[idx]
            
            st.markdown(f"### {problem_num}")
            question_text = selected.get('question', '문제를 불러올 수 없습니다.')
            st.markdown(question_text)
            
            # 그래프가 있는 경우 표시
            if selected.get('graph'):
                st.markdown("**그래프:**")
                img_html = f'<img src="data:image/png;base64,{selected["graph"]}" style="max-width:100%; height:auto;">'
                st.markdown(img_html, unsafe_allow_html=True)
            
            if selected.get('choices'):
                st.markdown("**선택지:**")
                circle_nums = ["①", "②", "③", "④", "⑤"]
                for i, choice in enumerate(selected.get('choices', []), 1):
                    st.markdown(f"{circle_nums[i-1]} {choice}")
            
            with st.expander("정답 및 풀이"):
                answer_text = selected.get('answer', 'N/A')
                st.success(f"정답: {answer_text}")
                solution_text = selected.get('solution', '풀이를 불러올 수 없습니다.')
                st.markdown(solution_text)
        
        with tab3:
            df_data = []
            for p in problems:
                df_data.append({
                    "문제 번호": p.get('number', 0),
                    "유형": p.get('problem_type', 'N/A'),
                    "주제": p.get('topic', 'N/A'),
                    "난이도": p.get('difficulty', 'N/A'),
                    "배점": p.get('points', 0)
                })
            
            df = pd.DataFrame(df_data)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 주제별 분포")
                topic_counts = df['주제'].value_counts()
                st.bar_chart(topic_counts)
            
            with col2:
                st.markdown("#### 난이도별 분포")
                diff_counts = df['난이도'].value_counts()
                st.bar_chart(diff_counts)
            
            st.markdown("#### 문제 상세 정보")
            st.dataframe(df, use_container_width=True)
            
            total_points = df['배점'].sum()
            st.info(f"총점: {total_points}점")
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📥 모의고사 저장 (JSON)"):
                filename = generator.save_problems_to_file(problems, "exam_set.json")
                st.success(f"모의고사가 {filename}에 저장되었습니다!")
        
        with col2:
            json_str = json.dumps(problems, ensure_ascii=False, indent=2)
            st.download_button(
                label="💾 JSON 다운로드",
                data=json_str,
                file_name="ksat_math_exam.json",
                mime="application/json"
            )
        
        with col3:
            if st.button("📄 PDF 생성"):
                with st.spinner("PDF를 생성하는 중... (최대 1분 소요)"):
                    try:
                        exam_info = {
                            "title": "대학수학능력시험 모의고사",
                            "subject": "수학 영역",
                            "date": datetime.now().strftime("%Y년 %m월 %d일"),
                            "time": "100분",
                            "total_questions": len(problems)
                        }
                        pdf_bytes = pdf_generator.create_exam_pdf(problems, exam_info)
                        
                        st.download_button(
                            label="📑 PDF 다운로드",
                            data=pdf_bytes,
                            file_name=f"ksat_math_exam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                        st.success("PDF가 성공적으로 생성되었습니다!")
                    except Exception as e:
                        st.error(f"PDF 생성 중 오류 발생: {str(e)}")
                        st.info("LaTeX가 설치되지 않은 경우 간단한 형식의 PDF가 생성됩니다.")

if __name__ == "__main__":
    main()