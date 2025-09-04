# 📁 KSAT Math AI 프로젝트 구조

## 🏗️ 디렉토리 구조

```
ksat-math-ai/
├── src/                        # 소스 코드 루트
│   ├── __init__.py            # 패키지 초기화
│   ├── core/                  # 핵심 기능
│   │   ├── __init__.py
│   │   ├── config.py          # 설정 및 상수
│   │   └── problem_generator.py # 문제 생성 엔진
│   │
│   ├── generators/            # 생성기 모듈
│   │   ├── __init__.py
│   │   ├── graph_generator.py # 그래프 생성
│   │   ├── latex_renderer.py  # LaTeX 렌더링
│   │   ├── pdf_generator.py   # PDF 생성
│   │   └── ultra_hard_problems.py # 킬러 문제
│   │
│   ├── validators/            # 검증 모듈
│   │   ├── __init__.py
│   │   ├── quality_validator.py # 품질 검증
│   │   └── error_fixes.py    # 오류 수정
│   │
│   ├── ui/                    # 사용자 인터페이스
│   │   ├── __init__.py
│   │   └── app.py             # Streamlit 앱
│   │
│   ├── tests/                 # 테스트 모듈
│   │   ├── __init__.py
│   │   ├── test_killer_fixes.py
│   │   ├── test_quality_enhancement.py
│   │   └── test_torch_fix.py
│   │
│   └── docs/                  # 문서
│       ├── README.md
│       └── ULTRA_HARD_FEATURES.md
│
├── .env                       # 환경 변수
├── .env.example              # 환경 변수 예시
├── .gitignore                # Git 제외 파일
├── requirements.txt          # 의존성 목록
├── setup.py                  # 패키지 설정
├── run_app.py               # 실행 스크립트
├── search.sh                # 검색 스크립트
└── PROJECT_STRUCTURE.md     # 이 문서
```

## 📦 모듈 설명

### 🎯 Core (핵심 모듈)
- **config.py**: 2015 개정 교육과정 설정, API 키, 난이도 기준
- **problem_generator.py**: 메인 문제 생성 엔진, Gemini AI 연동

### 🎨 Generators (생성기 모듈)
- **graph_generator.py**: 수학 그래프 및 도형 생성
- **latex_renderer.py**: LaTeX 수식 렌더링
- **pdf_generator.py**: PDF 시험지 생성
- **ultra_hard_problems.py**: 킬러 문제 생성 (항등식, 융합, 부등식)

### ✅ Validators (검증 모듈)
- **quality_validator.py**: SymPy 기반 수학 검증, 품질 향상
- **error_fixes.py**: JSON 파싱 오류 수정, 문제 검증

### 🖥️ UI (사용자 인터페이스)
- **app.py**: Streamlit 웹 애플리케이션

### 🧪 Tests (테스트 모듈)
- 각종 기능 단위 테스트 및 통합 테스트

## 🚀 실행 방법

### 1. 환경 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에 GEMINI_API_KEY 입력
```

### 2. 애플리케이션 실행
```bash
# 방법 1: 실행 스크립트 사용
python run_app.py

# 방법 2: Streamlit 직접 실행
streamlit run src/ui/app.py

# 방법 3: 패키지 설치 후 실행
pip install -e .
ksat-math
```

### 3. 테스트 실행
```bash
# 모든 테스트 실행
python -m pytest src/tests/

# 특정 테스트 실행
python src/tests/test_killer_fixes.py
```

## 🔧 개발 가이드

### 새 모듈 추가 시
1. 적절한 디렉토리에 파일 생성
2. 해당 디렉토리의 `__init__.py`에 export 추가
3. 필요한 경우 테스트 파일 작성

### Import 규칙
```python
# 같은 모듈 내
from .config import SOME_CONFIG

# 다른 모듈
from ..validators.quality_validator import MathValidator

# UI나 테스트에서 (sys.path 추가 필요)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.problem_generator import KSATMathGenerator
```

## 📝 주요 기능

1. **일반 문제 생성**: 수학1, 수학2, 미적분 전 범위
2. **킬러 문제 생성**: 초고난도 문제 (항등식, 다단원 융합)
3. **품질 검증**: SymPy 기반 수식 검증
4. **PDF 출력**: 시험지 형식으로 출력
5. **LaTeX 렌더링**: 수식 시각화

## 🔐 환경 변수

`.env` 파일에 다음 설정 필요:
```
GEMINI_API_KEY=your-api-key-here
```

## 📚 문서

- [README](src/docs/README.md): 프로젝트 개요
- [ULTRA_HARD_FEATURES](src/docs/ULTRA_HARD_FEATURES.md): 킬러 문제 기능 상세

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request