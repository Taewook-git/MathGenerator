# 📚 대학수학능력시험 수학 문제 생성기

Gemini AI API를 활용하여 한국 대학수학능력시험(수능) 수학 문제를 자동으로 생성하는 프로그램입니다.

## 주요 기능

- **단일 문제 생성**: 원하는 조건에 맞는 수능 수학 문제를 개별 생성
- **모의고사 생성**: 실제 수능과 유사한 형식의 전체 모의고사 세트 생성
- **맞춤형 설정**: 시험 유형(공통/선택과목), 문제 유형, 주제, 난이도, 배점 선택 가능
- **문제 저장 및 다운로드**: 생성된 문제를 JSON 형식으로 저장
- **PDF 출력**: LaTeX를 활용한 전문적인 모의고사 PDF 생성

## 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/ksat-math-ai.git
cd ksat-math-ai
```

### 2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. Gemini API 키 설정

1. [Google AI Studio](https://makersuite.google.com/app/apikey)에서 API 키 발급
2. `.env.example` 파일을 `.env`로 복사
3. `.env` 파일에 발급받은 API 키 입력

```bash
cp .env.example .env
```

`.env` 파일 내용:
```
GEMINI_API_KEY=your_actual_api_key_here
```

## 실행 방법

```bash
streamlit run app.py
```

브라우저에서 자동으로 `http://localhost:8501`이 열립니다.

## 사용 방법

### 단일 문제 생성
1. 좌측 사이드바에서 "단일 문제 생성" 모드 선택
2. 원하는 문제 조건 설정:
   - 시험 유형 (공통/미적분/확률과 통계/기하)
   - 문제 유형 (선택형/단답형)
   - 주제 (미적분, 확률과 통계 등)
   - 난이도 (하/중/상)
   - 배점 (2~4점)
3. "문제 생성" 버튼 클릭
4. 생성된 문제 확인 및 저장

### 모의고사 생성
1. 좌측 사이드바에서 "모의고사 생성" 모드 선택
2. 시험 유형과 문제 수 설정
3. "모의고사 생성" 버튼 클릭
4. 생성된 전체 문제 세트 확인 및 다운로드

## 프로젝트 구조

```
ksat-math-ai/
├── app.py                 # Streamlit 웹 애플리케이션
├── problem_generator.py   # 문제 생성 핵심 로직
├── pdf_generator.py      # PDF 생성 모듈
├── config.py             # 설정 및 상수 정의
├── requirements.txt      # 필요한 패키지 목록
├── .env.example         # 환경 변수 예시 파일
├── .gitignore           # Git 제외 파일 목록
└── README.md           # 프로젝트 문서
```

## 문제 유형 및 주제 (2015 개정 교육과정)

### 공통과목
- **수학1**: 지수함수와 로그함수, 삼각함수, 수열
- **수학2**: 함수의 극한과 연속, 미분, 적분

### 선택과목
- **미적분**: 수열의 극한, 미분법, 도함수의 활용, 적분법, 정적분의 활용
- **확률과 통계**: 경우의 수, 순열과 조합, 확률, 통계
- **기하**: 이차곡선, 평면벡터, 공간도형과 공간좌표

### 문항 구성
- **선택형**: 21문항 (2~4점)
- **단답형**: 9문항 (3~4점)
- **총 점수**: 100점

## PDF 생성 기능

### LaTeX 설치 (선택사항)
PDF 품질 향상을 위해 LaTeX 설치를 권장합니다:

**macOS:**
```bash
brew install --cask mactex
```

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-full texlive-xetex texlive-lang-korean
```

**Windows:**
[MiKTeX](https://miktex.org/download) 또는 [TeX Live](https://www.tug.org/texlive/) 설치

LaTeX가 설치되지 않은 경우에도 간단한 형식의 PDF 생성이 가능합니다.

## 주의사항

- Gemini API 사용량 제한이 있을 수 있으니 확인 필요
- 생성된 문제의 정확성은 AI 모델에 의존하므로 검토 필요
- 실제 수능 문제와 완전히 동일한 품질을 보장하지 않음
- PDF 생성 시 한글 폰트 설정이 필요할 수 있음

## 라이센스

MIT License

## 기여 방법

버그 리포트, 기능 제안, 풀 리퀘스트 등 모든 기여를 환영합니다!