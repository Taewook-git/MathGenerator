"""
FAISS를 사용한 벡터 인덱싱 및 검색 모듈
"""
import faiss
import numpy as np
import pickle
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import json


class FAISSIndexer:
    """FAISS 기반 벡터 검색 인덱서"""
    
    def __init__(
        self,
        dimension: int = 768,
        index_type: str = "HNSW",
        metric: str = "cosine"
    ):
        """
        Args:
            dimension: 임베딩 차원
            index_type: 인덱스 유형 (Flat, HNSW, IVF)
            metric: 거리 측정 방식 (L2, cosine)
        """
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        self.index = self._create_index()
        self.documents = []
        self.metadata = []
        
    def _create_index(self) -> faiss.Index:
        """FAISS 인덱스 생성"""
        if self.metric == "cosine":
            # 코사인 유사도를 위한 정규화 + 내적
            if self.index_type == "Flat":
                index = faiss.IndexFlatIP(self.dimension)
            elif self.index_type == "HNSW":
                index = faiss.IndexHNSWFlat(self.dimension, 32, faiss.METRIC_INNER_PRODUCT)
                index.hnsw.efConstruction = 40
            elif self.index_type == "IVF":
                quantizer = faiss.IndexFlatIP(self.dimension)
                index = faiss.IndexIVFFlat(quantizer, self.dimension, 100, faiss.METRIC_INNER_PRODUCT)
            else:
                raise ValueError(f"Unknown index type: {self.index_type}")
        else:  # L2
            if self.index_type == "Flat":
                index = faiss.IndexFlatL2(self.dimension)
            elif self.index_type == "HNSW":
                index = faiss.IndexHNSWFlat(self.dimension, 32)
                index.hnsw.efConstruction = 40
            elif self.index_type == "IVF":
                quantizer = faiss.IndexFlatL2(self.dimension)
                index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            else:
                raise ValueError(f"Unknown index type: {self.index_type}")
                
        return index
    
    def add(
        self,
        embeddings: np.ndarray,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ):
        """
        벡터와 문서를 인덱스에 추가
        
        Args:
            embeddings: 임베딩 벡터 배열
            documents: 원본 문서 리스트
            metadata: 문서별 메타데이터
        """
        if len(embeddings) != len(documents):
            raise ValueError("임베딩과 문서 개수가 일치하지 않습니다")
            
        # IVF 인덱스는 학습이 필요
        if self.index_type == "IVF" and not self.index.is_trained:
            print("Training IVF index...")
            self.index.train(embeddings)
            
        # 인덱스에 추가
        self.index.add(embeddings)
        self.documents.extend(documents)
        
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(documents))
            
        print(f"Added {len(documents)} documents. Total: {self.index.ntotal}")
        
    def search(
        self,
        query_embeddings: np.ndarray,
        k: int = 10,
        threshold: Optional[float] = None
    ) -> List[List[Tuple[str, float, Dict]]]:
        """
        유사한 문서 검색
        
        Args:
            query_embeddings: 쿼리 임베딩
            k: 검색할 문서 개수
            threshold: 최소 유사도 임계값
            
        Returns:
            검색 결과 [(문서, 점수, 메타데이터), ...]
        """
        if self.index.ntotal == 0:
            return []
            
        # 검색 수행
        if len(query_embeddings.shape) == 1:
            query_embeddings = query_embeddings.reshape(1, -1)
            
        distances, indices = self.index.search(query_embeddings, min(k, self.index.ntotal))
        
        # 결과 포맷팅
        results = []
        for dist_row, idx_row in zip(distances, indices):
            query_results = []
            for dist, idx in zip(dist_row, idx_row):
                if idx == -1:  # 검색 실패
                    continue
                if threshold and dist < threshold:
                    continue
                    
                query_results.append((
                    self.documents[idx],
                    float(dist),
                    self.metadata[idx] if self.metadata else {}
                ))
            results.append(query_results)
            
        return results[0] if len(results) == 1 else results
    
    def save(self, path: str):
        """인덱스와 데이터 저장"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # FAISS 인덱스 저장
        faiss.write_index(self.index, str(path / "index.faiss"))
        
        # 문서와 메타데이터 저장
        with open(path / "documents.pkl", "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "metadata": self.metadata
            }, f)
            
        # 설정 저장
        with open(path / "config.json", "w") as f:
            json.dump({
                "dimension": self.dimension,
                "index_type": self.index_type,
                "metric": self.metric,
                "total": self.index.ntotal
            }, f, indent=2)
            
        print(f"Index saved to {path}")
        
    def load(self, path: str):
        """저장된 인덱스와 데이터 로드"""
        path = Path(path)
        
        # FAISS 인덱스 로드
        self.index = faiss.read_index(str(path / "index.faiss"))
        
        # 문서와 메타데이터 로드
        with open(path / "documents.pkl", "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.metadata = data["metadata"]
            
        # 설정 로드
        with open(path / "config.json", "r") as f:
            config = json.load(f)
            self.dimension = config["dimension"]
            self.index_type = config["index_type"]
            self.metric = config["metric"]
            
        print(f"Index loaded from {path} ({self.index.ntotal} documents)")
        
    def clear(self):
        """인덱스 초기화"""
        self.index = self._create_index()
        self.documents = []
        self.metadata = []