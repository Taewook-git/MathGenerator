import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import Optional, Tuple, Dict, Any
import io
import base64
from matplotlib import font_manager, rc
import platform

# 시스템에 따른 한글 폰트 설정
def setup_korean_font():
    system = platform.system()
    
    # 사용 가능한 모든 폰트 이름 가져오기
    available_fonts = set([f.name for f in font_manager.fontManager.ttflist])
    
    if system == 'Darwin':  # macOS
        # 수능 스타일에 가까운 폰트 우선순위
        font_candidates = [
            'AppleSDGothicNeo',  # Apple SD Gothic Neo (수능과 유사)
            'Apple SD Gothic Neo',  # 다른 표기
            'AppleGothic',
            'Apple Gothic',
            'AppleMyungjo',
            'Nanum Gothic',
            'NanumGothic',
            'Malgun Gothic',
            'Arial Unicode MS',  # macOS의 대체 유니코드 폰트
            'Helvetica'
        ]
    elif system == 'Windows':
        font_candidates = [
            'Malgun Gothic',
            'NanumGothic',
            'Gulim',
            'Batang',
            'Arial Unicode MS'
        ]
    else:  # Linux
        font_candidates = [
            'NanumGothic',
            'NanumMyeongjo',
            'UnDotum',
            'DejaVu Sans'
        ]
    
    # 사용 가능한 폰트 찾기
    for font_name in font_candidates:
        if font_name in available_fonts:
            return font_name
    
    # 한글을 지원하는 폰트 찾기 (폴백)
    for font in available_fonts:
        if 'Gothic' in font or 'Nanum' in font or 'Malgun' in font:
            return font
    
    return 'DejaVu Sans'  # 최종 폴백

# 한글 폰트 설정
korean_font = setup_korean_font()
print(f"Using font: {korean_font}")  # 디버그용
plt.rcParams['font.family'] = korean_font
plt.rcParams['axes.unicode_minus'] = False

# 수능 스타일 설정
plt.rcParams['font.size'] = 11  # 수능 표준 폰트 크기
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 12

# 선 스타일 설정
plt.rcParams['lines.linewidth'] = 1.5
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.linewidth'] = 0.5
plt.rcParams['grid.alpha'] = 0.3

