import streamlit as st
import streamlit.components.v1 as components
import sys
import os
from pathlib import Path
import json
import pandas as pd
from datetime import datetime
import base64
from typing import Dict, Any, List, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.retriever import ProblemSearcher
from src.generator import ProblemGenerator
from src.solver import GemmaSolver, SolutionFormatter
from src.utils.pdf_generator import PDFGenerator
from src.utils.config import Config
from src.core.config import MATH_TOPICS, PROBLEM_TYPES
from src.core.curriculum_2015 import CURRICULUM_2015, get_curriculum_info, PROBLEM_GUIDELINES
from src.generator.problem_generator_2015 import ProblemGenerator2015
from src.generator.ultra_hard_generator import UltraHardGenerator
from src.generator.gemini_client_v2 import GeminiClientV2
from src.generators.latex_renderer import LaTeXRenderer

st.set_page_config(
    page_title="수능 수학 문제 생성기",
    page_icon="📚",
    layout="wide"
)

@st.cache_resource
def init_generator():
    """문제 생성기 초기화"""
    try:
        return ProblemGenerator()
    except Exception as e:
        st.error(f"Generator 초기화 실패: {e}")
        return None

@st.cache_resource
def init_2015_generator():
    """2015 개정 교육과정 문제 생성기 초기화"""
    try:
        client = GeminiClientV2(use_safety_filter=False)
        return ProblemGenerator2015(gemini_client=client)
    except Exception as e:
        st.error(f"2015 Generator 초기화 실패: {e}")
        return None

@st.cache_resource
def init_ultra_hard_generator():
    """울트라 하드 문항 생성기 초기화"""
    try:
        client = GeminiClientV2(use_safety_filter=False)
        # 연결 테스트
        success, msg = client.test_connection()
        if not success:
            st.warning(f"⚠️ API 연결 문제: {msg}")
        return UltraHardGenerator(gemini_client=client)
    except Exception as e:
        st.error(f"Ultra Hard Generator 초기화 실패: {e}")
        return None

@st.cache_resource
def init_pdf_generator():
    """PDF 생성기 초기화"""
    try:
        return PDFGenerator()
    except:
        from generators.pdf_generator import KSATPDFGenerator
        return KSATPDFGenerator()

@st.cache_resource
def init_searcher():
    """검색 모듈 초기화"""
    try:
        index_path = os.getenv("INDEX_PATH", "data/index")
        if Path(index_path).exists():
            return ProblemSearcher(index_path=index_path)
    except Exception as e:
        st.warning(f"검색 모듈 초기화 실패: {e}")
    return None

@st.cache_resource
def init_latex_renderer():
    """LaTeX 렌더러 초기화"""
    return LaTeXRenderer()

@st.cache_resource  
def init_solver():
    """풀이 모듈 초기화"""
    try:
        return GemmaSolver()
    except Exception as e:
        st.warning(f"Solver 초기화 실패: {e}")
    return None

