#!/usr/bin/env python
"""
기출문제 데이터 준비 스크립트
JSONL 형식의 문제 데이터를 준비하고 전처리합니다.
"""
import json
import jsonlines
from pathlib import Path
import sys
import pandas as pd
from typing import List, Dict, Any
import argparse

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))


def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """JSON 파일에서 데이터 로드"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_jsonl_data(file_path: str) -> List[Dict[str, Any]]:
    """JSONL 파일에서 데이터 로드"""
    data = []
    with jsonlines.open(file_path, 'r') as reader:
        for obj in reader:
            data.append(obj)
    return data


def save_jsonl_data(data: List[Dict[str, Any]], file_path: str):
    """데이터를 JSONL 형식으로 저장"""
    with jsonlines.open(file_path, 'w') as writer:
        for obj in data:
            writer.write(obj)


def preprocess_problem(problem: Dict[str, Any]) -> Dict[str, Any]:
    """
    문제 데이터 전처리
    필수 필드: id, text(또는 question), topic, difficulty, type
    """
    processed = {}
    
    # ID 처리
    if 'id' in problem:
        processed['id'] = problem['id']
    else:
        # ID가 없으면 생성
        import hashlib
        text = problem.get('text', problem.get('question', ''))
        processed['id'] = hashlib.md5(text.encode()).hexdigest()[:12]
    
    # 텍스트 처리
    if 'text' in problem:
        processed['text'] = problem['text'].strip()
    elif 'question' in problem:
        processed['text'] = problem['question'].strip()
    else:
        raise ValueError("문제에 'text' 또는 'question' 필드가 필요합니다")
    
    # 메타데이터 처리
    metadata_fields = [
        'topic', 'subject', 'difficulty', 'type', 'exam_type',
        'year', 'month', 'number', 'points', 'answer', 'options'
    ]
    
    for field in metadata_fields:
        if field in problem:
            processed[field] = problem[field]
    
    # 키워드 추출 (간단한 버전)
    if 'keywords' not in processed:
        keywords = extract_keywords(processed['text'])
        if keywords:
            processed['keywords'] = keywords
    
    return processed


def extract_keywords(text: str) -> List[str]:
    """텍스트에서 수학 관련 키워드 추출"""
    math_keywords = [
        '미분', '적분', '극한', '함수', '방정식', '부등식',
        '확률', '통계', '기댓값', '분산', '표준편차',
        '벡터', '행렬', '공간', '평면', '직선',
        '수열', '급수', '등차', '등비', '시그마',
        '삼각함수', 'sin', 'cos', 'tan', '라디안',
        '지수', '로그', 'ln', 'log', 'e',
        '조합', '순열', '이항정리', '복소수'
    ]
    
    found_keywords = []
    text_lower = text.lower()
    
    for keyword in math_keywords:
        if keyword.lower() in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords[:5]  # 최대 5개


def create_sample_data() -> List[Dict[str, Any]]:
    """샘플 데이터 생성"""
    samples = [
        {
            "id": "sample_001",
            "text": "함수 f(x) = x³ - 3x² + 2x + 1에 대하여, f'(1)의 값을 구하시오.",
            "topic": "미분과 적분",
            "difficulty": "중",
            "type": "단답형",
            "exam_type": "공통",
            "points": 3,
            "answer": "2",
            "keywords": ["미분", "함수", "도함수"]
        },
        {
            "id": "sample_002",
            "text": "주사위를 두 번 던질 때, 나온 눈의 수의 합이 7 이상일 확률은?",
            "topic": "확률과 통계",
            "difficulty": "하",
            "type": "선택형",
            "exam_type": "공통",
            "points": 2,
            "options": ["①1/6", "②1/4", "③1/3", "④5/12", "⑤7/12"],
            "answer": "⑤",
            "keywords": ["확률", "주사위"]
        },
        {
            "id": "sample_003",
            "text": "수열 {aₙ}이 a₁ = 2, aₙ₊₁ = 2aₙ + 1 을 만족할 때, a₅의 값을 구하시오.",
            "topic": "수열",
            "difficulty": "중",
            "type": "단답형",
            "exam_type": "공통",
            "points": 3,
            "answer": "47",
            "keywords": ["수열", "점화식"]
        },
        {
            "id": "sample_004",
            "text": "∫₀¹ (x² + 2x) dx 의 값은?",
            "topic": "미분과 적분",
            "difficulty": "중",
            "type": "선택형",
            "exam_type": "공통",
            "points": 3,
            "options": ["①1/3", "②2/3", "③1", "④4/3", "⑤5/3"],
            "answer": "④",
            "keywords": ["적분", "정적분"]
        },
        {
            "id": "sample_005",
            "text": "cosθ = 3/5 일 때, sin2θ 의 값은? (단, 0 < θ < π/2)",
            "topic": "삼각함수",
            "difficulty": "중",
            "type": "선택형",
            "exam_type": "공통",
            "points": 3,
            "options": ["①12/25", "②16/25", "③18/25", "④21/25", "⑤24/25"],
            "answer": "⑤",
            "keywords": ["삼각함수", "cos", "sin", "배각공식"]
        }
    ]
    
    return samples


def main():
    parser = argparse.ArgumentParser(description="수학 문제 데이터 준비")
    parser.add_argument(
        "--input",
        type=str,
        help="입력 파일 경로 (JSON/JSONL)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/problems.jsonl",
        help="출력 파일 경로 (JSONL)"
    )
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="샘플 데이터 생성"
    )
    
    args = parser.parse_args()
    
    # 출력 디렉토리 생성
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if args.create_sample:
        # 샘플 데이터 생성
        print("샘플 데이터 생성 중...")
        data = create_sample_data()
        save_jsonl_data(data, args.output)
        print(f"샘플 데이터 {len(data)}개를 {args.output}에 저장했습니다.")
        
        # 통계 출력
        df = pd.DataFrame(data)
        print("\n데이터 통계:")
        print(f"- 총 문제 수: {len(df)}")
        print(f"- 주제별 분포:\n{df['topic'].value_counts()}")
        print(f"- 난이도별 분포:\n{df['difficulty'].value_counts()}")
        print(f"- 유형별 분포:\n{df['type'].value_counts()}")
        
    elif args.input:
        # 기존 데이터 처리
        print(f"{args.input} 파일 로드 중...")
        
        # 파일 형식에 따라 로드
        input_path = Path(args.input)
        if input_path.suffix == '.json':
            data = load_json_data(args.input)
        elif input_path.suffix == '.jsonl':
            data = load_jsonl_data(args.input)
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {input_path.suffix}")
        
        # 전처리
        print(f"{len(data)}개 문제 전처리 중...")
        processed_data = []
        errors = []
        
        for i, problem in enumerate(data):
            try:
                processed = preprocess_problem(problem)
                processed_data.append(processed)
            except Exception as e:
                errors.append((i, str(e)))
        
        # 저장
        save_jsonl_data(processed_data, args.output)
        print(f"전처리된 데이터 {len(processed_data)}개를 {args.output}에 저장했습니다.")
        
        if errors:
            print(f"\n오류 발생: {len(errors)}개")
            for idx, error in errors[:5]:  # 처음 5개만 표시
                print(f"  - 문제 {idx}: {error}")
        
        # 통계 출력
        if processed_data:
            df = pd.DataFrame(processed_data)
            print("\n데이터 통계:")
            print(f"- 총 문제 수: {len(df)}")
            if 'topic' in df.columns:
                print(f"- 주제별 분포:\n{df['topic'].value_counts().head()}")
            if 'difficulty' in df.columns:
                print(f"- 난이도별 분포:\n{df['difficulty'].value_counts()}")
            if 'type' in df.columns:
                print(f"- 유형별 분포:\n{df['type'].value_counts()}")
    
    else:
        print("입력 파일을 지정하거나 --create-sample 옵션을 사용하세요.")
        parser.print_help()


if __name__ == "__main__":
    main()