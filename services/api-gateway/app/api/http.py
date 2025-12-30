from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from app.application import ingest_document, run_query
from app.core.config import Settings, get_settings
from app.infrastructure.db import init_db

api = FastAPI(title="Private RAG Platform PoC", version="0.1.0")


class IngestRequest(BaseModel):
    path: str = Field(..., description="Path to local file (mounted into container under /app/data).")
    chunk_size: Optional[int] = Field(None, description="Chunk size override.")
    chunk_overlap: Optional[int] = Field(None, description="Chunk overlap override.")


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = Field(None, description="How many chunks to retrieve.")
    mode: Optional[str] = Field("default", description="default|evaluate")


@api.on_event("startup")
def _startup() -> None:
    settings = get_settings()
    init_db(settings)
    logger.info("API startup complete")


@api.get("/health")
def health() -> dict:
    return {"status": "ok"}


@api.post("/ingest")
def ingest(req: IngestRequest) -> dict:
    settings = get_settings()
    if req.chunk_size:
        settings.chunk_size = req.chunk_size
    if req.chunk_overlap:
        settings.chunk_overlap = req.chunk_overlap
    path = Path(req.path)
    try:
        count = ingest_document(path, settings)
        return {"ingested": count, "collection": settings.rag_collection}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - debug surface
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@api.post("/query")
def query(req: QueryRequest) -> dict:
    settings: Settings = get_settings()
    top_k = req.top_k or settings.default_top_k
    try:
        result = run_query(req.query, settings, top_k=top_k, mode=req.mode or "default")
        return result.as_dict()
    except Exception as exc:  # pragma: no cover
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
