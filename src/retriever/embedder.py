"""
EmbeddingGemma를 사용한 텍스트 임베딩 모듈
"""
import torch
from transformers import AutoTokenizer, AutoModel
from typing import List, Union, Optional
import numpy as np
from tqdm import tqdm


class EmbeddingGemma:
    """EmbeddingGemma 모델을 사용한 텍스트 임베딩 생성기"""
    
    def __init__(
        self,
        model_name: str = "google/embeddinggemma-300m",
        device: Optional[str] = None,
        batch_size: int = 32,
        max_length: int = 512
    ):
        """
        Args:
            model_name: HuggingFace 모델 이름
            device: 연산 디바이스 (None이면 자동 선택)
            batch_size: 배치 크기
            max_length: 최대 토큰 길이
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.batch_size = batch_size
        self.max_length = max_length
        
        print(f"Loading {model_name} on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        
    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False
    ) -> np.ndarray:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            texts: 입력 텍스트 (문자열 또는 리스트)
            show_progress: 진행 상황 표시 여부
            
        Returns:
            임베딩 벡터 (numpy array)
        """
        if isinstance(texts, str):
            texts = [texts]
            
        embeddings = []
        
        # 배치 처리
        for i in tqdm(range(0, len(texts), self.batch_size), 
                     disable=not show_progress,
                     desc="Encoding"):
            batch_texts = texts[i:i+self.batch_size]
            
            # 토크나이징
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors='pt'
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 임베딩 생성
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Mean pooling
                batch_embeddings = outputs.last_hidden_state.mean(dim=1)
                embeddings.append(batch_embeddings.cpu().numpy())
                
        embeddings = np.vstack(embeddings)
        
        # 정규화
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        return embeddings if len(texts) > 1 else embeddings[0]
    
    def encode_queries(self, queries: Union[str, List[str]]) -> np.ndarray:
        """쿼리 텍스트 인코딩 (검색용)"""
        if isinstance(queries, str):
            queries = f"Query: {queries}"
        else:
            queries = [f"Query: {q}" for q in queries]
        return self.encode(queries)
    
    def encode_documents(self, documents: Union[str, List[str]]) -> np.ndarray:
        """문서 텍스트 인코딩 (색인용)"""
        if isinstance(documents, str):
            documents = f"Document: {documents}"
        else:
            documents = [f"Document: {doc}" for doc in documents]
        return self.encode(documents)