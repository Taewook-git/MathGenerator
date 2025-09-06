"""
PDF 생성 모듈
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from typing import List, Dict, Any
import os
from pathlib import Path


class PDFGenerator:
    """수학 문제 PDF 생성기"""
    
    def __init__(self):
        """초기화"""
        self._register_fonts()
        self.styles = self._create_styles()
        
    def _register_fonts(self):
        """한글 폰트 등록"""
        # 시스템 폰트 경로들
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "C:/Windows/Fonts/malgun.ttf",
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    # 폰트 등록 시도
                    if font_path.endswith('.ttf'):
                        pdfmetrics.registerFont(TTFont('Korean', font_path))
                        return
                except:
                    continue
                    
    def _create_styles(self):
        """스타일 생성"""
        styles = getSampleStyleSheet()
        
        # 제목 스타일
        styles.add(ParagraphStyle(
            name='KoreanTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        
        # 문제 스타일
        styles.add(ParagraphStyle(
            name='Problem',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=10,
            leading=15
        ))
        
        # 보기 스타일
        styles.add(ParagraphStyle(
            name='Option',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leftIndent=20,
            spaceAfter=5
        ))
        
        # 메타데이터 스타일
        styles.add(ParagraphStyle(
            name='Meta',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_LEFT
        ))
        
        return styles
        
    def generate_problems_pdf(self, problems: List[Dict[str, Any]]) -> bytes:
        """
        문제 리스트를 PDF로 생성
        
        Args:
            problems: 문제 리스트
            
        Returns:
            PDF 바이트 데이터
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # 제목
        title = Paragraph("수학 문제", self.styles['KoreanTitle'])
        story.append(title)
        story.append(Spacer(1, 0.5*cm))
        
        # 문제들
        for i, problem in enumerate(problems, 1):
            # 문제 번호와 텍스트
            problem_text = f"<b>{i}.</b> {problem.get('question', problem.get('text', ''))}"
            para = Paragraph(problem_text, self.styles['Problem'])
            story.append(para)
            
            # 선택지
            if problem.get('options'):
                for option in problem['options']:
                    option_para = Paragraph(option, self.styles['Option'])
                    story.append(option_para)
                    
            # 메타데이터
            meta_parts = []
            if problem.get('topic'):
                meta_parts.append(f"주제: {problem['topic']}")
            if problem.get('difficulty'):
                meta_parts.append(f"난이도: {problem['difficulty']}")
            if problem.get('points'):
                meta_parts.append(f"배점: {problem['points']}점")
                
            if meta_parts:
                meta_text = " | ".join(meta_parts)
                meta_para = Paragraph(meta_text, self.styles['Meta'])
                story.append(meta_para)
                
            story.append(Spacer(1, 0.5*cm))
            
            # 페이지 나누기 (5문제마다)
            if i % 5 == 0 and i < len(problems):
                story.append(PageBreak())
                
        # 정답 페이지
        story.append(PageBreak())
        answer_title = Paragraph("정답", self.styles['KoreanTitle'])
        story.append(answer_title)
        story.append(Spacer(1, 0.5*cm))
        
        # 정답 테이블
        answer_data = []
        for i, problem in enumerate(problems, 1):
            answer = problem.get('answer', '-')
            answer_data.append([str(i), str(answer)])
            
        # 5열로 정리
        answer_table_data = []
        for i in range(0, len(answer_data), 5):
            row = []
            for j in range(5):
                if i + j < len(answer_data):
                    row.extend(answer_data[i + j])
                else:
                    row.extend(['', ''])
            answer_table_data.append(row)
            
        answer_table = Table(answer_table_data)
        answer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(answer_table)
        
        # PDF 빌드
        doc.build(story)
        
        # 바이트 데이터 반환
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    def generate_exam_pdf(self, problems: List[Dict[str, Any]]) -> bytes:
        """
        모의고사 PDF 생성
        
        Args:
            problems: 문제 리스트
            
        Returns:
            PDF 바이트 데이터
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # 표지
        cover_title = Paragraph(
            "대학수학능력시험 모의고사<br/>수학 영역",
            self.styles['KoreanTitle']
        )
        story.append(Spacer(1, 5*cm))
        story.append(cover_title)
        story.append(Spacer(1, 2*cm))
        
        # 시험 정보
        exam_info = Paragraph(
            f"문항 수: {len(problems)}문제<br/>"
            f"시험 시간: 100분<br/>"
            f"배점: 100점",
            self.styles['Problem']
        )
        story.append(exam_info)
        story.append(PageBreak())
        
        # 문제들
        for i, problem in enumerate(problems, 1):
            # 문제 번호와 배점
            problem_header = f"<b>{i}.</b> "
            if problem.get('points'):
                problem_header += f"[{problem['points']}점] "
                
            problem_text = problem_header + problem.get('question', problem.get('text', ''))
            para = Paragraph(problem_text, self.styles['Problem'])
            story.append(para)
            
            # 선택지
            if problem.get('options'):
                for option in problem['options']:
                    option_para = Paragraph(option, self.styles['Option'])
                    story.append(option_para)
                    
            story.append(Spacer(1, 0.7*cm))
            
            # 페이지 나누기 (적절히)
            if i in [7, 14, 21]:  # 7문제씩
                story.append(PageBreak())
                
        # 답안지
        story.append(PageBreak())
        answer_sheet_title = Paragraph("답안지", self.styles['KoreanTitle'])
        story.append(answer_sheet_title)
        story.append(Spacer(1, 1*cm))
        
        # 답안 표
        answer_grid = []
        for i in range(1, len(problems) + 1):
            if problem.get('type') == '선택형':
                answer_grid.append([
                    str(i),
                    "①", "②", "③", "④", "⑤"
                ])
            else:
                answer_grid.append([
                    str(i),
                    "___________"
                ])
                
        answer_table = Table(answer_grid[:15])  # 처음 15문제
        answer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(answer_table)
        
        if len(problems) > 15:
            story.append(Spacer(1, 1*cm))
            answer_table2 = Table(answer_grid[15:])
            answer_table2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(answer_table2)
            
        # PDF 빌드
        doc.build(story)
        
        # 바이트 데이터 반환
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes