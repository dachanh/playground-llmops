import os
from functools import lru_cache
from typing import Optional


class Settings:
    """Core configuration shared across layers."""

    def __init__(self) -> None:
        self.database_url: str = os.getenv("DATABASE_URL", "postgres://rag:rag@localhost:5432/rag")
        self.qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.rag_collection: str = os.getenv("RAG_COLLECTION", "private_docs")
        self.default_top_k: int = int(os.getenv("RAG_TOP_K", "4"))
        self.chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "500"))
        self.chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
        self.chatgpt_model: str = os.getenv("CHATGPT_MODEL", "gpt-4o-mini")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