def main():
    st.title("🎓 대학수학능력시험 수학 문제 생성기")
    st.markdown("2015 개정 교육과정 기반 AI 문제 생성 시스템")
    st.info("📌 **모든 문제는 2015 개정 교육과정 범위 내에서만 출제됩니다**")
    
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
    generator_2015 = init_2015_generator()
    ultra_hard_generator = init_ultra_hard_generator()
    pdf_generator = init_pdf_generator()
    latex_renderer = init_latex_renderer()
    
    with st.sidebar:
        st.header("⚙️ 문제 설정")
        
        mode = st.radio(
            "모드 선택", 
            ["단일 문제 생성", "울트라 하드 문항 생성", "모의고사 생성"],
            help="울트라 하드 문항: 2015 개정 교육과정 내 최고 난도 문제"
        )
        
        if mode == "울트라 하드 문항 생성":
            st.subheader("🔥 울트라 하드 문항 생성")
            st.warning("⚠️ 울트라 하드 문항도 2015 개정 교육과정을 철저히 준수합니다")
            
            # 울트라 하드 옵션
            col1, col2 = st.columns(2)
            
            with col1:
                fusion_type = st.selectbox(
                    "융합 유형",
                    ["수학1+수학2", "미적분"],
                    help="수학1+수학2: 두 과목 개념 융합\n미적분: 미적분 단독 최고난도"
                )
            
            with col2:
                pattern = st.selectbox(
                    "울트라 하드 패턴",
                    ["항등식", "명제", "경우의수", "최적화", 
                     "초월함수 미분가능성", "극한과 연속성", "합성함수 분석"],
                    help="문제의 핵심 난도 요소"
                )
            
            problem_type = st.radio(
                "문제 유형",
                ["선택형 (14번, 15번)", "단답형 (21번, 22번, 29번, 30번)"],
                horizontal=True
            )
            problem_type = problem_type.split()[0]  # "선택형" 또는 "단답형"만 추출
            
            # 울트라 하드 가이드라인
            with st.expander("🎯 울트라 하드 문항 특징"):
                st.info("""
                **필수 요소:**
                • 항등식의 복잡한 해석
                • 여러 단원의 개념 융합
                • 어려운 명제의 참/거짓 판별
                • 다단계 사고 과정 요구
                • 경우의 수 분할 또는 조건 분석
                
                **예상 소요 시간:** 10-15분
                **배점:** 4점 고정
                """)
            
            if st.button("🔥 울트라 하드 문항 생성", type="primary"):
                with st.spinner("최고 난도 문제를 생성하는 중... (약 10초 소요)"):
                    if ultra_hard_generator:
                        try:
                            problem = ultra_hard_generator.generate_ultra_hard_problem(
                                fusion_type=fusion_type,
                                pattern=pattern,
                                problem_type=problem_type
                            )
                        except Exception as e:
                            error_msg = str(e)
                            if "quota" in error_msg.lower() or "429" in error_msg:
                                st.error("""⚠️ **Gemini API 일일 할당량 초과**
                                
                                무료 티어의 하루 50개 요청 제한에 도달했습니다.
                                
                                **해결 방법:**
                                1. 내일 다시 시도 (할당량이 초기화됩니다)
                                2. [Google AI Studio](https://aistudio.google.com/)에서 유료 플랜으로 업그레이드
                                3. .env 파일에 OPENAI_API_KEY 추가하여 OpenAI 사용
                                """)
                            else:
                                st.error(f"문제 생성 실패: {error_msg}")
                            problem = None
                    else:
                        st.error("울트라 하드 문항 생성기를 사용할 수 없습니다")
                        problem = None
                    
                    if problem:
                        # LaTeX 렌더링 적용
                        problem = latex_renderer.process_problem_text(problem)
                        st.session_state['current_problem'] = problem
        
        elif mode == "단일 문제 생성":
            st.subheader("📚 2015 개정 교육과정 기준")
            
            # 과목 선택
            subject = st.selectbox(
                "과목 선택",
                ["수학1", "수학2", "미적분"],
                help="2015 개정 교육과정 수학 과목"
            )
            
            # 선택된 과목의 단원 표시
            chapters = list(CURRICULUM_2015[subject]["chapters"].keys())
            chapter = st.selectbox("단원 선택", chapters)
            
            # 소단원 선택 (선택사항)
            chapter_data = CURRICULUM_2015[subject]["chapters"][chapter]
            sections = chapter_data.get("sections", [])
            if sections:
                section = st.selectbox("세부 주제", ["전체"] + sections)
                if section == "전체":
                    section = None
            else:
                section = None
            
            problem_type = st.selectbox("문제 유형", ["선택형", "단답형"])
            
            difficulty = st.selectbox(
                "난이도", 
                ["하", "중", "상"],
                help="모든 난이도는 2015 개정 교육과정 범위 내에서 출제"
            )
            
            # 교육과정 제한사항 표시
            with st.expander("📌 교육과정 가이드라인"):
                limits = chapter_data.get("curriculum_limits", [])
                if limits:
                    st.warning("주의사항:")
                    for limit in limits:
                        st.write(f"- {limit}")
                        
                guidelines = PROBLEM_GUIDELINES.get(subject, {}).get(
                    chapter.replace(" ", "_"), {}
                ).get(difficulty, "")
                if guidelines:
                    st.info(f"{difficulty} 난이도 가이드: {guidelines}")
            
            points = st.selectbox("배점", 
                                [2, 3, 4] if problem_type == "선택형" else [3, 4])
            
            if st.button("🚀 문제 생성", type="primary"):
                with st.spinner("교육과정 준수 문제를 생성하는 중..."):
                    if generator_2015:
                        problem = generator_2015.generate_curriculum_problem(
                            subject=subject,
                            chapter=chapter,
                            section=section,
                            difficulty=difficulty,
                            problem_type=problem_type
                        )
                    else:
                        # 폴백: 기본 생성기 사용
                        problem = generator.generate_problem(
                            subject=subject,
                            topic=section or chapter,
                            difficulty=difficulty,
                            problem_type=problem_type,
                            points=points
                        )
                    # LaTeX 렌더링 적용
                    problem = latex_renderer.process_problem_text(problem)
                    st.session_state['current_problem'] = problem
        
        else:  # 모의고사 생성
            st.subheader("📝 모의고사 설정")
            
            exam_type = st.radio(
                "시험 유형",
                ["통합형", "단원별"],
                help="통합형: 모든 과목 포함, 단원별: 특정 과목/단원만"
            )
            
            if exam_type == "단원별":
                exam_subject = st.selectbox(
                    "과목 선택",
                    ["수학1", "수학2", "미적분"]
                )
                exam_chapters = list(CURRICULUM_2015[exam_subject]["chapters"].keys())
                exam_chapter = st.selectbox("단원 선택", exam_chapters)
            
            num_problems = st.slider("문제 수", 10, 30, 20)
            
            # 난이도 분포 설정
            st.write("난이도 분포")
            col1, col2, col3 = st.columns(3)
            with col1:
                easy_pct = st.slider("하 (%)", 0, 100, 30)
            with col2:
                medium_pct = st.slider("중 (%)", 0, 100, 50)
            with col3:
                hard_pct = 100 - easy_pct - medium_pct
                st.metric("상 (%)", hard_pct)
            
            if st.button("📝 모의고사 생성", type="primary"):
                with st.spinner(f"{num_problems}개의 교육과정 준수 문제를 생성하는 중..."):
                    if exam_type == "단원별" and generator_2015:
                        problems = generator_2015.generate_unit_test(
                            subject=exam_subject,
                            chapter=exam_chapter,
                            num_problems=num_problems
                        )
                    else:
                        # 통합형 모의고사
                        problems = generator.generate_exam(
                            exam_type="공통",
                            num_problems=num_problems
                        )
                    # 모든 문제에 LaTeX 렌더링 적용
                    problems = [latex_renderer.process_problem_text(p) for p in problems]
                    st.session_state['exam_problems'] = problems
    
    if (mode == "단일 문제 생성" or mode == "울트라 하드 문항 생성") and 'current_problem' in st.session_state:
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
                
                if problem.get('key_concepts') or problem.get('curriculum_concepts'):
                    with st.expander("핵심 개념"):
                        # 교육과정 핵심 개념 표시
                        curriculum_concepts = problem.get('curriculum_concepts', [])
                        if curriculum_concepts:
                            st.write("📖 교육과정 핵심 개념:")
                            for concept in curriculum_concepts:
                                st.markdown(f"- {concept}")
                        
                        # 기타 핵심 개념
                        key_concepts = problem.get('key_concepts', [])
                        if key_concepts:
                            st.write("💡 관련 개념:")
                            for concept in key_concepts:
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
                            "exam_type": "공통+선택",  # 2015 개정 교육과정 체제
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