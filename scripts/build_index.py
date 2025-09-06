#!/usr/bin/env python
"""
FAISS 인덱스 구축 스크립트
전처리된 문제 데이터로부터 벡터 검색 인덱스를 생성합니다.
"""
import sys
from pathlib import Path
import jsonlines
import argparse
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from src.retriever import EmbeddingGemma, FAISSIndexer, ProblemSearcher

load_dotenv()


def load_problems(file_path: str) -> List[Dict[str, Any]]:
    """JSONL 파일에서 문제 데이터 로드"""
    problems = []
    with jsonlines.open(file_path, 'r') as reader:
        for obj in reader:
            problems.append(obj)
    return problems


def main():
    parser = argparse.ArgumentParser(description="FAISS 인덱스 구축")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/problems.jsonl",
        help="입력 JSONL 파일 경로"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/index",
        help="인덱스 저장 경로"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("EMBEDDING_MODEL", "google/embedding-gemma-2b"),
        help="임베딩 모델 이름"
    )
    parser.add_argument(
        "--index-type",
        type=str,
        default=os.getenv("FAISS_INDEX_TYPE", "HNSW"),
        choices=["Flat", "HNSW", "IVF"],
        help="FAISS 인덱스 유형"
    )
    parser.add_argument(
        "--metric",
        type=str,
        default=os.getenv("FAISS_METRIC", "cosine"),
        choices=["cosine", "L2"],
        help="거리 측정 방식"
    )
    parser.add_argument(
        "--dimension",
        type=int,
        default=int(os.getenv("EMBEDDING_DIMENSION", "768")),
        help="임베딩 차원"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="배치 크기"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=os.getenv("DEVICE", "auto"),
        help="연산 디바이스 (auto/cuda/cpu)"
    )
    
    args = parser.parse_args()
    
    # 디바이스 설정
    if args.device == "auto":
        device = None  # 자동 선택
    else:
        device = args.device
    
    print(f"설정:")
    print(f"- 입력 파일: {args.input}")
    print(f"- 출력 경로: {args.output}")
    print(f"- 임베딩 모델: {args.model}")
    print(f"- 인덱스 유형: {args.index_type}")
    print(f"- 거리 측정: {args.metric}")
    print(f"- 임베딩 차원: {args.dimension}")
    print(f"- 디바이스: {device or 'auto'}")
    print()
    
    # 문제 데이터 로드
    print(f"문제 데이터 로드 중...")
    problems = load_problems(args.input)
    print(f"총 {len(problems)}개의 문제를 로드했습니다.")
    
    if not problems:
        print("문제가 없습니다. 종료합니다.")
        return
    
    # 임베딩 모델 초기화
    print(f"\n임베딩 모델 초기화 중...")
    try:
        embedder = EmbeddingGemma(
            model_name=args.model,
            device=device,
            batch_size=args.batch_size,
            max_length=512
        )
    except Exception as e:
        print(f"임베딩 모델 로드 실패: {e}")
        print("\nHuggingFace 토큰이 필요할 수 있습니다.")
        print("1. https://huggingface.co/settings/tokens 에서 토큰 발급")
        print("2. .env 파일에 HUGGINGFACE_TOKEN=your_token 추가")
        print("3. 또는 huggingface-cli login 실행")
        return
    
    # 인덱서 초기화
    print(f"\n인덱서 초기화 중...")
    indexer = FAISSIndexer(
        dimension=args.dimension,
        index_type=args.index_type,
        metric=args.metric
    )
    
    # ProblemSearcher 생성
    searcher = ProblemSearcher(
        embedder=embedder,
        indexer=indexer
    )
    
    # 문제 추가 및 인덱싱
    print(f"\n문제 인덱싱 중...")
    try:
        searcher.add_problems(problems, show_progress=True)
    except Exception as e:
        print(f"인덱싱 실패: {e}")
        return
    
    # 인덱스 저장
    print(f"\n인덱스 저장 중...")
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        searcher.save_index(str(output_path))
        print(f"인덱스를 {output_path}에 저장했습니다.")
    except Exception as e:
        print(f"인덱스 저장 실패: {e}")
        return
    
    # 테스트 검색
    print(f"\n테스트 검색 수행 중...")
    test_queries = [
        "미분 문제",
        "확률과 통계",
        "수열의 극한"
    ]
    
    for query in test_queries:
        print(f"\n쿼리: '{query}'")
        results = searcher.search(query, k=3)
        
        if results:
            for i, result in enumerate(results, 1):
                text = result['text'][:100] + "..." if len(result['text']) > 100 else result['text']
                print(f"  {i}. [점수: {result['score']:.3f}] {text}")
        else:
            print("  검색 결과가 없습니다.")
    
    print("\n인덱스 구축이 완료되었습니다!")
    print(f"\n다음 명령으로 검색 테스트를 수행할 수 있습니다:")
    print(f"python scripts/search_test.py --index {args.output} --query '미분 문제'")


if __name__ == "__main__":
    main()