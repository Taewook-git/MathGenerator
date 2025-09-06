"""
설정 관리 모듈
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Any, Dict, Optional

load_dotenv()


class Config:
    """설정 관리 클래스"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Args:
            env_file: 환경 변수 파일 경로
        """
        if env_file:
            load_dotenv(env_file)
            
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """환경 변수에서 설정 로드"""
        return {
            # API 키
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "HUGGINGFACE_TOKEN": os.getenv("HUGGINGFACE_TOKEN"),
            
            # 모델 설정
            "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
            "GEMMA_MODEL": os.getenv("GEMMA_MODEL", "google/gemma-2-9b-it"),
            "EMBEDDING_MODEL": os.getenv("EMBEDDING_MODEL", "google/embedding-gemma-2b"),
            
            # 검색 설정
            "FAISS_INDEX_TYPE": os.getenv("FAISS_INDEX_TYPE", "HNSW"),
            "FAISS_METRIC": os.getenv("FAISS_METRIC", "cosine"),
            "EMBEDDING_DIMENSION": int(os.getenv("EMBEDDING_DIMENSION", "768")),
            
            # 경로 설정
            "DATA_PATH": Path(os.getenv("DATA_PATH", "./data")),
            "INDEX_PATH": Path(os.getenv("INDEX_PATH", "./data/index")),
            "OUTPUT_PATH": Path(os.getenv("OUTPUT_PATH", "./output")),
            
            # 디바이스 설정
            "DEVICE": os.getenv("DEVICE", "auto"),
            
            # 생성 설정
            "DEFAULT_TEMPERATURE": float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
            "MAX_OUTPUT_TOKENS": int(os.getenv("MAX_OUTPUT_TOKENS", "2048")),
            
            # UI 설정
            "STREAMLIT_THEME": os.getenv("STREAMLIT_THEME", "light"),
            "ENABLE_LATEX": os.getenv("ENABLE_LATEX", "true").lower() == "true",
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 가져오기"""
        return self._config.get(key, default)
        
    def set(self, key: str, value: Any):
        """설정 값 설정"""
        self._config[key] = value
        
    def validate(self) -> Dict[str, bool]:
        """필수 설정 검증"""
        validation = {
            "GEMINI_API_KEY": bool(self.get("GEMINI_API_KEY")),
            "DATA_PATH_EXISTS": self.get("DATA_PATH").exists(),
        }
        
        # HuggingFace 토큰 (선택사항)
        if self.get("HUGGINGFACE_TOKEN"):
            validation["HUGGINGFACE_TOKEN"] = True
            
        return validation
        
    def create_directories(self):
        """필요한 디렉토리 생성"""
        paths = [
            self.get("DATA_PATH"),
            self.get("INDEX_PATH"),
            self.get("OUTPUT_PATH"),
            self.get("DATA_PATH") / "raw",
            self.get("DATA_PATH") / "processed",
        ]
        
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
            
    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 반환"""
        return self._config.copy()
        
    def __repr__(self) -> str:
        """설정 정보 문자열 표현"""
        safe_config = self._config.copy()
        
        # 민감한 정보 마스킹
        if safe_config.get("GEMINI_API_KEY"):
            safe_config["GEMINI_API_KEY"] = "***" + safe_config["GEMINI_API_KEY"][-4:]
        if safe_config.get("HUGGINGFACE_TOKEN"):
            safe_config["HUGGINGFACE_TOKEN"] = "***" + safe_config["HUGGINGFACE_TOKEN"][-4:]
            
        return f"Config({safe_config})"


# 전역 설정 인스턴스
config = Config()