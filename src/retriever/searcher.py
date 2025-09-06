"""
통합 검색 인터페이스
"""
from typing import List, Optional, Dict, Any, Tuple
from .embedder import EmbeddingGemma
from .indexer import FAISSIndexer
import json
from pathlib import Path


class ProblemSearcher:
    """수학 문제 검색 시스템"""
    
    def __init__(
        self,
        embedder: Optional[EmbeddingGemma] = None,
        indexer: Optional[FAISSIndexer] = None,
        index_path: Optional[str] = None
    ):
        """
        Args:
            embedder: 임베딩 모델
            indexer: FAISS 인덱서
            index_path: 기존 인덱스 경로
        """
        self.embedder = embedder or EmbeddingGemma()
        self.indexer = indexer or FAISSIndexer()
        
        if index_path and Path(index_path).exists():
            self.load_index(index_path)
            
    def add_problems(
        self,
        problems: List[Dict[str, Any]],
        show_progress: bool = True
    ):
        """
        문제들을 인덱스에 추가
        
        Args:
            problems: 문제 리스트 (각 문제는 최소한 'text' 필드 포함)
            show_progress: 진행 상황 표시
        """
        # 텍스트 추출
        texts = []
        metadata = []
        
        for prob in problems:
            # 검색용 텍스트 생성
            search_text = self._create_search_text(prob)
            texts.append(search_text)
            
            # 메타데이터 저장
            meta = {k: v for k, v in prob.items() if k != 'text'}
            metadata.append(meta)
            
        # 임베딩 생성
        print("Creating embeddings...")
        embeddings = self.embedder.encode_documents(texts, show_progress=show_progress)
        
        # 인덱스에 추가
        self.indexer.add(embeddings, texts, metadata)
        
    def search(
        self,
        query: str,
        conditions: Optional[Dict[str, Any]] = None,
        k: int = 10,
        rerank: bool = False
    ) -> List[Dict[str, Any]]:
        """
        문제 검색
        
        Args:
            query: 검색 쿼리
            conditions: 추가 필터 조건 (난이도, 주제 등)
            k: 검색할 문제 개수
            rerank: 재랭킹 여부
            
        Returns:
            검색된 문제 리스트
        """
        # 쿼리 임베딩
        query_embedding = self.embedder.encode_queries(query)
        
        # 벡터 검색
        results = self.indexer.search(query_embedding, k=k*2 if conditions else k)
        
        # 조건 필터링
        if conditions:
            filtered_results = []
            for doc, score, meta in results:
                if self._match_conditions(meta, conditions):
                    filtered_results.append({
                        "text": doc,
                        "score": score,
                        "metadata": meta
                    })
                if len(filtered_results) >= k:
                    break
            results = filtered_results[:k]
        else:
            results = [
                {"text": doc, "score": score, "metadata": meta}
                for doc, score, meta in results
            ]
            
        # 재랭킹 (선택사항)
        if rerank and len(results) > 0:
            results = self._rerank(query, results)
            
        return results
    
    def _create_search_text(self, problem: Dict[str, Any]) -> str:
        """문제를 검색용 텍스트로 변환"""
        parts = []
        
        # 문제 텍스트
        if 'text' in problem:
            parts.append(problem['text'])
        if 'question' in problem:
            parts.append(problem['question'])
            
        # 메타데이터 추가
        if 'topic' in problem:
            parts.append(f"주제: {problem['topic']}")
        if 'difficulty' in problem:
            parts.append(f"난이도: {problem['difficulty']}")
        if 'type' in problem:
            parts.append(f"유형: {problem['type']}")
        if 'keywords' in problem:
            parts.append(f"키워드: {', '.join(problem['keywords'])}")
            
        return " ".join(parts)
    
    def _match_conditions(
        self,
        metadata: Dict[str, Any],
        conditions: Dict[str, Any]
    ) -> bool:
        """메타데이터가 조건과 일치하는지 확인"""
        for key, value in conditions.items():
            if key not in metadata:
                return False
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        return True
    
    def _rerank(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        검색 결과 재랭킹 (추후 LLM 기반으로 확장 가능)
        현재는 점수 기반 정렬만 수행
        """
        return sorted(results, key=lambda x: x['score'], reverse=True)
    
    def save_index(self, path: str):
        """인덱스 저장"""
        self.indexer.save(path)
        
    def load_index(self, path: str):
        """인덱스 로드"""
        self.indexer.load(path)
        
    def clear_index(self):
        """인덱스 초기화"""
        self.indexer.clear()