class MathGraphGenerator:
    def __init__(self):
        self.fig_size = (6.5, 5)  # 수능 크기에 맞춤
        self.dpi = 120  # 고품질 출력
        self.ksat_style = {
            'axes_color': '#000000',
            'grid_color': '#cccccc',
            'background_color': '#ffffff',
            'font_family': korean_font,
            'math_font': 'stix',  # 수학 기호용 폰트
        }
        
    def generate_trigonometric_graph(self, 
                                    functions: list,
                                    x_range: Tuple[float, float] = (-2*np.pi, 2*np.pi),
                                    title: str = "Trigonometric Functions",
                                    show_grid: bool = True) -> str:
        """
        삼각함수 그래프 생성
        
        Args:
            functions: 그릴 함수들의 리스트 (예: ['sin', 'cos', 'tan'])
            x_range: x축 범위
            title: 그래프 제목
            show_grid: 그리드 표시 여부
            
        Returns:
            base64 인코딩된 이미지 문자열
        """
        fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)
        
        # 수능 스타일 배경 설정
        fig.patch.set_facecolor(self.ksat_style['background_color'])
        ax.set_facecolor(self.ksat_style['background_color'])
        
        x = np.linspace(x_range[0], x_range[1], 1000)
        
        # 수능에서 사용하는 색상 (진한 검정, 파랑, 빨강 위주)
        function_map = {
            'sin': (np.sin, 'sin x', '#0000FF'),  # 파랑
            'cos': (np.cos, 'cos x', '#FF0000'),  # 빨강
            'tan': (np.tan, 'tan x', '#008000'),  # 초록
            'cot': (lambda x: 1/np.tan(x), 'cot x', '#FF8C00'),
            'sec': (lambda x: 1/np.cos(x), 'sec x', '#800080'),
            'csc': (lambda x: 1/np.sin(x), 'csc x', '#8B4513')
        }
        
        for func_name in functions:
            if func_name in function_map:
                func, label, color = function_map[func_name]
                y = func(x)
                
                # tan, cot, sec, csc의 경우 불연속점 처리
                if func_name in ['tan', 'cot', 'sec', 'csc']:
                    y[np.abs(y) > 10] = np.nan
                
                ax.plot(x, y, label=label, color=color, linewidth=1.8)
        
        # x축, y축 설정 (수능 스타일: 진한 검정색)
        ax.axhline(y=0, color='black', linewidth=1.2, zorder=5)
        ax.axvline(x=0, color='black', linewidth=1.2, zorder=5)
        
        # 축 화살표 추가 (수능 스타일)
        ax.annotate('', xy=(x_range[1], 0), xytext=(x_range[1]-0.1, 0),
                   arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
        ax.annotate('', xy=(0, 3), xytext=(0, 2.9),
                   arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
        
        # 축 라벨 (수능 스타일)
        ax.text(x_range[1]-0.2, -0.3, 'x', fontsize=11, style='italic')
        ax.text(0.2, 2.8, 'y', fontsize=11, style='italic')
        
        # π 단위로 x축 눈금 설정
        pi_ticks = np.arange(x_range[0], x_range[1] + np.pi/2, np.pi/2)
        pi_labels = []
        for tick in pi_ticks:
            if tick == 0:
                pi_labels.append('0')
            elif tick == np.pi:
                pi_labels.append('π')
            elif tick == -np.pi:
                pi_labels.append('-π')
            elif tick == np.pi/2:
                pi_labels.append('π/2')
            elif tick == -np.pi/2:
                pi_labels.append('-π/2')
            elif tick == 2*np.pi:
                pi_labels.append('2π')
            elif tick == -2*np.pi:
                pi_labels.append('-2π')
            else:
                pi_labels.append(f'{tick/np.pi:.1f}π')
        
        ax.set_xticks(pi_ticks)
        ax.set_xticklabels(pi_labels)
        
        ax.set_ylim(-3, 3)
        
        # 수능 스타일: 축 라벨 제거 (이미 화살표 옆에 표시)
        ax.set_xlabel('')
        ax.set_ylabel('')
        
        # 제목 스타일 (수능은 보통 제목 없음)
        if title and title != "Trigonometric Functions":
            ax.set_title(title, fontsize=12, fontweight='normal', pad=10)
        
        # 범례 스타일 (수능 스타일)
        ax.legend(loc='upper right', frameon=True, fancybox=False,
                 edgecolor='black', framealpha=1.0, fontsize=9)
        
        if show_grid:
            ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5)
        
        # 축 스타일 설정
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(0.8)
        ax.spines['bottom'].set_linewidth(0.8)
        
        return self._fig_to_base64(fig)
    
    def generate_geometry_figure(self, 
                                figure_type: str,
                                params: Dict[str, Any] = None) -> str:
        """
        기하 도형 생성
        
        Args:
            figure_type: 도형 유형 ('triangle', 'circle', 'rectangle', 'polygon' 등)
            params: 도형 파라미터
            
        Returns:
            base64 인코딩된 이미지 문자열
        """
        fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)
        
        if figure_type == 'triangle':
            # 삼각형 그리기
            vertices = params.get('vertices', [(0, 0), (2, 0), (1, 1.732)])
            triangle = patches.Polygon(vertices, closed=True, 
                                     edgecolor='black', facecolor='lightblue',
                                     linewidth=2)
            ax.add_patch(triangle)
            
            # 꼭짓점 표시
            for i, (x, y) in enumerate(vertices):
                ax.plot(x, y, 'ko', markersize=8)
                ax.annotate(chr(65+i), (x, y), xytext=(5, 5), 
                          textcoords='offset points', fontsize=12)
            
            # 변의 길이 표시 (선택적)
            if params.get('show_sides', False):
                for i in range(len(vertices)):
                    x1, y1 = vertices[i]
                    x2, y2 = vertices[(i+1) % len(vertices)]
                    mid_x, mid_y = (x1+x2)/2, (y1+y2)/2
                    length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    ax.annotate(f'{length:.2f}', (mid_x, mid_y), 
                              fontsize=10, ha='center')
        
        elif figure_type == 'circle':
            # 원 그리기
            center = params.get('center', (0, 0))
            radius = params.get('radius', 1)
            circle = patches.Circle(center, radius, 
                                   edgecolor='black', facecolor='lightgreen',
                                   linewidth=2)
            ax.add_patch(circle)
            
            # 중심점 표시
            ax.plot(center[0], center[1], 'ko', markersize=8)
            ax.annotate('O', center, xytext=(5, 5), 
                      textcoords='offset points', fontsize=12)
            
            # 반지름 표시
            if params.get('show_radius', False):
                ax.plot([center[0], center[0]+radius], 
                       [center[1], center[1]], 'k--', linewidth=1)
                ax.annotate(f'r={radius}', 
                          (center[0]+radius/2, center[1]+0.1), 
                          fontsize=10)
        
        elif figure_type == 'rectangle':
            # 직사각형 그리기
            corner = params.get('corner', (0, 0))
            width = params.get('width', 3)
            height = params.get('height', 2)
            rect = patches.Rectangle(corner, width, height,
                                    edgecolor='black', facecolor='lightyellow',
                                    linewidth=2)
            ax.add_patch(rect)
            
            # 꼭짓점 표시
            vertices = [corner, 
                       (corner[0]+width, corner[1]),
                       (corner[0]+width, corner[1]+height),
                       (corner[0], corner[1]+height)]
            for i, (x, y) in enumerate(vertices):
                ax.plot(x, y, 'ko', markersize=8)
                ax.annotate(chr(65+i), (x, y), xytext=(5, 5),
                          textcoords='offset points', fontsize=12)
        
        elif figure_type == 'coordinate_system':
            # 좌표계와 점들 그리기
            points = params.get('points', [(1, 2), (-1, 1), (2, -1)])
            
            # 좌표축
            ax.axhline(y=0, color='black', linewidth=1)
            ax.axvline(x=0, color='black', linewidth=1)
            
            # 점들 그리기
            for i, (x, y) in enumerate(points):
                ax.plot(x, y, 'ro', markersize=8)
                ax.annotate(f'P{i+1}({x},{y})', (x, y), 
                          xytext=(5, 5), textcoords='offset points',
                          fontsize=10)
            
            # 선분 연결 (선택적)
            if params.get('connect_points', False) and len(points) > 1:
                try:
                    points_array = np.array(points, dtype=float)
                    ax.plot(points_array[:, 0], points_array[:, 1], 
                           'b-', linewidth=1, alpha=0.5)
                except (ValueError, TypeError):
                    # 점을 변환할 수 없으면 연결선을 그리지 않음
                    pass
        
        # 축 설정
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        
        # 축 범위 자동 조정
        ax.autoscale()
        margin = 0.5
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        ax.set_xlim(xlim[0]-margin, xlim[1]+margin)
        ax.set_ylim(ylim[0]-margin, ylim[1]+margin)
        
        if params and params.get('title'):
            ax.set_title(params['title'])
        
        return self._fig_to_base64(fig)
    
    def generate_function_graph(self,
                              function_str: str,
                              x_range: Tuple[float, float] = (-10, 10),
                              title: str = "Function Graph") -> str:
        """
        일반 함수 그래프 생성
        
        Args:
            function_str: 함수 문자열 (예: "x**2 + 2*x + 1")
            x_range: x축 범위
            title: 그래프 제목
            
        Returns:
            base64 인코딩된 이미지 문자열
        """
        fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)
        
        x = np.linspace(x_range[0], x_range[1], 1000)
        
        # 안전한 함수 평가
        try:
            # function_str 전처리 - 일반적인 수학 표현을 Python 표현으로
            processed_str = function_str
            processed_str = processed_str.replace('^', '**')  # 지수 표현
            processed_str = processed_str.replace('×', '*')    # 곱셈 기호
            processed_str = processed_str.replace('÷', '/')    # 나눗셈 기호
            
            # numpy 함수들을 사용 가능하게 함
            # 상수 및 변수 추가
            safe_dict = {
                'x': x, 'np': np, 
                'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
                'sinh': np.sinh, 'cosh': np.cosh, 'tanh': np.tanh,
                'exp': np.exp, 'log': np.log, 'log10': np.log10, 'sqrt': np.sqrt,
                'pi': np.pi, 'e': np.e,
                # 추가 상수들 - 일반적으로 사용되는 매개변수
                'a': 1, 'b': 1, 'c': 1, 'd': 1,  # 기본 계수
                'm': 1, 'n': 1, 'k': 1, 'p': 1, 'q': 1,  # 추가 파라미터
                'abs': np.abs, 'pow': np.power,
                'floor': np.floor, 'ceil': np.ceil,
                'min': np.minimum, 'max': np.maximum
            }
            
            # function_str에서 변수 추출 및 safe_dict 업데이트
            import re
            # a_1, a_2 같은 패턴 찾기
            subscript_vars = re.findall(r'([a-z])_(\d+)', processed_str)
            for var, num in subscript_vars:
                safe_dict[f'{var}_{num}'] = 1
            
            # 추가 변수 패턴 찾기 (대문자 상수)
            upper_vars = re.findall(r'\b([A-Z])\b', processed_str)
            for var in upper_vars:
                if var not in safe_dict:
                    safe_dict[var] = 1
            
            y = eval(processed_str, {"__builtins__": {}}, safe_dict)
            
            # NaN이나 Inf 처리
            y = np.where(np.isfinite(y), y, np.nan)
            
            ax.plot(x, y, 'b-', linewidth=2, label=f'y = {function_str}')
            
            # 축 그리기
            ax.axhline(y=0, color='black', linewidth=0.5)
            ax.axvline(x=0, color='black', linewidth=0.5)
            
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.set_title(title)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        except NameError as e:
            # 변수 이름 오류 처리
            missing_var = str(e).split("'")[1] if "'" in str(e) else "unknown"
            error_msg = f'변수 오류: {missing_var}가 정의되지 않았습니다.\n함수에 사용할 수 있는 변수는 x입니다.'
            ax.text(0.5, 0.5, error_msg, 
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=10, wrap=True)
            ax.set_title(f'그래프 생성 실패: {function_str}')
        except SyntaxError as e:
            error_msg = f'구문 오류: 올바른 수식이 아닙니다.\n예: x**2, sin(x), exp(x)'
            ax.text(0.5, 0.5, error_msg, 
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=10, wrap=True)
            ax.set_title(f'그래프 생성 실패: {function_str}')
        except Exception as e:
            ax.text(0.5, 0.5, f'오류: {str(e)}', 
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=10)
        
        return self._fig_to_base64(fig)
    
    def generate_vector_diagram(self,
                              vectors: list,
                              origin: Tuple[float, float] = (0, 0),
                              title: str = "Vector Diagram") -> str:
        """
        벡터 다이어그램 생성
        
        Args:
            vectors: 벡터 리스트 [(dx, dy, label), ...]
            origin: 시작점
            title: 그래프 제목
            
        Returns:
            base64 인코딩된 이미지 문자열
        """
        fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)
        
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        
        for i, vector_data in enumerate(vectors):
            if len(vector_data) == 3:
                dx, dy, label = vector_data
            else:
                dx, dy = vector_data
                label = f'v{i+1}'
            
            color = colors[i % len(colors)]
            
            # 벡터 화살표 그리기
            ax.quiver(origin[0], origin[1], dx, dy,
                     angles='xy', scale_units='xy', scale=1,
                     color=color, width=0.005, 
                     label=label)
            
            # 벡터 끝점에 라벨 표시
            ax.annotate(label, 
                       (origin[0] + dx, origin[1] + dy),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=10)
        
        # 축 설정
        ax.set_aspect('equal')
        ax.axhline(y=0, color='black', linewidth=0.5)
        ax.axvline(x=0, color='black', linewidth=0.5)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title(title)
        ax.legend()
        
        # 축 범위 자동 조정
        ax.autoscale()
        margin = 1
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        ax.set_xlim(xlim[0]-margin, xlim[1]+margin)
        ax.set_ylim(ylim[0]-margin, ylim[1]+margin)
        
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """
        matplotlib figure를 base64 문자열로 변환
        """
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_base64
    
    def save_graph_to_file(self, base64_str: str, filename: str):
        """
        base64 이미지를 파일로 저장
        """
        img_data = base64.b64decode(base64_str)
        with open(filename, 'wb') as f:
            f.write(img_data)